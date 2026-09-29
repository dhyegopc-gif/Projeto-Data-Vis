r"""Gera o dashboard do R04 (tamanho planejado x tempo realizado).

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_r04.py

Fonte dos números: sqlite/r04_prazo_planejado_realizado.sql (um cartão por
linha), r04_commits_por_cartao.sql (vínculos commit -> cartão) e
r04_resumo_por_tamanho.sql (medianas por tamanho). Antes de gravar, reconta
em Python o vínculo "#N" e as medianas; se algo divergir, para.
"""
import re
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from comum import conectar, consultar, conferir, gravar, ler_sql, registro_mais_recente  # noqa: E402

PLANEJADO = {"PP": 0.25, "P": 0.5, "M": 1.0, "G": 3.0, "GG": 5.0}
# "#N" sem zero à esquerda e não seguido de letra ou dígito (mesma regra do SQL)
RE_CARTAO = re.compile(r"#(0|[1-9][0-9]*)(?![0-9A-Za-z])")


def main() -> None:
    con = conectar()
    cartoes = consultar(con, ler_sql("r04_prazo_planejado_realizado.sql"))
    vinculos = consultar(con, ler_sql("r04_commits_por_cartao.sql"))
    resumo = consultar(con, ler_sql("r04_resumo_por_tamanho.sql"))

    # --- Conferência 1: o vínculo "#N" recontado em Python -------------------
    autorais = consultar(con, """
        SELECT c.grupo, c.commit_id, c.titulo, c.mensagem
        FROM commits c JOIN grupos g ON g.grupo = c.grupo
        WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em""")
    existe = {(g, n) for g, n in con.execute("SELECT grupo, cartao_numero FROM cartoes")}
    nossos = set()
    for c in autorais:
        numeros = {int(x) for x in RE_CARTAO.findall(c["titulo"] or "")} or \
                  {int(x) for x in RE_CARTAO.findall(c["mensagem"] or "")}
        for n in numeros:
            nossos.add((c["grupo"], n, c["commit_id"]))
    do_sql = {(v["grupo"], v["numero_citado"], v["commit_id"]) for v in vinculos}
    conferir(nossos == do_sql, f"vínculos divergem: {len(nossos ^ do_sql)} diferenças")
    validos = [v for v in vinculos if not v["numero_sem_cartao"]]
    conferir(all((v["grupo"], v["cartao_numero"]) in existe for v in validos), "vínculo aponta cartão inexistente")

    # --- Conferência 2: commits por cartão e medianas por tamanho ------------
    por_cartao = Counter((v["grupo"], v["cartao_numero"]) for v in validos)
    for c in cartoes:
        conferir(c["commits_ligados"] == por_cartao.get((c["grupo"], c["cartao_numero"]), 0),
                 f"commits do cartão {c['grupo']} #{c['cartao_numero']}")
        conferir(PLANEJADO[c["tamanho"]] == c["dias_planejados"], "dias planejados")
    grupos_tam = defaultdict(list)
    for c in cartoes:
        grupos_tam[(c["grupo"], c["tamanho"])].append(c)
    for r in resumo:
        if r["tamanho"] == "(sem tamanho)":
            continue
        lista = grupos_tam[(r["grupo"], r["tamanho"])]
        conferir(len(lista) == r["no_grafico"], f"cartões no gráfico {r['grupo']} {r['tamanho']}")
        med = statistics.median(c["dias_realizados"] for c in lista)
        conferir(abs(round(med, 2) - r["mediana_dias_realizados"]) <= 0.011,
                 f"mediana {r['grupo']} {r['tamanho']}: {med} x {r['mediana_dias_realizados']}")

    # --- O que fica fora do gráfico, por grupo --------------------------------
    fora = {g: {"sem_tamanho": 0, "abertos": 0} for (g,) in con.execute("SELECT grupo FROM grupos")}
    for r in resumo:
        if r["tamanho"] == "(sem tamanho)":
            fora[r["grupo"]]["sem_tamanho"] = r["cartoes"]
        else:
            fora[r["grupo"]]["abertos"] += r["fora_do_grafico"]
    total_cartoes = dict(con.execute("SELECT grupo, COUNT(*) FROM cartoes GROUP BY grupo"))
    autorais_grupo = Counter(c["grupo"] for c in autorais)
    com_cartao = Counter()
    for g, cid in {(v["grupo"], v["commit_id"]) for v in validos}:
        com_cartao[g] += 1
    citacao_sem_cartao = Counter(v["grupo"] for v in vinculos if v["numero_sem_cartao"])
    lote = dict(con.execute("""
        SELECT grupo, SUM(n) FROM (
            SELECT grupo, SUBSTR(fechado_em, 1, 16) m, COUNT(*) n FROM cartoes
            WHERE fechado_em IS NOT NULL GROUP BY 1, 2 HAVING COUNT(*) >= 5)
        GROUP BY grupo"""))

    grupos = {}
    for g in sorted(fora):
        grupos[g] = {
            "cartoes": total_cartoes[g],
            "sem_tamanho": fora[g]["sem_tamanho"],
            "abertos_com_tamanho": fora[g]["abertos"],
            "commits_autorais": autorais_grupo[g],
            "commits_com_cartao": com_cartao[g],
            "fechados_em_lote": lote.get(g, 0),
            "citacoes_sem_cartao": citacao_sem_cartao[g],
        }

    commits = defaultdict(list)
    for v in validos:
        commits[f"{v['grupo']}:{v['cartao_numero']}"].append(
            [v["commit_id"], v["autor_id"], v["autorado_em"], v["titulo"] or "",
             v["linhas_adicionadas"], v["linhas_removidas"]])

    dados = {
        "planejado": PLANEJADO,
        "cartoes": [[c["grupo"], c["cartao_numero"], c["titulo"] or "", c["sprint"], c["responsaveis_ids"] or "",
                     c["tamanho"], c["dias_planejados"], c["criado_em"], c["fechado_em"], c["dias_realizados"],
                     c["commits_ligados"], c["linhas_alteradas"]] for c in cartoes],
        "commits": commits,
        "grupos": grupos,
        "registro_mais_recente": registro_mais_recente(con),
    }
    print(f"{len(cartoes)} cartões no gráfico, {len(validos)} vínculos commit -> cartão; confere com o SQL.")
    gravar("r04_modelo.html", dados, "r04_prazo_planejado_realizado.html", "Planejado × realizado")


if __name__ == "__main__":
    main()
