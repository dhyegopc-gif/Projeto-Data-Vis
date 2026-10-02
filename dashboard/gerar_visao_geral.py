r"""Gera a visão geral (a primeira tela): a leitura principal de R01 a R06 em uma página.

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_visao_geral.py

Não cria medida nova. Roda as mesmas consultas de sqlite/ que as telas usam
(t04, r02, r03, r04, r05 e r06), com os mesmos padrões de cada tela, e resume
uma leitura por requisito e grupo, todas as sprints. Cada leitura é conferida
por um segundo caminho (outra consulta ou recontagem) antes de gravar.
"""
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import (PREMISSAS, conectar, consultar, conferir, gravar, ler_sql,  # noqa: E402
                   registro_mais_recente, trocar_uma_vez)
from gerar_r02 import PARAMETROS_PADRAO, PARAMETROS_TODOS  # noqa: E402

# Padrões de cada tela (as premissas estão em comum.py; aqui só o número)
SILENCIO_DIAS = 3        # R01
LIMITE_HORAS = 48        # R02
COBERTURA_MIN = 80       # R03
FOCO_PCT = 75            # R06


def premissa(tela: str, nome: str) -> str:
    return next(v for n, v, _ in PREMISSAS[tela] if n == nome)


def r01(con) -> dict:
    marco = con.execute("SELECT MAX(prazo_em) FROM sprints WHERE prazo_em IS NOT NULL").fetchone()[0]
    serie = defaultdict(list)
    for g, d, n in con.execute(ler_sql("t04_cadencia_commits_diaria.sql")):
        serie[g].append((d, n))
    autorais = dict(con.execute("""
        SELECT c.grupo, COUNT(*) FROM commits c JOIN grupos g ON g.grupo = c.grupo
        WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em GROUP BY c.grupo"""))
    out = {}
    for g, s in sorted(serie.items()):
        s.sort()
        conferir(sum(n for _, n in s) == autorais[g], f"R01 {g}: t04 x commits autorais")
        corridas, i = [], 0
        while i < len(s):
            if s[i][1] == 0:
                j = i
                while j + 1 < len(s) and s[j + 1][1] == 0:
                    j += 1
                corridas.append({"dias": j - i + 1, "de": s[i][0], "ate": s[j][0]})
                i = j + 1
            else:
                i += 1
        antes = [c for c in corridas if c["ate"] <= marco]
        depois = [c for c in corridas if c["de"] > marco]
        sil = [c for c in antes if c["dias"] >= SILENCIO_DIAS]
        ate = [n for d, n in s if d <= marco]
        out[g] = {
            "silencios": len(sil),
            "maior": max(antes, key=lambda c: (c["dias"], c["de"])) if antes else None,
            "maior_depois": max(depois, key=lambda c: c["dias"]) if depois else None,
            "commits": sum(ate), "dias": len(ate), "dias_com": sum(1 for n in ate if n),
            "valor": len(sil),
        }
    return {"marco": marco, "grupos": out, "inicio": min(s[0][0] for s in serie.values()),
            "fim": max(s[-1][0] for s in serie.values())}


def r02(con) -> dict:
    detalhe = consultar(con, trocar_uma_vez(ler_sql("r02_cartoes_da_etapa.sql"), PARAMETROS_PADRAO, PARAMETROS_TODOS))
    resumo = consultar(con, ler_sql("r02_acumulo_por_etapa.sql"))
    conferir(resumo[0]["limite_horas"] == LIMITE_HORAS, "R02: limite do SQL")
    out = {}
    for g in sorted({d["grupo"] for d in detalhe}):
        ds = [d for d in detalhe if d["grupo"] == g]
        cartoes = {d["cartao_numero"] for d in ds}
        acima = {d["cartao_numero"] for d in ds if d["horas_exatas"] > LIMITE_HORAS}
        etapas = defaultdict(lambda: [0, 0.0])
        for d in ds:
            etapas[d["etapa"]][0] += d["horas_exatas"] > LIMITE_HORAS
            etapas[d["etapa"]][1] += d["horas_exatas"]
        # segundo caminho: o resumo do SQL, somado nas sprints
        for e, (n, _) in etapas.items():
            conferir(n == sum(r["cartoes_acima_limite"] for r in resumo if r["grupo"] == g and r["etapa"] == e), f"R02 {g} {e}")
        maior = max(etapas, key=lambda e: (etapas[e][0], etapas[e][1]))   # mesma regra da tela
        out[g] = {"cartoes": len(cartoes), "acima": len(acima), "valor": round(100 * len(acima) / len(cartoes), 1),
                  "etapa": maior, "etapa_acima": etapas[maior][0]}
    return {"grupos": out}


def r03(con) -> dict:
    linhas = consultar(con, ler_sql("r03_cobertura_registro.sql"))
    out = defaultdict(lambda: {"baixos": [], "usados": 0})
    for r in linhas:
        if r["tela"] == "-":
            continue
        o = out[r["grupo"]]
        o["usados"] += 1
        conferir(abs(round(100 * r["preenchidos"] / r["registros"], 1) - r["pct_preenchido"]) < 0.051, f"R03 {r['campo']}")
        if r["pct_preenchido"] < COBERTURA_MIN:
            o["baixos"].append({"chave": f"{r['arquivo']}|{r['campo']}", "pct": r["pct_preenchido"],
                                "telas": [t.strip() for t in r["tela"].split(",")]})
    for o in out.values():
        o["valor"] = len(o["baixos"])
    return {"grupos": dict(sorted(out.items()))}


