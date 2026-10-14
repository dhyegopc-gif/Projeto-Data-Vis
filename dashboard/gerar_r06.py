r"""Gera o dashboard do R06 (divisão dos tipos de tarefa no grupo).

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_r06.py

Fonte dos números: sqlite/r06_divisao_do_eixo.sql (como os cartões de cada eixo
se dividem entre os 7 integrantes, a leitura principal), sqlite/r06_eixo_por_integrante.sql
(parte de cada eixo por integrante, grupo e sprint) e sqlite/r06_cartoes_por_eixo.sql
(um cartão por linha, para a lista). Antes de gravar, refaz em Python as duas
contas a partir dos rótulos crus de cada cartão e para se divergir.
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import conectar, consultar, conferir, gravar, ler_sql, registro_mais_recente  # noqa: E402

# Mesma tabela do SQL, na mesma ordem (a ordem é a dos eixos no radar)
EIXOS = [
    {"id": "Código", "rotulos": ["CODE", "BUG", "Fix", "TEST", "DEPLOY", "CODE_REVIEW"]},
    {"id": "Design", "rotulos": ["DESIGN"]},
    {"id": "Documentação", "rotulos": ["DOCUMENTATION", "REQUIREMENTS", "user-story"]},
    {"id": "Negócio", "rotulos": ["NEGÓCIOS", "Presentation"]},
]
EIXO_DO_ROTULO = {r.upper(): e["id"] for e in EIXOS for r in e["rotulos"]}


def main() -> None:
    con = conectar()
    partes = consultar(con, ler_sql("r06_eixo_por_integrante.sql"))
    divisao = consultar(con, ler_sql("r06_divisao_do_eixo.sql"))
    cartoes = consultar(con, ler_sql("r06_cartoes_por_eixo.sql"))

    # --- Conferência: eixo de cada cartão refeito a partir dos rótulos crus ---
    nossos = defaultdict(lambda: defaultdict(float))   # (grupo, sprint, pessoa) -> eixo -> peso
    totais = defaultdict(lambda: [0, 0])               # (grupo, sprint, pessoa) -> [com eixo, sem eixo]
    for c in cartoes:
        eixos = sorted({EIXO_DO_ROTULO[r.upper()] for r in (c["rotulos"] or "").split(";") if r.upper() in EIXO_DO_ROTULO},
                       key=[e["id"] for e in EIXOS].index)
        conferir(";".join(eixos) == (c["eixos"] or ""), f"eixos do cartão {c['grupo']} #{c['cartao_numero']}")
        if not c["e_integrante"]:
            continue
        recortes = ["(todas)"] + ([c["sprint"]] if c["sprint"] != "(sem sprint)" else [])
        for s in recortes:
            for quem in (c["responsavel"], "(grupo)"):
                k = (c["grupo"], s, quem)
                totais[k][0 if eixos else 1] += 1
                for e in eixos:
                    nossos[k][e] += 1 / len(eixos)
    for p in partes:
        k = (p["grupo"], p["sprint"], p["pessoa_id"])
        conferir(abs(nossos[k][p["eixo"]] - p["cartoes"]) < 0.0001, f"{k} {p['eixo']}: {nossos[k][p['eixo']]} x {p['cartoes']}")
        conferir(totais[k] == [p["cartoes_total"], p["sem_eixo"]], f"{k}: totais {totais[k]} x {p['cartoes_total']}, {p['sem_eixo']}")
    conferir({k for k, (a, b) in totais.items() if a or b} <= {(p["grupo"], p["sprint"], p["pessoa_id"]) for p in partes},
             "recorte com cartão que falta no SQL")
    integrantes = defaultdict(set)
    for p in partes:
        if p["e_integrante"]:
            integrantes[p["grupo"]].add(p["pessoa_id"])
    conferir(all(len(v) == 7 for v in integrantes.values()), "7 integrantes por grupo")

    # --- Conferência: divisão de cada eixo entre os integrantes, refeita dos pesos ---
    for d in divisao:
        pesos = sorted((nossos[(d["grupo"], d["sprint"], p)][d["eixo"]] for p in integrantes[d["grupo"]]), reverse=True)
        total = sum(pesos)
        conferir(abs(total - d["cartoes_eixo"]) < 0.0001, f"divisão {d['grupo']} {d['sprint']} {d['eixo']}: total")
        conferir(sum(v > 0 for v in pesos) == d["integrantes_no_eixo"], f"divisão {d['grupo']} {d['sprint']} {d['eixo']}: integrantes")
        conferir(abs(sum(pesos[:2]) - d["dois_maiores"]) < 0.0001, f"divisão {d['grupo']} {d['sprint']} {d['eixo']}: dois maiores")
        com_eixo = sum(nossos[(d["grupo"], d["sprint"], "(grupo)")].values())
        conferir(abs((100 * total / com_eixo if com_eixo else 0) - d["parte_do_grupo"]) < 0.051, f"divisão {d['grupo']} {d['sprint']} {d['eixo']}: parte")

    # --- Dados da tela ---------------------------------------------------------
    recortes = {}
    for p in partes:
        r = recortes.setdefault(f"{p['grupo']}|{p['sprint']}|{p['pessoa_id']}",
                                {"n": p["cartoes_total"], "sem": p["sem_eixo"], "v": [0.0] * len(EIXOS)})
        r["v"][p["ordem"] - 1] = round(p["cartoes"], 4)
    fora = defaultdict(lambda: {"sem_responsavel": 0, "nao_integrante": 0, "total": 0})
    for c in cartoes:
        f = fora[c["grupo"]]
        f["total"] += 1
        if c["responsavel"] == "(vazio)":
            f["sem_responsavel"] += 1
        elif not c["e_integrante"]:
            f["nao_integrante"] += 1
    dados = {
        "eixos": EIXOS,
        "integrantes": {g: sorted(v) for g, v in sorted(integrantes.items())},
        "sprints": sorted({p["sprint"] for p in partes if p["sprint"] != "(todas)"}),
        "recortes": recortes,
        "divisao": {f"{d['grupo']}|{d['sprint']}|{d['eixo']}": {
            "n": d["cartoes_eixo"], "pessoas": d["integrantes_no_eixo"], "dois": d["dois_maiores"],
            "pct2": d["pct_dois_maiores"], "parte": d["parte_do_grupo"]} for d in divisao},
        "cartoes": [[c["grupo"], c["cartao_numero"], c["titulo"] or "", c["sprint"], c["situacao"],
                     c["responsavel"], c["eixos"] or ""] for c in cartoes if c["e_integrante"]],
        "fora": fora,
        "registro_mais_recente": registro_mais_recente(con),
    }
    for g in sorted(integrantes):
        resumo = []
        for e in EIXOS:
            d = dados["divisao"][f"{g}|(todas)|{e['id']}"]
            resumo.append(f"{e['id']} {d['parte']}% do grupo, 2 integrantes com {d['pct2']}%")
        print(f"{g}: " + "; ".join(resumo))
    print(f"{len(partes)} linhas de parte por eixo e {len(divisao)} de divisão; conferem com os rótulos crus.")
    gravar("r06_modelo.html", dados, "r06_eixos_de_tarefa.html", "Eixos no grupo")


if __name__ == "__main__":
    main()
