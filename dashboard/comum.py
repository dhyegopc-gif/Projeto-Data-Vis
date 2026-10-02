"""Peças comuns dos geradores R02 a R06 e da visão geral.

Cada gerador:
  1. roda os .sql de sqlite/ (fonte da verdade dos números);
  2. reconta o essencial por conta própria, em Python, e para se divergir;
  3. chama gravar(), que injeta comum.css, comum.js e os dados no modelo e
     grava a versão colorida e a P&B (mesma página, só a paleta trocada).

O gerar_r01.py é anterior a este módulo e continua independente.
"""
import csv
import io
import json
import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = Path(__file__).resolve().parent
SQLITE = RAIZ / "sqlite"
BANCO = SQLITE / "dados.db"

# Nenhum arquivo do conjunto registra a data de extração (ver R01).
ENTRADA_NO_REPOSITORIO = "2026-09-18"  # primeiro commit de csvs_originais/ no git

# Telas do projeto: a visão geral primeiro, depois os requisitos em ordem numérica
# (a navegação do topo segue esta ordem). url = versão publicada (privada) quando
# houver (None até publicar); a navegação usa o arquivo local quando a página é aberta do disco.
TELAS = [
    {"id": "Início", "nome": "Visão geral", "arquivo": "visao_geral.html",
     "url": "https://claude.ai/artifact/Jh4vnFxrMXM2oP9gE2jjsD"},
    {"id": "R01", "nome": "Ritmo de registro", "arquivo": "r01_ritmo_de_registro.html",
     "url": "https://claude.ai/artifact/J8vMTWGFyRVzfqxYK9nNXo"},
    {"id": "R02", "nome": "Acúmulo por etapa", "arquivo": "r02_acumulo_por_etapa.html",
     "url": "https://claude.ai/artifact/HTDPZKzttfVncZUGBU4kvv"},
    {"id": "R03", "nome": "Cobertura do registro", "arquivo": "r03_cobertura_registro.html",
     "url": "https://claude.ai/artifact/6UznL9ZeRJR2973pazcdCG"},
    {"id": "R04", "nome": "Planejado × realizado", "arquivo": "r04_prazo_planejado_realizado.html",
     "url": "https://claude.ai/artifact/X6Z8ZAoEurjtGkGagFE8my"},
    {"id": "R05", "nome": "Concentração (Gini)", "arquivo": "r05_concentracao_gini.html",
     "url": "https://claude.ai/artifact/UFJ17FrDcetbwMGXCuqNRj"},
    {"id": "R06", "nome": "Eixos de tarefa", "arquivo": "r06_eixos_de_tarefa.html",
     "url": "https://claude.ai/artifact/4tvQRwKfVW5JZs6p2cYRqv"},
]

