r"""Gera o dashboard do R01 (ritmo de registro) a partir de sqlite/dados.db.

    py -3 C:\py\Projeto-Data-Vis\dashboard\gerar_r01.py

Grava dashboard/r01_ritmo_de_registro.html: um arquivo so, sem rede, com os
dados embutidos. Antes de gravar, confere que a contagem diaria embutida e a
mesma de sqlite/t04_cadencia_commits_diaria.sql -- se divergir, para.
"""
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "sqlite" / "dados.db"
T04 = RAIZ / "sqlite" / "t04_cadencia_commits_diaria.sql"
MODELO = Path(__file__).with_name("r01_modelo.html")
SAIDA = Path(__file__).with_name("r01_ritmo_de_registro.html")
SAIDA_PB = Path(__file__).with_name("r01_ritmo_de_registro_pb.html")

# Versao em preto, branco e cinza: a mesma pagina, so com a paleta trocada.
# Os tokens sao redeclarados depois dos originais, nos mesmos tres escopos,
# entao vencem pela ordem. Colunas em cinza medio; o dia aberto na lista se
# distingue pelo extremo (preto no claro, branco no escuro) e pela seta no eixo.
_PB_CLARO = """
  --page: #f5f5f5; --surface: #ffffff; --ink: #111111; --ink-2: #4a4a4a;
  --muted: #6b6b6b; --grid: #e2e2e2; --axis: #bdbdbd; --series: #737373;
  --series-strong: #111111; --hover: rgba(0, 0, 0, 0.06); --silence: #ebebeb;
  --zero: #9e9e9e; --border: rgba(0, 0, 0, 0.12); --chip: #ededed; --focus: #111111;"""
_PB_ESCURO = """
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a1a; --ink: #ffffff; --ink-2: #c4c4c4;
  --muted: #a3a3a3; --grid: #2c2c2c; --axis: #3d3d3d; --series: #8f8f8f;
  --series-strong: #f5f5f5; --hover: rgba(255, 255, 255, 0.08); --silence: #262626;
  --zero: #6b6b6b; --border: rgba(255, 255, 255, 0.12); --chip: #2c2c2c; --focus: #ffffff;"""
TEMA_PB = f"""
/* tema preto, branco e cinza */
:root {{{_PB_CLARO}
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{{_PB_ESCURO}
  }}
}}
:root[data-theme="dark"] {{{_PB_ESCURO}
}}
"""

# Nenhum arquivo do conjunto registra quando os dados foram extraidos. A nota
# de origem diz isso e mostra o que se sabe; se a data aparecer, preencha aqui
# no formato AAAA-MM-DD.
DATA_EXTRACAO = None
ENTRADA_NO_REPOSITORIO = "2026-09-18"  # primeiro commit de csvs_originais/ no git

SENTINELAS = ("[externo]", "[bot]")


def main() -> None:
    con = sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True)
    q = lambda sql, *p: con.execute(sql, p).fetchall()

    # Mesmo recorte do t04 e do Detalhamento: sem merges, sem historico do template
    commits = q("""
        SELECT c.grupo, c.commit_id, c.autor_id, c.autorado_em, COALESCE(c.titulo, ''),
               c.linhas_adicionadas, c.linhas_removidas
        FROM commits c JOIN grupos g ON g.grupo = c.grupo
        WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em
        ORDER BY c.grupo, c.autorado_em""")

    primeiro, ultimo = q("""
        SELECT MIN(DATE(c.autorado_em)), MAX(DATE(c.autorado_em))
        FROM commits c JOIN grupos g ON g.grupo = c.grupo
        WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em""")[0]

    grupos = {}
    for grupo, criado in q("SELECT grupo, criado_em FROM grupos ORDER BY grupo"):
        merges = dict(q("""
            SELECT DATE(c.autorado_em), COUNT(*) FROM commits c JOIN grupos g ON g.grupo = c.grupo
            WHERE c.grupo = ? AND c.e_merge = 1 AND c.commitado_em >= g.criado_em
            GROUP BY 1""", grupo))
        herdados, h_ini, h_fim = q("""
            SELECT COUNT(*), MIN(DATE(c.autorado_em)), MAX(DATE(c.autorado_em))
            FROM commits c JOIN grupos g ON g.grupo = c.grupo
            WHERE c.grupo = ? AND c.commitado_em < g.criado_em""", grupo)[0]
        sprints = [list(r) for r in q("""
            SELECT sprint, inicio_em, prazo_em FROM sprints
            WHERE grupo = ? AND inicio_em IS NOT NULL AND prazo_em IS NOT NULL
            ORDER BY sprint""", grupo)]
        grupos[grupo] = {
            "criado": criado[:10],
            "merges": merges,
            "herdados": herdados,
            "herdados_de": h_ini,
            "herdados_ate": h_fim,
            "sprints": sprints,
        }

    # Fim do calendario de sprints: so o G03 tem datas de sprint, entao o marco
    # vem dele e a tela diz de quem e.
    fim_sprint, sprint_fim, grupo_fim = q("""
        SELECT prazo_em, sprint, grupo FROM sprints
        WHERE prazo_em IS NOT NULL ORDER BY prazo_em DESC LIMIT 1""")[0]

    registro_mais_recente = q("""
        SELECT MAX(t) FROM (
            SELECT MAX(ultima_atividade_em) t FROM grupos
            UNION ALL SELECT MAX(ocorrido_em) FROM kanban_eventos
            UNION ALL SELECT MAX(atualizado_em) FROM cartoes
            UNION ALL SELECT MAX(atualizado_em) FROM merge_requests
            UNION ALL SELECT MAX(commitado_em) FROM commits)""")[0][0]

    # Conferencia contra o t04: mesmos dias, mesmas contagens
    t04 = {(g, d): n for g, d, n in con.execute(T04.read_text(encoding="utf-8"))}
    nossos = Counter((c[0], c[3][:10]) for c in commits)
    divergentes = [k for k, n in t04.items() if nossos.get(k, 0) != n]
    if divergentes or sum(t04.values()) != len(commits):
        sys.exit(f"Contagem diverge do t04 em {len(divergentes)} dia(s): {divergentes[:5]}")

    dados = {
        "inicio": primeiro,
        "fim": ultimo,
        "grupos": grupos,
        "commits": [list(c) for c in commits],
        "sentinelas": SENTINELAS,
        "fim_calendario": {"data": fim_sprint, "sprint": sprint_fim, "grupo": grupo_fim},
        "extracao": DATA_EXTRACAO,
        "entrada_repositorio": ENTRADA_NO_REPOSITORIO,
        "registro_mais_recente": registro_mais_recente[:10],
    }
    bloco = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = MODELO.read_text(encoding="utf-8").replace("__DADOS__", bloco)
    SAIDA.write_text(html, encoding="utf-8")
    pb = (html.replace("<title>Ritmo de registro</title>", "<title>Ritmo de registro P&amp;B</title>", 1)
              .replace("</style>", TEMA_PB + "</style>", 1))
    SAIDA_PB.write_text(pb, encoding="utf-8")
    por_grupo = Counter(c[0] for c in commits)
    print(f"{len(commits)} commits ({dict(por_grupo)}), {len(t04) // len(grupos)} dias "
          f"de {primeiro} a {ultimo}; confere com o t04.")
    print(f"-> {SAIDA}")
    print(f"-> {SAIDA_PB}")


if __name__ == "__main__":
    main()
