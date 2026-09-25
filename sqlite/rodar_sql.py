r"""Roda arquivos .sql contra dados.db e grava cada resultado em CSV ao lado.

Pelo botao Run (sem argumento): roda todos os .sql desta pasta.
Pelo terminal, um arquivo so:

    py -3 C:\py\Projeto-Data-Vis\sqlite\rodar_sql.py Detalhamento_dos_commits.sql

Cada CSV sai com o nome do .sql (UTF-8 com BOM e ';', abre direto no Excel)
e as primeiras linhas aparecem no terminal.
"""
import csv
import sqlite3
import sys
from pathlib import Path

PASTA = Path(__file__).parent
BANCO = PASTA / "dados.db"


def rodar(arquivo: Path) -> None:
    consulta = arquivo.read_text(encoding="utf-8")
    if not consulta.strip():
        print(f"{arquivo.name} esta vazio no disco -- salve o arquivo (Ctrl+S) e rode de novo.\n")
        return

    with sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True) as con:
        cur = con.execute(consulta)
        colunas = [d[0] for d in cur.description]
        linhas = cur.fetchall()

    saida = arquivo.with_suffix(".csv")
    with saida.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(colunas)
        w.writerows(linhas)

    print(f"== {arquivo.name}")
    print(" | ".join(colunas))
    for linha in linhas[:15]:
        print(" | ".join("" if v is None else str(v) for v in linha))
    if len(linhas) > 15:
        print(f"... ({len(linhas) - 15} linhas a mais)")
    print(f"{len(linhas)} linhas -> {saida}\n")


if len(sys.argv) > 1:
    arquivo = Path(sys.argv[1])
    if not arquivo.exists():
        # aceita so o nome: procura na pasta do script, de onde quer que se rode
        arquivo = PASTA / arquivo.name
    rodar(arquivo)
else:
    for arquivo in sorted(PASTA.glob("*.sql")):
        rodar(arquivo)
