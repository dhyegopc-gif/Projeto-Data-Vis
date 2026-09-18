"""Confere que dados.db reproduz os CSVs linha a linha, na mesma ordem.

Uso:
    py -3 sqlite/verificar.py

Le cada CSV e a tabela correspondente, converte os valores do banco de volta
para texto (NULL -> string vazia) e compara as listas de tuplas. Sai com
codigo 1 se qualquer tabela divergir.
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BANCO = Path(__file__).resolve().parent / "dados.db"


def main() -> int:
    if not BANCO.exists():
        print(f"{BANCO} nao existe; rode csv_para_sqlite.py antes.", file=sys.stderr)
        return 1

    con = sqlite3.connect(BANCO)
    tudo_ok = True
    for caminho in sorted(RAIZ.glob("*.csv")):
        with caminho.open("r", encoding="utf-8-sig", newline="") as f:
            leitor = csv.reader(f)
            cabecalho = next(leitor)
            do_csv = [tuple(linha) for linha in leitor]

        colunas = ", ".join(f'"{c}"' for c in cabecalho)
        do_banco = [
            tuple("" if v is None else str(v) for v in linha)
            for linha in con.execute(f'SELECT {colunas} FROM "{caminho.stem}"')
        ]

        identico = do_csv == do_banco
        tudo_ok &= identico
        print(f"  {caminho.stem:<16} {len(do_csv):>6} linhas  identico: {identico}")

    print("\nTODAS AS TABELAS IDENTICAS AOS CSVs" if tudo_ok else "\nDIVERGENCIA ENCONTRADA")
    return 0 if tudo_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
