r"""Gera o dashboard do R05 (concentração do trabalho registrado, índice de Gini).

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_r05.py

Fonte dos números: sqlite/r05_contribuicao_por_integrante.sql (valor de cada
integrante) e sqlite/r05_gini_concentracao.sql (o índice). Antes de gravar,
recalcula o Gini em Python a partir das contribuições e para se divergir.

Também calcula aqui o intervalo possível do índice quando há parcela sem dono
([externo], [bot], cartão sem responsável):
  - máximo: toda a parcela seria de quem já tem mais;
  - mínimo: a parcela seria distribuída a partir de quem tem menos, nivelando.
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import conectar, consultar, conferir, gravar, ler_sql, registro_mais_recente  # noqa: E402

MEDIDAS = [
    {"id": "dias_planejados_concluidos", "nome": "Dias planejados concluídos", "curto": "dias planejados",
     "unidade": "dias planejados", "casas": 2, "sprint": True,
     "explica": "Cartões fechados, somados por responsável e pesados pelo tamanho (PP ¼, P ½, M 1, G 3, GG 5 dias)."},
    {"id": "cartoes_concluidos", "nome": "Cartões concluídos", "curto": "cartões",
     "unidade": "cartões", "casas": 1, "sprint": True,
     "explica": "Cartões fechados por responsável, todos com o mesmo peso."},
    {"id": "commits_autorais", "nome": "Commits autorais", "curto": "commits",
     "unidade": "commits", "casas": 0, "sprint": False,
     "explica": "Commits sem merge e sem o histórico do template, por autor (mesma base do R01)."},
    {"id": "mrs_autorados", "nome": "Merge requests", "curto": "MRs",
     "unidade": "MRs", "casas": 0, "sprint": True,
     "explica": "Merge requests criados, somados por autor."},
]


def gini(valores: list[float]) -> float | None:
    x = sorted(valores)
    n, s = len(x), sum(x)
    if not s:
        return None
    return sum((2 * i - n - 1) * v for i, v in enumerate(x, 1)) / (n * s)


def nivelar(valores: list[float], extra: float) -> list[float]:
    """Distribui 'extra' a partir dos menores, subindo todos a um mesmo nível."""
    x = sorted(valores)
    for k in range(1, len(x) + 1):
        nivel = (sum(x[:k]) + extra) / k
        if k == len(x) or nivel <= x[k]:
            return [max(v, nivel) if i < k else v for i, v in enumerate(x)]
    return x


def main() -> None:
    con = conectar()
    contrib = consultar(con, ler_sql("r05_contribuicao_por_integrante.sql"))
    indice = consultar(con, ler_sql("r05_gini_concentracao.sql"))

    recortes = defaultdict(lambda: {"integrantes": {}, "nao_atribuido": 0.0})
    for r in contrib:
        k = (r["grupo"], r["sprint"], r["medida"])
        if r["e_integrante"]:
            recortes[k]["integrantes"][r["pessoa_id"]] = r["valor"]
        else:
            recortes[k]["nao_atribuido"] = r["valor"]

    # --- Conferência: Gini do SQL = Gini recalculado; 7 integrantes por grupo
    por_indice = {(r["grupo"], r["sprint"], r["medida"]): r for r in indice}
    for k, rc in recortes.items():
        g = gini(list(rc["integrantes"].values()))
        if g is None:
            conferir(k not in por_indice, f"{k}: SQL tem índice para total zero")
            continue
        conferir(k in por_indice, f"{k}: falta no SQL")
        conferir(abs(round(g, 3) - por_indice[k]["gini"]) < 0.0015, f"{k}: Gini {g:.4f} x {por_indice[k]['gini']}")
        conferir(len(rc["integrantes"]) == 7, f"{k}: {len(rc['integrantes'])} integrantes")

    linhas = []
    for (grupo, sprint, medida), rc in sorted(recortes.items()):
        vals = rc["integrantes"]
        g = gini(list(vals.values()))
        if g is None:
            continue
        u = rc["nao_atribuido"]
        x = sorted(vals.values())
        g_max = gini(x[:-1] + [x[-1] + u]) if u else g
        g_min = gini(nivelar(x, u)) if u else g
        linhas.append({
            "grupo": grupo, "sprint": sprint, "medida": medida,
            "gini": round(g, 4), "gini_min": round(g_min, 4), "gini_max": round(g_max, 4),
            "nao_atribuido": round(u, 4),
            # em ordem de identificador: a tela não ordena pessoas por volume
            "valores": sorted([p, round(v, 4)] for p, v in vals.items()),
        })

    sprints = sorted({r["sprint"] for r in linhas if r["sprint"] != "(todas)"})
    # cartões fechados sem tamanho: entram em "cartões concluídos", não em "dias planejados"
    sem_tamanho = dict(con.execute("""
        SELECT c.grupo, COUNT(*) FROM cartoes c
        WHERE c.fechado_em IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM v_cartoes_rotulos r
            WHERE r.grupo = c.grupo AND r.cartao_numero = c.cartao_numero
              AND UPPER(r.rotulo) IN ('PP', 'SIZE_PP', 'P', 'SIZE_P', 'M', 'SIZE_M', 'G', 'SIZE_G', 'GG', 'SIZE_GG'))
        GROUP BY c.grupo"""))
    fechados = dict(con.execute("SELECT grupo, COUNT(*) FROM cartoes WHERE fechado_em IS NOT NULL GROUP BY grupo"))
    # perfis do cadastro: integrantes, com registro mas fora do critério, sem registro nenhum
    cadastro = consultar(con, """
        WITH integrantes AS (
            SELECT DISTINCT k.grupo, k.pessoa_id FROM kanban_eventos k
            JOIN pessoas p ON p.pessoa_id = k.pessoa_id WHERE p.grupo = k.grupo),
        com_registro AS (
            SELECT autor_id AS pessoa_id FROM commits UNION SELECT autor_id FROM merge_requests
            UNION SELECT pessoa_id FROM kanban_eventos UNION SELECT pessoa_id FROM v_cartoes_responsaveis_ids
            UNION SELECT autor_id FROM cartoes UNION SELECT pessoa_id FROM v_merge_requests_revisores_ids)
        SELECT p.pessoa_id, p.grupo, p.papel,
               EXISTS (SELECT 1 FROM integrantes i WHERE i.pessoa_id = p.pessoa_id) AS integrante,
               EXISTS (SELECT 1 FROM com_registro r WHERE r.pessoa_id = p.pessoa_id) AS registro
        FROM pessoas p""")
    fora_com_registro = sorted(c["pessoa_id"] for c in cadastro if not c["integrante"] and c["registro"])
    sem_registro = [c for c in cadastro if not c["registro"]]
    dados = {
        "medidas": MEDIDAS,
        "sprints": sprints,
        "recortes": linhas,
        "fechados": fechados,
        "fechados_sem_tamanho": sem_tamanho,
        "cadastro": len(cadastro),
        "integrantes": sum(c["integrante"] for c in cadastro),
        "fora_com_registro": fora_com_registro,
        "sem_registro": len(sem_registro),
        "registro_mais_recente": registro_mais_recente(con),
    }
    todas = [r for r in linhas if r["sprint"] == "(todas)" and r["medida"] == MEDIDAS[0]["id"]]
    print("Gini (dias planejados concluídos, todas as sprints): "
          + ", ".join(f"{r['grupo']} {r['gini']:.3f} [{r['gini_min']:.3f}–{r['gini_max']:.3f}]" for r in todas)
          + "; confere com o SQL.")
    gravar("r05_modelo.html", dados, "r05_concentracao_gini.html", "Concentração do trabalho")


if __name__ == "__main__":
    main()
