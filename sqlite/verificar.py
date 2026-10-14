"""Confere que dados.db reproduz os CSVs linha a linha, na mesma ordem.

Uso:
    py -3 sqlite/verificar.py

Tres conferencias, todas contra os CSVs de csvs_originais/:
  1. Valores. Cada tabela e lida de volta e comparada com o CSV. Colunas
     DATETIME comparam o INSTANTE: o valor do banco, lido como hora de
     America/Sao_Paulo, tem de ser o mesmo instante do valor do CSV com seu
     offset original. O resto compara como texto (NULL -> string vazia).
  2. Chaves. Cada tabela tem a chave primaria do contrato de dados; em
     kanban_eventos, evento_id e exatamente o numero do registro no CSV.
  3. Views multivaloradas. Juntando os valores de cada registro com ';', na
     ordem, cada view remonta o campo original do CSV, sem sobra nem falta.

Sai com codigo 1 se qualquer conferencia falhar.
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ORIGEM = Path(__file__).resolve().parent.parent / "csvs_originais"
BANCO = Path(__file__).resolve().parent / "dados.db"

FUSO = ZoneInfo("America/Sao_Paulo")

# Chave primaria esperada por tabela (modelagem/Contrato_de_dados.md).
CHAVES = {
    "cartoes": ["grupo", "cartao_numero"],
    "commits": ["grupo", "commit_id"],
    "grupos": ["grupo"],
    "kanban_eventos": ["evento_id"],
    "merge_requests": ["grupo", "mr_numero"],
    "pessoas": ["pessoa_id"],
    "quadro_colunas": ["grupo", "quadro", "coluna"],
    "sprints": ["grupo", "sprint"],
}
SUBSTITUTAS = {"kanban_eventos": "evento_id"}

MULTIVALORADOS = [
    ("cartoes", "rotulos", ["grupo", "cartao_numero"], "rotulo"),
    ("cartoes", "responsaveis_ids", ["grupo", "cartao_numero"], "pessoa_id"),
    ("merge_requests", "rotulos", ["grupo", "mr_numero"], "rotulo"),
    ("merge_requests", "revisores_ids", ["grupo", "mr_numero"], "pessoa_id"),
    ("merge_requests", "responsaveis_ids", ["grupo", "mr_numero"], "pessoa_id"),
]


def ler_csv(caminho: Path) -> tuple[list[str], list[list[str]]]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor)
        return cabecalho, [linha for linha in leitor]


def mesmo_valor(do_csv: str, do_banco, tipo: str) -> bool:
    if do_banco is None:
        return do_csv == ""
    if tipo == "DATETIME":
        local = datetime.fromisoformat(do_banco).replace(tzinfo=FUSO)
        return local == datetime.fromisoformat(do_csv)
    return do_csv == str(do_banco)


def conferir_valores(con: sqlite3.Connection) -> bool:
    tudo_ok = True
    for caminho in sorted(ORIGEM.glob("*.csv")):
        tabela = caminho.stem
        cabecalho, do_csv = ler_csv(caminho)
        tipos = {r[1]: r[2] for r in con.execute(f'PRAGMA table_info("{tabela}")')}
        colunas = ", ".join(f'"{c}"' for c in cabecalho)
        do_banco = con.execute(f'SELECT {colunas} FROM "{tabela}" ORDER BY rowid').fetchall()

        identico = len(do_csv) == len(do_banco) and all(
            mesmo_valor(v_csv, v_db, tipos[c])
            for l_csv, l_db in zip(do_csv, do_banco)
            for c, v_csv, v_db in zip(cabecalho, l_csv, l_db)
        )
        tudo_ok &= identico
        datas = [c for c in cabecalho if tipos[c] in ("DATE", "DATETIME")]
        print(f"  {tabela:<16} {len(do_csv):>6} linhas  identico: {identico}"
              + (f"   datas: {', '.join(datas)}" if datas else ""))
    return tudo_ok


def conferir_chaves(con: sqlite3.Connection) -> bool:
    tudo_ok = True
    for tabela, esperada in CHAVES.items():
        pk = [r[1] for r in sorted(con.execute(f'PRAGMA table_info("{tabela}")'), key=lambda r: r[5]) if r[5]]
        ok = pk == esperada
        if tabela in SUBSTITUTAS:
            # A substituta tem de ser exatamente o numero do registro no CSV.
            col = SUBSTITUTAS[tabela]
            n = con.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
            fora = con.execute(
                f'SELECT COUNT(*) FROM "{tabela}" WHERE "{col}" <> rowid OR "{col}" NOT BETWEEN 1 AND ?', (n,)
            ).fetchone()[0]
            ok &= fora == 0
        tudo_ok &= ok
        print(f"  {tabela:<16} {', '.join(pk):<30} ok: {ok}")
    return tudo_ok


def conferir_views(con: sqlite3.Connection) -> bool:
    tudo_ok = True
    for tabela, campo, chave, valor in MULTIVALORADOS:
        cabecalho, linhas = ler_csv(ORIGEM / f"{tabela}.csv")
        idx = [cabecalho.index(c) for c in chave]
        i_campo = cabecalho.index(campo)
        esperado = {
            tuple(linha[i] for i in idx): linha[i_campo]
            for linha in linhas if linha[i_campo] != ""
        }

        view = f"v_{tabela}_{campo}"
        partes = defaultdict(list)
        cols = ", ".join(chave)
        for *ch, ordem, v in con.execute(f'SELECT {cols}, ordem, {valor} FROM "{view}"'):
            partes[tuple(str(x) for x in ch)].append((ordem, v))
        remontado = {k: ";".join(v for _, v in sorted(p)) for k, p in partes.items()}

        ok = remontado == esperado
        tudo_ok &= ok
        n = sum(len(p) for p in partes.values())
        print(f"  {view:<34} {len(esperado):>5} registros -> {n:>5} linhas  remonta: {ok}")
    return tudo_ok


def main() -> int:
    if not BANCO.exists():
        print(f"{BANCO} nao existe; rode csv_para_sqlite.py antes.", file=sys.stderr)
        return 1

    con = sqlite3.connect(BANCO)
    print("Valores")
    ok_valores = conferir_valores(con)
    print("\nChaves primarias")
    ok_chave = conferir_chaves(con)
    print("\nViews multivaloradas")
    ok_views = conferir_views(con)

    tudo_ok = ok_valores and ok_chave and ok_views
    print("\nBANCO CONFERE COM OS CSVs" if tudo_ok else "\nDIVERGENCIA ENCONTRADA")
    return 0 if tudo_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
