"""Carrega os 8 CSVs de telemetria do GitLab em um unico banco SQLite.

Uso:
    py -3 sqlite/csv_para_sqlite.py

Regras desta carga:
  - Os CSVs ficam em csvs_originais/ e sao abertos SOMENTE PARA LEITURA.
    Nada e reescrito ou movido; o banco e sempre reconstruido do zero em
    sqlite/dados.db.
  - Uma tabela por arquivo, mesmo nome do CSV, mesmas colunas, mesma ordem.
    Nenhuma linha e filtrada ou deduplicada. A modelagem dimensional de
    modelagem/schema.sql e outra camada.
  - Cada tabela tem a chave primaria do contrato de dados. kanban_eventos,
    sem chave natural, ganha evento_id (numero do registro no CSV) como
    primeira coluna; e a unica coluna que nao vem do CSV.
  - O tipo de cada coluna e inferido do conteudo: INTEGER, REAL, DATE,
    DATETIME ou TEXT.
  - Timestamps (DATETIME) sao convertidos para o fuso unico do contrato de
    dados, America/Sao_Paulo, e gravados em ISO 8601 sem offset:
    'AAAA-MM-DDTHH:MM:SS.sss'. Os CSVs misturam UTC 'Z' e offsets -03:00 e
    +00:00; depois da conversao todas as colunas de tempo tem uma so grafia,
    comparam como string e date()/strftime() devolvem o dia e a hora locais.
    Datas puras (DATE) ja vem 'AAAA-MM-DD' e ficam como estao.
  - Os campos multivalorados (rotulos, *_ids) sao gravados intactos, com o
    ';' original. As views v_<tabela>_<campo> dividem cada um em uma linha
    por valor.
  - Campo vazio no CSV vira NULL. Nenhuma coluna do conjunto usa a string
    vazia como valor com significado proprio.
"""

from __future__ import annotations

import csv
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ORIGEM = Path(__file__).resolve().parent.parent / "csvs_originais"
DESTINO = Path(__file__).resolve().parent / "dados.db"

FUSO = ZoneInfo("America/Sao_Paulo")

# Chave primaria por tabela, a do contrato de dados (modelagem/
# Contrato_de_dados.md, "Chaves declaradas"). grupo entra na chave porque
# numero de cartao, numero de MR e commit_id reiniciam ou se repetem entre
# os grupos; pessoa_id ja traz o grupo no prefixo e basta sozinho.
CHAVES = {
    "grupos": ["grupo"],
    "pessoas": ["pessoa_id"],
    "sprints": ["grupo", "sprint"],
    "quadro_colunas": ["grupo", "quadro", "coluna"],
    "cartoes": ["grupo", "cartao_numero"],
    "commits": ["grupo", "commit_id"],
    "merge_requests": ["grupo", "mr_numero"],
}

# Tabela sem chave natural: ganha uma chave substituta, como primeira coluna,
# com o numero do registro no CSV (1 = primeiro registro apos o cabecalho).
# kanban_eventos tem 12 eventos triplicados, identicos nas 6 colunas; o numero
# do registro os distingue sem descartar nenhum.
SUBSTITUTAS = {
    "kanban_eventos": "evento_id",
}

# Colunas de join mais usadas que a chave primaria nao cobre: viram indice.
INDICES = {
    "pessoas": [["grupo"]],
    "cartoes": [["autor_id"], ["sprint"]],
    "commits": [["autor_id"], ["grupo", "autorado_em"]],
    "merge_requests": [["autor_id"]],
    "kanban_eventos": [["grupo", "cartao_numero"], ["pessoa_id"], ["coluna"], ["grupo", "ocorrido_em"]],
}

# Campos multivalorados: (tabela, campo, chave do registro, nome do valor).
# Apenas estes cinco sao listas; ';' em texto livre (descricao, mensagem)
# e pontuacao e nao e dividido.
MULTIVALORADOS = [
    ("cartoes", "rotulos", ["grupo", "cartao_numero"], "rotulo"),
    ("cartoes", "responsaveis_ids", ["grupo", "cartao_numero"], "pessoa_id"),
    ("merge_requests", "rotulos", ["grupo", "mr_numero"], "rotulo"),
    ("merge_requests", "revisores_ids", ["grupo", "mr_numero"], "pessoa_id"),
    ("merge_requests", "responsaveis_ids", ["grupo", "mr_numero"], "pessoa_id"),
]

RE_INT = re.compile(r"^-?\d+$")
RE_REAL = re.compile(r"^-?\d+\.\d+$")
RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
RE_TIMESTAMP_SEM_FUSO = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")


def ler_csv(caminho: Path) -> tuple[list[str], list[list[str]]]:
    """Le o CSV inteiro. utf-8-sig remove um eventual BOM do cabecalho."""
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor)
        linhas = [linha for linha in leitor]
    return cabecalho, linhas


