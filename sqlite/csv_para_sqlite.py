"""Carrega os 8 CSVs de telemetria do GitLab em um unico banco SQLite.

Uso:
    py -3 sqlite/csv_para_sqlite.py

Regras desta carga:
  - Os CSVs sao a fonte e sao abertos SOMENTE PARA LEITURA. Nada e reescrito
    ou movido; o banco e sempre reconstruido do zero em sqlite/dados.db.
  - Uma tabela por arquivo, mesmo nome do CSV, mesmas colunas, mesma ordem.
    Nenhuma linha e filtrada, deduplicada ou normalizada: este e o estagio
    bruto. A modelagem dimensional de modelagem/schema.sql e outra camada.
  - O tipo de cada coluna e inferido do conteudo (INTEGER / REAL / TEXT).
    Como o SQLite e de tipagem dinamica, o valor gravado continua identico
    ao do CSV; a declaracao so garante ordenacao e agregacao corretas.
    Datas ficam em TEXT no ISO 8601 original, que e o formato que as funcoes
    de data do SQLite entendem.
  - Campo vazio no CSV vira NULL. Nenhuma coluna do conjunto usa a string
    vazia como valor com significado proprio.
"""

from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = Path(__file__).resolve().parent / "dados.db"

# Chaves naturais por arquivo: viram indice para acelerar os joins entre as
# tabelas. Nao sao declaradas como UNIQUE porque kanban_eventos.csv tem
# repeticoes legitimas na origem.
INDICES = {
    "grupos": [["grupo"]],
    "pessoas": [["grupo"], ["pessoa_id"]],
    "sprints": [["grupo", "sprint"]],
    "quadro_colunas": [["grupo", "quadro"]],
    "cartoes": [["grupo", "cartao_numero"], ["autor_id"], ["sprint"]],
    "commits": [["grupo", "commit_id"], ["autor_id"]],
    "merge_requests": [["grupo", "mr_numero"], ["autor_id"]],
    "kanban_eventos": [["grupo", "cartao_numero"], ["pessoa_id"], ["coluna"]],
}

RE_INT = re.compile(r"^-?\d+$")
RE_REAL = re.compile(r"^-?\d+\.\d+$")


def ler_csv(caminho: Path) -> tuple[list[str], list[list[str]]]:
    """Le o CSV inteiro. utf-8-sig remove um eventual BOM do cabecalho."""
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor)
        linhas = [linha for linha in leitor]
    return cabecalho, linhas


def inferir_tipos(cabecalho: list[str], linhas: list[list[str]]) -> list[str]:
    tipos = []
    for i in range(len(cabecalho)):
        valores = [linha[i] for linha in linhas if linha[i] != ""]
        if valores and all(RE_INT.match(v) for v in valores):
            tipos.append("INTEGER")
        elif valores and all(RE_INT.match(v) or RE_REAL.match(v) for v in valores):
            tipos.append("REAL")
        else:
            tipos.append("TEXT")
    return tipos


def converter(valor: str, tipo: str):
    if valor == "":
        return None
    if tipo == "INTEGER":
        return int(valor)
    if tipo == "REAL":
        return float(valor)
    return valor


def carregar(con: sqlite3.Connection, caminho: Path) -> tuple[str, int, int]:
    tabela = caminho.stem
    cabecalho, linhas = ler_csv(caminho)
    tipos = inferir_tipos(cabecalho, linhas)

    colunas = ",\n    ".join(f'"{c}" {t}' for c, t in zip(cabecalho, tipos))
    con.execute(f'DROP TABLE IF EXISTS "{tabela}"')
    con.execute(f'CREATE TABLE "{tabela}" (\n    {colunas}\n)')

    marcadores = ", ".join("?" * len(cabecalho))
    dados = [
        tuple(converter(v, t) for v, t in zip(linha, tipos))
        for linha in linhas
    ]
    con.executemany(f'INSERT INTO "{tabela}" VALUES ({marcadores})', dados)

    for cols in INDICES.get(tabela, []):
        nome = "ix_{}_{}".format(tabela, "_".join(cols))
        alvo = ", ".join(f'"{c}"' for c in cols)
        con.execute(f'CREATE INDEX "{nome}" ON "{tabela}" ({alvo})')

    gravadas = con.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
    return tabela, len(linhas), gravadas


def main() -> int:
    arquivos = sorted(RAIZ.glob("*.csv"))
    if not arquivos:
        print(f"Nenhum CSV encontrado em {RAIZ}", file=sys.stderr)
        return 1

    if DESTINO.exists():
        DESTINO.unlink()

    divergencias = []
    with sqlite3.connect(DESTINO) as con:
        for caminho in arquivos:
            tabela, no_csv, no_banco = carregar(con, caminho)
            marca = "ok" if no_csv == no_banco else "DIVERGENTE"
            if no_csv != no_banco:
                divergencias.append(tabela)
            print(f"  {tabela:<16} {no_banco:>6} linhas  ({marca})")
        con.commit()
        con.execute("VACUUM")

    tamanho = DESTINO.stat().st_size / 1024 / 1024
    print(f"\nBanco: {DESTINO}  ({tamanho:.1f} MB)")
    if divergencias:
        print(f"ATENCAO: contagem divergente em {', '.join(divergencias)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
