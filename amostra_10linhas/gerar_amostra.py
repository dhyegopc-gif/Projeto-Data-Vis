"""Gera uma amostra com as 10 primeiras linhas de cada CSV de csvs_originais/.

Uso:
    py -3 amostra_10linhas/gerar_amostra.py

Decisoes:
  - Os CSVs de csvs_originais/ sao abertos SOMENTE PARA LEITURA. As amostras sao escritas
    aqui dentro, com o mesmo nome do arquivo de origem.
  - "10 linhas" = cabecalho + 10 REGISTROS, nao 10 linhas fisicas. Campos como
    commits.mensagem e cartoes.descricao contem quebras de linha dentro de
    aspas: cartoes.csv tem 1.238 registros em 8.876 linhas fisicas. Cortar por
    linha fisica partiria um registro no meio e geraria um CSV invalido.
  - O recorte e feito sobre os BYTES originais, nao reserializado. O csv.reader
    so serve para descobrir onde cada registro termina; as linhas que ele
    consumiu sao copiadas como estao. Assim aspas, virgulas, acentos e as
    quebras CRLF saem identicos ao arquivo de origem.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ORIGEM = Path(__file__).resolve().parent.parent / "csvs_originais"
DESTINO = Path(__file__).resolve().parent
REGISTROS = 10


def recortar(caminho: Path, n: int) -> tuple[str, int]:
    """Devolve o prefixo textual com cabecalho + n registros, e quantos vieram."""
    capturadas: list[str] = []

    with caminho.open("r", encoding="utf-8", newline="") as f:

        def espelhar():
            # Guarda cada linha fisica que o csv.reader consumir.
            for linha in f:
                capturadas.append(linha)
                yield linha

        leitor = csv.reader(espelhar())
        next(leitor, None)  # cabecalho
        lidos = 0
        for _ in leitor:
            lidos += 1
            if lidos == n:
                break

    return "".join(capturadas), lidos


def main() -> int:
    arquivos = sorted(ORIGEM.glob("*.csv"))
    if not arquivos:
        print(f"Nenhum CSV encontrado em {ORIGEM}", file=sys.stderr)
        return 1

    for caminho in arquivos:
        texto, lidos = recortar(caminho, REGISTROS)
        saida = DESTINO / caminho.name
        saida.write_text(texto, encoding="utf-8", newline="")
        aviso = "" if lidos == REGISTROS else f"  (origem so tem {lidos})"
        print(f"  {caminho.name:<20} {lidos:>2} registros{aviso}")

    print(f"\nAmostras em {DESTINO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
