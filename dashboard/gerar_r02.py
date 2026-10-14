r"""Gera o dashboard do R02 (acúmulo de cartões por etapa do quadro).

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_r02.py

Fonte dos números: sqlite/r02_cartoes_da_etapa.sql rodado com os parâmetros
abertos ('*' = todos os grupos, sprints e etapas), um cartão x etapa por linha.
Antes de gravar, soma esses cartões por grupo, sprint e etapa e confere contra
sqlite/r02_acumulo_por_etapa.sql, inclusive a etapa de maior acúmulo com o
limite de 48 h. Se divergir, para.
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import conectar, consultar, conferir, gravar, ler_sql, registro_mais_recente, trocar_uma_vez  # noqa: E402

PARAMETROS_PADRAO = "'G01' AS grupo, 'Sprint 02' AS sprint, 'Backlog' AS etapa"
PARAMETROS_TODOS = "'*' AS grupo, '*' AS sprint, '*' AS etapa"


def main() -> None:
    con = conectar()
    resumo = consultar(con, ler_sql("r02_acumulo_por_etapa.sql"))
    detalhe = consultar(con, trocar_uma_vez(ler_sql("r02_cartoes_da_etapa.sql"), PARAMETROS_PADRAO, PARAMETROS_TODOS))
    limite = resumo[0]["limite_horas"]

    # --- Conferência: detalhe somado = resumo ---------------------------------
    soma = defaultdict(lambda: {"cartoes": 0, "passagens": 0, "horas": 0.0, "acima": 0, "sem_saida": 0, "abertos": 0})
    for d in detalhe:
        s = soma[(d["grupo"], d["sprint"], d["etapa"])]
        s["cartoes"] += 1
        s["passagens"] += d["passagens"]
        s["horas"] += d["horas_exatas"]
        s["acima"] += d["acima_limite"]
        # a tela compara as horas exatas com o limite; tem de dar a mesma marca do SQL
        conferir(int(d["horas_exatas"] > limite) == d["acima_limite"], f"acima do limite: cartão {d['cartao_numero']}")
        s["sem_saida"] += d["intervalos_sem_saida"]
        s["abertos"] += d["intervalos_abertos_no_corte"]
    conferir(len(soma) == len(resumo), f"{len(soma)} recortes no detalhe x {len(resumo)} no resumo")
    for r in resumo:
        s = soma[(r["grupo"], r["sprint"], r["etapa"])]
        k = f"{r['grupo']} {r['sprint']} {r['etapa']}"
        conferir(s["cartoes"] == r["cartoes"], f"{k}: cartões")
        conferir(s["passagens"] == r["passagens"], f"{k}: passagens")
        conferir(abs(s["horas"] - r["horas_total"]) <= 0.051, f"{k}: horas {s['horas']} x {r['horas_total']}")
        conferir(s["acima"] == r["cartoes_acima_limite"], f"{k}: acima do limite")
        conferir(s["sem_saida"] == r["intervalos_sem_saida"], f"{k}: sem saída")
        conferir(s["abertos"] == r["intervalos_abertos_no_corte"], f"{k}: abertos no corte")
    # etapa de maior acúmulo: mais cartões acima do limite, desempate por horas
    por_sprint = defaultdict(list)
    for r in resumo:
        por_sprint[(r["grupo"], r["sprint"])].append(r)
    for rs in por_sprint.values():
        topo = max((r["cartoes_acima_limite"], r["horas_total"]) for r in rs)
        for r in rs:
            conferir(r["e_maior_acumulo"] == int((r["cartoes_acima_limite"], r["horas_total"]) == topo),
                     f"maior acúmulo {r['grupo']} {r['sprint']} {r['etapa']}")

    etapas = [e for (e,) in con.execute("SELECT DISTINCT coluna FROM quadro_colunas ORDER BY posicao")]
    nao_etapas = con.execute("""
        SELECT COUNT(*), COUNT(DISTINCT k.coluna) FROM kanban_eventos k
        LEFT JOIN quadro_colunas q ON q.grupo = k.grupo AND q.coluna = k.coluna
        WHERE q.coluna IS NULL AND k.coluna IS NOT NULL""").fetchone()
    coluna_vazia = con.execute("SELECT COUNT(*) FROM kanban_eventos WHERE coluna IS NULL").fetchone()[0]
    dados = {
        "limite_padrao": limite,
        "etapas": etapas,
        "linhas": [[d["grupo"], d["sprint"], d["etapa"], d["cartao_numero"], d["titulo"] or "", d["situacao"],
                    d["responsaveis_ids"] or "", d["passagens"], d["primeira_entrada"], d["ultima_saida"],
                    round(d["horas_exatas"], 4), d["intervalos_sem_saida"], d["intervalos_abertos_no_corte"]] for d in detalhe],
        "eventos_rotulo": nao_etapas[0],
        "grafias_rotulo": nao_etapas[1],
        "eventos_coluna_vazia": coluna_vazia,
        "registro_mais_recente": registro_mais_recente(con),
    }
    print(f"{len(detalhe)} cartão x etapa em {len(resumo)} recortes; confere com o r02_acumulo_por_etapa.sql.")
    gravar("r02_modelo.html", dados, "r02_acumulo_por_etapa.html", "Acúmulo por etapa")


if __name__ == "__main__":
    main()