def r04(con) -> dict:
    cartoes = consultar(con, ler_sql("r04_prazo_planejado_realizado.sql"))
    resumo = consultar(con, ler_sql("r04_resumo_por_tamanho.sql"))
    out = {}
    for g in sorted({c["grupo"] for c in cartoes}):
        cs = [c for c in cartoes if c["grupo"] == g]
        acima = sum(c["dias_realizados"] > c["dias_planejados"] for c in cs)
        dobro = sum(c["dias_realizados"] > 2 * c["dias_planejados"] for c in cs)
        # segundo caminho: % por tamanho do resumo, ponderado pelos cartões
        pelo_resumo = sum(r["pct_acima_planejado"] * r["no_grafico"] / 100 for r in resumo
                          if r["grupo"] == g and r["tamanho"] != "(sem tamanho)")
        conferir(abs(pelo_resumo - acima) < 0.5, f"R04 {g}: {pelo_resumo} x {acima}")
        out[g] = {"cartoes": len(cs), "acima": acima, "dobro": dobro, "valor": round(100 * acima / len(cs), 1),
                  "mediana": round(statistics.median(c["dias_realizados"] / c["dias_planejados"] for c in cs), 2)}
    return {"grupos": out}


def r05(con) -> dict:
    indice = consultar(con, ler_sql("r05_gini_concentracao.sql"))
    contrib = consultar(con, ler_sql("r05_contribuicao_por_integrante.sql"))
    out = {}
    for r in indice:
        if r["sprint"] != "(todas)" or r["medida"] != "dias_planejados_concluidos":
            continue
        x = sorted(c["valor"] for c in contrib if c["grupo"] == r["grupo"] and c["sprint"] == "(todas)"
                   and c["medida"] == "dias_planejados_concluidos" and c["e_integrante"])
        n, s = len(x), sum(x)
        g = sum((2 * i - n - 1) * v for i, v in enumerate(x, 1)) / (n * s)
        conferir(n == 7 and abs(round(g, 3) - r["gini"]) < 0.0015, f"R05 {r['grupo']}")
        out[r["grupo"]] = {"valor": r["gini"]}
    return {"grupos": dict(sorted(out.items()))}


def r06(con) -> dict:
    partes = consultar(con, ler_sql("r06_eixo_por_integrante.sql"))
    cartoes = consultar(con, ler_sql("r06_cartoes_por_eixo.sql"))
    por = defaultdict(dict)
    for p in partes:
        if p["sprint"] == "(todas)" and p["cartoes_total"]:
            por[(p["grupo"], p["pessoa_id"])][p["eixo"]] = (p["pct"], p["cartoes_total"])
    out = {}
    for g in sorted({k[0] for k in por}):
        focados = []
        for (gg, pessoa), eixos in sorted(por.items()):
            if gg != g or pessoa == "(grupo)":
                continue
            e = max(eixos, key=lambda k: eixos[k][0])
            if eixos[e][0] >= FOCO_PCT:
                focados.append({"pessoa": pessoa, "eixo": e, "pct": eixos[e][0], "cartoes": eixos[e][1]})
        perfil = por[(g, "(grupo)")]
        principal = max(perfil, key=lambda k: perfil[k][0])
        # segundo caminho: total do grupo = cartões com eixo dos integrantes na lista de cartões
        conferir(perfil[principal][1] == sum(1 for c in cartoes if c["grupo"] == g and c["e_integrante"] and c["eixos"]),
                 f"R06 {g}: cartões com eixo")
        out[g] = {"valor": len(focados), "focados": focados, "eixo": principal, "eixo_pct": perfil[principal][0],
                  "perfil": {e: v[0] for e, v in perfil.items()}}
    return {"grupos": out}


def main() -> None:
    con = conectar()
    conferir(f"{SILENCIO_DIAS} dias" in premissa("R01", "Silêncio"), "R01: silêncio")
    conferir(f"{LIMITE_HORAS} h" in premissa("R02", "Acúmulo"), "R02: limite")
    conferir(f"{COBERTURA_MIN}%" in premissa("R03", "Cobertura mínima"), "R03: mínimo")
    conferir(f"{FOCO_PCT}%" in premissa("R06", "Foco num eixo só"), "R06: foco")
    leituras = {"R01": r01(con), "R02": r02(con), "R03": r03(con), "R04": r04(con), "R05": r05(con), "R06": r06(con)}
    contexto = dict(zip(("cartoes", "mrs", "commits_autorais", "integrantes"), con.execute("""
        SELECT (SELECT COUNT(*) FROM cartoes), (SELECT COUNT(*) FROM merge_requests),
               (SELECT COUNT(*) FROM commits c JOIN grupos g ON g.grupo = c.grupo
                 WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em),
               (SELECT COUNT(*) FROM (SELECT DISTINCT k.grupo, k.pessoa_id FROM kanban_eventos k
                 JOIN pessoas p ON p.pessoa_id = k.pessoa_id WHERE p.grupo = k.grupo))""").fetchone()))
    dados = {
        "leituras": leituras,
        "padroes": {"silencio": SILENCIO_DIAS, "limite": LIMITE_HORAS, "cobertura": COBERTURA_MIN, "foco": FOCO_PCT},
        "contexto": contexto,
        "premissas_telas": {t: [{"nome": n, "valor": v} for n, v, _ in ps] for t, ps in PREMISSAS.items()},
        "registro_mais_recente": registro_mais_recente(con),
    }
    for req, l in leituras.items():
        print(req, ", ".join(f"{g} {v['valor']}" for g, v in l["grupos"].items()))
    gravar("visao_geral_modelo.html", dados, "visao_geral.html", "Visão geral")


if __name__ == "__main__":
    main()
