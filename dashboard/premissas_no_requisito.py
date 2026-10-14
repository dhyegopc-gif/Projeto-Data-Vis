r"""Escreve a linha "Premissas do grupo" de cada requisito em Requisitos.MD.

    py -3 C:\py\Projeto-Data-Vis\dashboard\premissas_no_requisito.py

A lista vem de PREMISSAS, em comum.py, a mesma que as telas mostram. A linha é
inserida (ou reescrita) no fim da tabela de cada seção R01 a R05. Rode depois
de mudar uma premissa; os geradores param se o requisito e a tela divergirem.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import PREMISSAS, REQUISITOS  # noqa: E402

ROTULO = "| **Premissas do grupo**"


def linha(tela: str) -> str:
    itens = "<br>".join(f"• **{n}**: {v}. {p[0].upper() + p[1:]}." for n, v, p in PREMISSAS[tela])
    return f"{ROTULO}   | Todas a confirmar com o professor; a tela mostra a mesma lista.<br>{itens} |"


def main() -> None:
    texto = REQUISITOS.read_text(encoding="utf-8")
    for tela in PREMISSAS:
        inicio = re.search(rf"^## {tela} — .*$", texto, re.M)
        if not inicio:
            sys.exit(f"Seção {tela} não encontrada")
        fim = re.search(r"^## ", texto[inicio.end():], re.M)
        a, b = inicio.end(), inicio.end() + (fim.start() if fim else len(texto) - inicio.end())
        secao = texto[a:b]
        linhas = [l for l in secao.split("\n") if not l.startswith(ROTULO)]
        # última linha de tabela da seção
        ult = max(i for i, l in enumerate(linhas) if l.startswith("|"))
        linhas.insert(ult + 1, linha(tela))
        texto = texto[:a] + "\n".join(linhas) + texto[b:]
    REQUISITOS.write_text(texto, encoding="utf-8")
    print("Premissas escritas em", REQUISITOS)


if __name__ == "__main__":
    main()
