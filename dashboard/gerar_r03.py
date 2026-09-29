r"""Gera o dashboard do R03 (cobertura do próprio registro).

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_r03.py

Fonte dos números: sqlite/r03_cobertura_registro.sql (um campo x grupo por
linha). Antes de gravar, reconta quatro campos direto das tabelas (autoria dos
commits, tamanho do cartão, responsável identificado, revisor de MR) e para se divergir.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import conectar, consultar, conferir, gravar, ler_sql, registro_mais_recente  # noqa: E402

TAMANHOS = ("PP", "SIZE_PP", "P", "SIZE_P", "M", "SIZE_M", "G", "SIZE_G", "GG", "SIZE_GG")


def main() -> None:
    con = conectar()
    linhas = consultar(con, ler_sql("r03_cobertura_registro.sql"))
    por = {(r["grupo"], r["campo"]): r for r in linhas}

    # --- Conferência: três campos recontados direto das tabelas ---------------
    for g, total, resolvidos in con.execute("""
            SELECT grupo, COUNT(*), SUM(autor_id NOT IN ('[externo]', '[bot]')) FROM commits GROUP BY grupo"""):
        r = por[(g, "autor_id resolvido (arquivo inteiro)")]
        conferir((r["registros"], r["preenchidos"]) == (total, resolvidos), f"autoria {g}")
    tamanho = {}
    for g, n, rotulos in con.execute("SELECT grupo, cartao_numero, rotulos FROM cartoes"):
        tem = any(x.upper() in TAMANHOS for x in (rotulos or "").split(";"))
        t = tamanho.setdefault(g, [0, 0])
        t[0] += 1
        t[1] += tem
    for g, (total, com) in tamanho.items():
        r = por[(g, "tamanho (rótulo PP a GG)")]
        conferir((r["registros"], r["preenchidos"]) == (total, com), f"tamanho {g}")
    for g, total, com in con.execute("""
            SELECT grupo, COUNT(*), SUM(responsaveis_ids IS NOT NULL AND responsaveis_ids NOT IN ('[externo]', '[bot]'))
            FROM cartoes GROUP BY grupo"""):
        r = por[(g, "responsaveis_ids resolvido")]
        conferir((r["registros"], r["preenchidos"]) == (total, com), f"responsável {g}")
    for g, total, com in con.execute("SELECT grupo, COUNT(*), SUM(revisores_ids IS NOT NULL) FROM merge_requests GROUP BY grupo"):
        r = por[(g, "revisores_ids")]
        conferir((r["registros"], r["preenchidos"]) == (total, com), f"revisor {g}")

    dados = {
        "linhas": [[r["grupo"], r["arquivo"], r["campo"], r["registros"], r["preenchidos"], r["pct_preenchido"],
                    r["o_que_inviabiliza"], r["tela"]] for r in linhas],
        "registro_mais_recente": registro_mais_recente(con),
    }
    print(f"{len(linhas)} campo x grupo; confere com as tabelas.")
    gravar("r03_modelo.html", dados, "r03_cobertura_registro.html", "Cobertura do registro")


if __name__ == "__main__":
    main()