# Premissas de cada tela: escolhas do grupo, não definições da orientação.
# Fonte única: a tela mostra esta lista no bloco "Premissas desta tela" e o
# requisito traz a mesma lista na linha "Premissas do grupo". gravar() confere
# que cada "**nome**: valor" está em requisitos/Requisitos.MD e para se não estiver.
PREMISSAS = {
    "R01": [
        ("Silêncio", "3 dias seguidos sem commit autoral, ajustável de 2 a 7 na tela",
         "um dia a mais que um fim de semana"),
        ("Dia do commit", "a data de autoria, não a de commit",
         "é quando a pessoa fez a alteração; em 10 commits contados o dia muda"),
        ("Marco de fim de sprint", "26/06/2026 para os três grupos, fim da Sprint 05 do G03",
         "é a única sprint do conjunto com data; G01 e G02 não têm datas de sprint"),
    ],
    "R02": [
        ("Etapa", "valor de coluna que casa com o Scrum Board do grupo (Backlog, Doing, Waiting Review, Review)",
         "os outros valores da mesma coluna são rótulos, como CODE ou SIZE_M"),
        ("Acúmulo", "cartão que somou mais de 48 h na etapa, contando todas as passagens; 24 h e 72 h para comparar",
         "a cliente não definiu um limite"),
        ("Passagem sem saída", "termina no fechamento do cartão; se ele não foi fechado, no último registro do conjunto",
         "assim a passagem não some da conta"),
        ("Etapa de maior acúmulo", "a que tem mais cartões acima do limite; no empate, a de mais horas somadas",
         "conta primeiro quantos cartões ficaram parados, depois quanto tempo"),
    ],
    "R03": [
        ("Cobertura mínima", "80% de preenchimento para confiar na leitura; 70% e 90% para comparar",
         "corte nosso para separar sinal de registro incompleto"),
        ("Pessoa resolvida", "[externo] e [bot] contam como vazio em autoria e responsável",
         "não existem no cadastro de pessoas"),
    ],
    "R04": [
        ("Dias planejados por tamanho", "PP 0,25 · P 0,5 · M 1 · G 3 · GG 5",
         "tirado do exemplo do professor; a cliente não definiu"),
        ("Tempo realizado", "da criação ao fechamento do cartão, em dias corridos",
         "escolhido no lugar de entrada em Doing → fechamento; inclui a espera no Backlog"),
        ("Commit ligado ao cartão", "#N no título (ou na mensagem, se o título não cita número) é o cartão N do mesmo grupo",
         "sugestão do professor; 83,2% dos commits autorais citam um cartão"),
        ("Levou mais que o planejado", "tempo realizado acima dos dias planejados; o dobro, acima de 2 vezes",
         "não há prazo combinado, então a tela não fala em atraso"),
    ],
    "R05": [
        ("Integrante", "pessoa do cadastro do grupo com pelo menos um movimento no quadro do próprio grupo (7 por grupo)",
         "deixa de fora 59 perfis sem registro e quem só atua em outro grupo"),
        ("Medida principal", "dias planejados dos cartões concluídos, somados por responsável",
         "pesa o cartão pelo tamanho e herda os dias por tamanho do R04"),
        ("Faixas de leitura", "até 0,2 distribuído; até 0,4 moderado; acima disso, concentrado",
         "orientam a conversa; não são régua oficial"),
        ("Poucos registros", "aviso quando uma medida de contagem tem menos de 14 registros no recorte",
         "2 por integrante; abaixo disso o índice sobe por construção"),
        ("Registro sem dono", "fica fora do índice e vira uma faixa possível (mínimo nivelando, máximo para quem tem mais)",
         "não se sabe de quem é"),
    ],
    "R06": [
        ("Eixo de tarefa", "rótulo do cartão agrupado em Código (CODE, BUG, Fix, TEST, DEPLOY, CODE_REVIEW), "
         "Design (DESIGN), Documentação (DOCUMENTATION, REQUIREMENTS, user-story) e Negócio (NEGÓCIOS, Presentation)",
         "não há rótulo UX no conjunto, e DESIGN é o mais próximo; os outros rótulos são tamanho, prioridade, artefato ou etapa"),
        ("Cartões do integrante", "os que têm o integrante como responsável, abertos e fechados; integrante é o mesmo do R05 (7 por grupo)",
         "o eixo mostra em que a pessoa foi alocada, não só o que ela concluiu"),
        ("Cartão de dois eixos", "conta metade em cada eixo",
         "assim a parte de cada integrante soma 100%"),
        ("Foco num eixo só", "75% ou mais dos cartões do integrante num mesmo eixo, ajustável para 60% ou 90% na tela",
         "três de cada quatro cartões no mesmo tipo de tarefa"),
        ("Poucos cartões", "aviso quando o integrante tem menos de 10 cartões com eixo no recorte",
         "com menos de 10, um cartão só muda a parte de um eixo em mais de 10 pontos"),
    ],
}
REQUISITOS = RAIZ / "requisitos" / "Requisitos.MD"


def premissas(tela: str) -> list[dict]:
    """Premissas da tela, conferidas contra o requisito."""
    texto_req = REQUISITOS.read_text(encoding="utf-8")
    faltam = [n for n, v, _ in PREMISSAS[tela] if f"**{n}**: {v}" not in texto_req]
    if faltam:
        sys.exit(f"{tela}: premissa fora do Requisitos.MD ({', '.join(faltam)}). "
                 "Rode dashboard/premissas_no_requisito.py.")
    return [{"nome": n, "valor": v, "por_que": p} for n, v, p in PREMISSAS[tela]]