def inferir_tipos(cabecalho: list[str], linhas: list[list[str]]) -> list[str]:
    tipos = []
    for i, nome in enumerate(cabecalho):
        valores = [linha[i] for linha in linhas if linha[i] != ""]
        if not valores:
            tipos.append("TEXT")
        elif all(RE_INT.match(v) for v in valores):
            tipos.append("INTEGER")
        elif all(RE_INT.match(v) or RE_REAL.match(v) for v in valores):
            tipos.append("REAL")
        elif all(RE_DATA.match(v) for v in valores):
            tipos.append("DATE")
        elif all(RE_TIMESTAMP.match(v) for v in valores):
            tipos.append("DATETIME")
        elif any(RE_TIMESTAMP_SEM_FUSO.match(v) for v in valores):
            # Sem offset nao da para saber o instante; melhor parar do que
            # gravar uma hora que pode estar 3h errada.
            raise ValueError(f"coluna {nome}: timestamp sem fuso ou em grafia desconhecida")
        else:
            tipos.append("TEXT")
    return tipos


def para_fuso_local(valor: str) -> str:
    """'2026-04-22T17:38:42.296Z' -> '2026-04-22T14:38:42.296' (America/Sao_Paulo)."""
    instante = datetime.fromisoformat(valor)
    return instante.astimezone(FUSO).replace(tzinfo=None).isoformat(timespec="milliseconds")


def converter(valor: str, tipo: str):
    if valor == "":
        return None
    if tipo == "INTEGER":
        return int(valor)
    if tipo == "REAL":
        return float(valor)
    if tipo == "DATETIME":
        return para_fuso_local(valor)
    return valor


def carregar(con: sqlite3.Connection, caminho: Path) -> tuple[str, int, int]:
    tabela = caminho.stem
    cabecalho, linhas = ler_csv(caminho)
    tipos = inferir_tipos(cabecalho, linhas)
    chave = CHAVES.get(tabela, [])
    substituta = SUBSTITUTAS.get(tabela)

    definicoes = [
        f'"{c}" {t}' + (" NOT NULL" if c in chave else "")
        for c, t in zip(cabecalho, tipos)
    ]
    if substituta:
        definicoes.insert(0, f'"{substituta}" INTEGER PRIMARY KEY')
    if chave:
        definicoes.append("PRIMARY KEY ({})".format(", ".join(f'"{c}"' for c in chave)))
    colunas = ",\n    ".join(definicoes)
    con.execute(f'DROP TABLE IF EXISTS "{tabela}"')
    con.execute(f'CREATE TABLE "{tabela}" (\n    {colunas}\n)')

    dados = [
        tuple(converter(v, t) for v, t in zip(linha, tipos))
        for linha in linhas
    ]
    if substituta:
        dados = [(n, *linha) for n, linha in enumerate(dados, start=1)]
    marcadores = ", ".join("?" * len(dados[0]))
    con.executemany(f'INSERT INTO "{tabela}" VALUES ({marcadores})', dados)

    for cols in INDICES.get(tabela, []):
        nome = "ix_{}_{}".format(tabela, "_".join(cols))
        alvo = ", ".join(f'"{c}"' for c in cols)
        con.execute(f'CREATE INDEX "{nome}" ON "{tabela}" ({alvo})')

    gravadas = con.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
    return tabela, len(linhas), gravadas


def criar_views_multivaloradas(con: sqlite3.Connection) -> list[str]:
    """Uma view por campo multivalorado: 1 linha por (registro, valor).

    qtd_valores e peso_alocacao (= 1/qtd_valores) permitem somar sobre a
    explosao sem contar o mesmo registro varias vezes, como as pontes de
    modelagem/schema.sql. Registro com o campo vazio nao aparece na view.
    """
    criadas = []
    for tabela, campo, chave, valor in MULTIVALORADOS:
        view = f"v_{tabela}_{campo}"
        ch = ", ".join(chave)
        con.execute(f'DROP VIEW IF EXISTS "{view}"')
        con.execute(f"""
CREATE VIEW "{view}" AS
WITH RECURSIVE partes({ch}, ordem, {valor}, resto) AS (
    SELECT {ch}, 1,
           substr({campo} || ';', 1, instr({campo} || ';', ';') - 1),
           substr({campo} || ';', instr({campo} || ';', ';') + 1)
    FROM   {tabela}
    WHERE  {campo} IS NOT NULL
    UNION ALL
    SELECT {ch}, ordem + 1,
           substr(resto, 1, instr(resto, ';') - 1),
           substr(resto, instr(resto, ';') + 1)
    FROM   partes
    WHERE  resto <> ''
),
contagem AS (
    SELECT {ch}, COUNT(*) AS qtd_valores FROM partes GROUP BY {ch}
)
SELECT {", ".join(f"p.{c}" for c in chave)}, p.ordem, p.{valor},
       c.qtd_valores, 1.0 / c.qtd_valores AS peso_alocacao
FROM   partes p
JOIN   contagem c USING ({ch})
""")
        criadas.append(view)
    return criadas


def main() -> int:
    arquivos = sorted(ORIGEM.glob("*.csv"))
    if not arquivos:
        print(f"Nenhum CSV encontrado em {ORIGEM}", file=sys.stderr)
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
        views = criar_views_multivaloradas(con)
        print(f"\n  views: {', '.join(views)}")
        con.commit()
    with sqlite3.connect(DESTINO) as con:
        con.execute("VACUUM")

    tamanho = DESTINO.stat().st_size / 1024 / 1024
    print(f"\nBanco: {DESTINO}  ({tamanho:.1f} MB)")
    if divergencias:
        print(f"ATENCAO: contagem divergente em {', '.join(divergencias)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
