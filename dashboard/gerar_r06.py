r"""Gera o dashboard do R06 (concentração por eixo de tarefa).

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_r06.py

Fonte dos números: sqlite/r06_eixo_por_integrante.sql (parte de cada eixo por
integrante, grupo e sprint) e sqlite/r06_cartoes_por_eixo.sql (um cartão por
linha, para a lista do integrante). Antes de gravar, refaz em Python a parte
de cada eixo a partir dos rótulos crus de cada cartão e para se divergir.
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
        "cartoes": [[c["grupo"], c["cartao_numero"], c["titulo"] or "", c["sprint"], c["situacao"],
                     c["responsavel"], c["eixos"] or ""] for c in cartoes if c["e_integrante"]],
        "fora": fora,
        "registro_mais_recente": registro_mais_recente(con),
    }
    for g in sorted(integrantes):
        grupo = recortes[f"{g}|(todas)|(grupo)"]
        tot = sum(grupo["v"])
        print(f"{g}: " + ", ".join(f"{e['id']} {100 * v / tot:.1f}%" for e, v in zip(EIXOS, grupo["v"])))
    print(f"{len(partes)} linhas de parte por eixo; confere com os rótulos crus.")
    gravar("r06_modelo.html", dados, "r06_eixos_de_tarefa.html", "Eixos de tarefa")


if __name__ == "__main__":
    main()