# Versão em preto, branco e cinza. Os tokens são redeclarados depois dos
# originais, nos mesmos três escopos, então vencem pela ordem. As duas séries
# viram cinza médio e quase preto; forma e rótulo seguem carregando a
# identidade (a cor nunca é o único canal).
_PB_CLARO = """
  --page: #f5f5f5; --surface: #ffffff; --ink: #111111; --ink-2: #4a4a4a;
  --muted: #6b6b6b; --grid: #e2e2e2; --axis: #bdbdbd; --series: #8a8a8a;
  --series-strong: #111111; --series-2: #1f1f1f; --wash-2: rgba(0, 0, 0, 0.05);
  --wash: rgba(0, 0, 0, 0.04); --hover: rgba(0, 0, 0, 0.06); --zero: #9e9e9e;
  --border: rgba(0, 0, 0, 0.12); --chip: #ededed; --focus: #111111;"""
_PB_ESCURO = """
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a1a; --ink: #ffffff; --ink-2: #c4c4c4;
  --muted: #a3a3a3; --grid: #2c2c2c; --axis: #3d3d3d; --series: #7a7a7a;
  --series-strong: #f5f5f5; --series-2: #ededed; --wash-2: rgba(255, 255, 255, 0.06);
  --wash: rgba(255, 255, 255, 0.04); --hover: rgba(255, 255, 255, 0.08); --zero: #6b6b6b;
  --border: rgba(255, 255, 255, 0.12); --chip: #2c2c2c; --focus: #ffffff;"""
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


def conectar() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True)


def ler_sql(nome: str) -> str:
    return (SQLITE / nome).read_text(encoding="utf-8")


def consultar(con: sqlite3.Connection, sql: str, *params) -> list[dict]:
    cur = con.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, linha)) for linha in cur.fetchall()]


def trocar_uma_vez(texto: str, antes: str, depois: str) -> str:
    """Troca um trecho que tem de existir exatamente uma vez (senão, para)."""
    n = texto.count(antes)
    if n != 1:
        sys.exit(f"Esperava 1 ocorrência de {antes!r}, achei {n}. O .sql mudou?")
    return texto.replace(antes, depois)


def registro_mais_recente(con: sqlite3.Connection) -> str:
    return con.execute("""
        SELECT MAX(t) FROM (
            SELECT MAX(ultima_atividade_em) t FROM grupos
            UNION ALL SELECT MAX(ocorrido_em) FROM kanban_eventos
            UNION ALL SELECT MAX(atualizado_em) FROM cartoes
            UNION ALL SELECT MAX(atualizado_em) FROM merge_requests
            UNION ALL SELECT MAX(commitado_em) FROM commits)""").fetchone()[0][:10]


def conferir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        sys.exit("CONFERÊNCIA FALHOU: " + mensagem)


def gravar(modelo: str, dados: dict, saida: str, titulo: str) -> None:
    tela = modelo[:3].upper()   # "r02_modelo.html" -> "R02"; a visão geral não tem premissas próprias
    dados = dict(dados, telas=TELAS, entrada_repositorio=ENTRADA_NO_REPOSITORIO,
                 premissas=premissas(tela) if tela in PREMISSAS else [])
    bloco = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (PASTA / modelo).read_text(encoding="utf-8")
    for marcador, conteudo in (("/*__CSS_COMUM__*/", (PASTA / "comum.css").read_text(encoding="utf-8")),
                               ("//__JS_COMUM__", (PASTA / "comum.js").read_text(encoding="utf-8"))):
        html = trocar_uma_vez(html, marcador, conteudo)
    html = trocar_uma_vez(html, "__DADOS__", bloco)
    colorida = PASTA / saida
    colorida.write_text(html, encoding="utf-8")
    pb = PASTA / saida.replace(".html", "_pb.html")
    pb.write_text(trocar_uma_vez(html, f"<title>{titulo}</title>", f"<title>{titulo} P&amp;B</title>")
                  .replace("</style>", TEMA_PB + "</style>", 1), encoding="utf-8")
    print(f"-> {colorida}\n-> {pb}")
