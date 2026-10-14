"""Fase F - painel analítico lido do DuckDB.

Lê somente saida/olist.duckdb (read_only) e gera saida/dashboard_duckdb.html com
KPIs de receita, pedidos e ticket; série mensal; top 10 categorias com cobertura;
estados com receita e pedidos; reconciliação; duração e SQL resumido de cada
consulta. Pedidos e ticket vêm da fato_item_venda com count(DISTINCT order_id)
no grão de cada consulta; o mart categórico só fornece medidas aditivas.
Nenhum número é digitado: tudo sai das consultas. Não abre o SQLite.
"""
import html
import sys
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent.parent
DUCK = BASE / "saida" / "olist.duckdb"
DESTINO = BASE / "saida" / "dashboard_duckdb.html"
TOP_N = 10
LIMIAR_MES_RALO = 0.01  # mês com menos de 1% dos pedidos do maior mês é marcado como parcial

CSS = """
:root{--fundo:#fafaf7;--superficie:#ffffff;--texto:#141413;--texto-2:#52514e;--texto-3:#6f6e69;
--borda:#dedcd5;--grade:#ebe9e3;--serie:#2a78d6;--serie-2:#9ec3ef;--zebra:#f4f3ee;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--fundo:#141413;--superficie:#1d1d1b;
--texto:#f0efec;--texto-2:#c3c2b7;--texto-3:#9a998f;--borda:#3a3936;--grade:#2c2b29;--serie:#3987e5;
--serie-2:#28507e;--zebra:#232321;color-scheme:dark}}
:root[data-theme="dark"]{--fundo:#141413;--superficie:#1d1d1b;--texto:#f0efec;--texto-2:#c3c2b7;
--texto-3:#9a998f;--borda:#3a3936;--grade:#2c2b29;--serie:#3987e5;--serie-2:#28507e;--zebra:#232321;
color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--texto);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
header,main,footer{max-width:1100px;margin:0 auto;padding:0 16px}
header{padding-top:28px}
h1{font-size:1.6rem;margin:0 0 4px}
h2{font-size:1.15rem;margin:0 0 6px}
h3{font-size:1rem;margin:14px 0 6px}
p{margin:6px 0}
.meta{color:var(--texto-2);font-size:.9rem;margin:2px 0}
.nota{color:var(--texto-2);font-size:.88rem}
code,.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;font-size:.85em;overflow-wrap:anywhere}
.meta,p{overflow-wrap:anywhere}
section{background:var(--superficie);border:1px solid var(--borda);border-radius:4px;padding:16px;margin:16px 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:0;padding:0;list-style:none}
.kpis li{border:1px solid var(--borda);border-radius:4px;padding:12px}
.kpis .rotulo{display:block;color:var(--texto-2);font-size:.85rem}
.kpis .valor{display:block;font-size:1.3rem;white-space:nowrap;font-weight:650;font-variant-numeric:tabular-nums}
.kpis .det{display:block;color:var(--texto-3);font-size:.8rem}
.rolagem{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
caption{text-align:left;color:var(--texto-2);font-size:.85rem;padding-bottom:6px}
th,td{padding:5px 8px;border-bottom:1px solid var(--borda);text-align:left;vertical-align:top}
th{font-weight:600}
td.num,th.num{text-align:right;white-space:nowrap}
tbody tr:nth-child(even){background:var(--zebra)}
tr.outros td{font-style:italic;color:var(--texto-2)}
.barra{display:inline-block;height:10px;border-radius:0 4px 4px 0;background:var(--serie);vertical-align:middle}
figure{margin:8px 0 12px}
figcaption{color:var(--texto-2);font-size:.85rem}
svg{display:block;width:100%;height:auto;overflow:visible}
svg text{fill:var(--texto-2);font-size:11px;font-family:inherit}
svg .eixo{stroke:var(--borda)}
svg .grade{stroke:var(--grade)}
svg rect.m{fill:var(--serie)}
svg rect.m.parcial{fill:var(--serie-2)}
svg rect.alvo{fill:transparent}
svg g.ponto:hover rect.m,svg g.ponto:focus rect.m{opacity:.75}
.dica{position:fixed;pointer-events:none;background:var(--superficie);color:var(--texto);border:1px solid var(--borda);
border-radius:4px;padding:6px 8px;font-size:.82rem;box-shadow:0 2px 8px rgba(0,0,0,.18);display:none;z-index:5;
white-space:pre-line}
.ok{font-weight:600}
.falha{font-weight:600;text-decoration:underline}
footer{color:var(--texto-2);font-size:.85rem;padding-bottom:32px}
"""

JS = """
(function(){
  var dica=document.createElement('div');dica.className='dica';dica.setAttribute('role','status');
  document.body.appendChild(dica);
  function mostrar(ev,el){dica.textContent=el.getAttribute('data-dica');dica.style.display='block';
    var x=(ev.clientX||el.getBoundingClientRect().left)+12,y=(ev.clientY||el.getBoundingClientRect().top)+12;
    var w=dica.offsetWidth;if(x+w>window.innerWidth-8){x=window.innerWidth-w-8;}
    dica.style.left=x+'px';dica.style.top=y+'px';}
  document.querySelectorAll('[data-dica]').forEach(function(el){
    el.addEventListener('pointermove',function(ev){mostrar(ev,el);});
    el.addEventListener('focus',function(ev){mostrar(ev,el);});
    el.addEventListener('pointerleave',function(){dica.style.display='none';});
    el.addEventListener('blur',function(){dica.style.display='none';});
  });
})();
"""


def e(v):
    return html.escape("" if v is None else str(v))


def fmt_int(n):
    return f"{int(n):,}".replace(",", ".")


def fmt_dec(x, casas=2):
    s = f"{float(x):,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_brl(x):
    return "R$ " + fmt_dec(x)


def fmt_brl_curto(x):
    x = float(x)
    if abs(x) >= 1e6:
        return "R$ " + fmt_dec(x / 1e6, 1) + " mi"
    if abs(x) >= 1e3:
        return "R$ " + fmt_dec(x / 1e3, 0) + " mil"
    return "R$ " + fmt_dec(x, 0)


def passo_eixo(maximo, alvo=4):
    """Passo 'redondo' (1, 2, 2,5 ou 5 x 10^k) para cerca de `alvo` linhas de grade."""
    if maximo <= 0:
        return 1
    bruto = maximo / alvo
    k = 10 ** (len(str(int(bruto))) - 1)
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * k:
            return m * k
    return 10 * k


def grafico_colunas(rotulos, valores, fmt_valor, fmt_eixo, titulo_id, parciais, dicas):
    """Colunas verticais em SVG, uma série, com grade recessiva e dica ao passar o ponteiro."""
    larg, alt, esq, dir_, topo, base = 960, 260, 64, 8, 10, 34
    area_l, area_a = larg - esq - dir_, alt - topo - base
    vmax = max(valores) if valores else 1
    passo = passo_eixo(vmax)
    teto = passo * (int(vmax / passo) + (0 if vmax % passo == 0 else 1))
    n = len(valores)
    banda = area_l / max(n, 1)
    larg_barra = max(banda - 2, 1)  # 2 px de respiro entre colunas
    partes = [f'<svg viewBox="0 0 {larg} {alt}" role="img" aria-labelledby="{titulo_id}">']
    v = 0
    while v <= teto + 1e-9:
        y = topo + area_a - area_a * v / teto
        partes.append(f'<line class="grade" x1="{esq}" x2="{larg - dir_}" y1="{y:.1f}" y2="{y:.1f}"/>')
        partes.append(f'<text x="{esq - 6}" y="{y + 4:.1f}" text-anchor="end">{e(fmt_eixo(v))}</text>')
        v += passo
    partes.append(f'<line class="eixo" x1="{esq}" x2="{larg - dir_}" y1="{topo + area_a}" y2="{topo + area_a}"/>')
    salto = max(1, round(n / 12))
    for i, (r, val) in enumerate(zip(rotulos, valores)):
        x = esq + i * banda + 1
        h = area_a * val / teto
        y = topo + area_a - h
        raio = min(4, larg_barra / 2, h)
        cls = "m parcial" if parciais[i] else "m"
        # Topo arredondado (4 px), base reta apoiada no eixo.
        caminho = (f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{larg_barra:.1f}" height="{h:.1f}" '
                   f'rx="{raio:.1f}"/>')
        if h > raio:
            caminho += (f'<rect class="{cls}" x="{x:.1f}" y="{y + h - raio:.1f}" width="{larg_barra:.1f}" '
                        f'height="{raio:.1f}"/>')
        partes.append(f'<g class="ponto" tabindex="0" data-dica="{e(dicas[i])}">'
                      f'<title>{e(dicas[i])}</title>{caminho}'
                      f'<rect class="alvo" x="{esq + i * banda:.1f}" y="{topo}" width="{banda:.1f}" height="{area_a}"/></g>')
        if i % salto == 0 or i == n - 1:
            partes.append(f'<text x="{x + larg_barra / 2:.1f}" y="{alt - base + 16}" text-anchor="middle">{e(r)}</text>')
    partes.append("</svg>")
    return "".join(partes)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    con = duckdb.connect(str(DUCK), read_only=True)
    consultas = []

    def consultar(nome, sql):
        t0 = time.perf_counter()
        linhas = con.execute(sql).fetchall()
        ms = (time.perf_counter() - t0) * 1000
        consultas.append({"nome": nome, "sql": " ".join(sql.split()), "ms": ms, "linhas": len(linhas)})
        return linhas

    kpi = consultar("KPIs", """
        SELECT sum(CAST(price AS DECIMAL(18,2))) AS receita,
               sum(CAST(freight_value AS DECIMAL(18,2))) AS frete,
               count(DISTINCT order_id) AS pedidos,
               sum(CAST(price AS DECIMAL(18,2))) / count(DISTINCT order_id) AS ticket,
               count(*) AS itens,
               min(data_compra) AS primeira, max(data_compra) AS ultima,
               count(DISTINCT order_status) AS status_distintos
        FROM fato_item_venda""")[0]
    receita, frete, pedidos, ticket, itens, primeira, ultima, n_status = kpi

    # Calendário completo entre o primeiro e o último mês: mês sem compra aparece com zero, não some.
    mensal = consultar("série mensal", """
        WITH m AS (SELECT mes, sum(CAST(price AS DECIMAL(18,2))) AS receita,
                          count(DISTINCT order_id) AS pedidos, count(*) AS itens
                   FROM fato_item_venda GROUP BY mes),
             cal AS (SELECT CAST(range AS DATE) AS mes
                     FROM range((SELECT min(mes) FROM m), (SELECT max(mes) FROM m) + INTERVAL 1 MONTH,
                                INTERVAL 1 MONTH))
        SELECT strftime(cal.mes, '%Y-%m') AS mes, coalesce(m.receita, 0) AS receita,
               coalesce(m.pedidos, 0) AS pedidos, m.receita / m.pedidos AS ticket,
               coalesce(m.itens, 0) AS itens
        FROM cal LEFT JOIN m USING (mes) ORDER BY cal.mes""")

    categorias = consultar("top categorias com cobertura (mart)", f"""
        WITH cat AS (SELECT categoria, sum(receita_produtos) AS receita, sum(itens) AS itens
                     FROM mart_vendas_mensais GROUP BY categoria),
        r AS (SELECT categoria, receita, itens,
                     row_number() OVER (ORDER BY receita DESC, categoria) AS posicao,
                     100 * receita / sum(receita) OVER () AS percentual,
                     100 * sum(receita) OVER (ORDER BY receita DESC, categoria
                                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                         / sum(receita) OVER () AS cobertura_acumulada,
                     count(*) OVER () AS categorias_total
              FROM cat)
        SELECT posicao, categoria, receita, itens, percentual, cobertura_acumulada, categorias_total
        FROM r WHERE posicao <= {TOP_N} ORDER BY posicao""")
    top_nomes = [c[1] for c in categorias]
    lista_sql = ", ".join("'" + n.replace("'", "''") + "'" for n in top_nomes)

    pedidos_cat = dict((c, (p, t)) for c, p, t in consultar("pedidos e ticket do top 10 (fato)", f"""
        SELECT categoria, count(DISTINCT order_id) AS pedidos,
               sum(CAST(price AS DECIMAL(18,2))) / count(DISTINCT order_id) AS ticket
        FROM fato_item_venda WHERE categoria IN ({lista_sql}) GROUP BY categoria"""))

    outros = consultar("cauda fora do top 10 (mart e fato)", f"""
        WITH m AS (SELECT count(DISTINCT categoria) AS categorias, sum(receita_produtos) AS receita,
                          sum(itens) AS itens
                   FROM mart_vendas_mensais WHERE categoria NOT IN ({lista_sql})),
             f AS (SELECT count(DISTINCT order_id) AS pedidos FROM fato_item_venda
                   WHERE categoria NOT IN ({lista_sql}))
        SELECT m.categorias, m.receita, m.itens, f.pedidos FROM m, f""")[0]

    estados = consultar("estados (mart + fato)", """
        WITH m AS (SELECT estado_cliente, sum(receita_produtos) AS receita, sum(frete) AS frete
                   FROM mart_vendas_mensais GROUP BY estado_cliente),
             f AS (SELECT estado_cliente, count(DISTINCT order_id) AS pedidos FROM fato_item_venda
                   GROUP BY estado_cliente)
        SELECT m.estado_cliente, m.receita, f.pedidos, m.receita / f.pedidos AS ticket, m.frete,
               100 * m.receita / sum(m.receita) OVER () AS percentual
        FROM m JOIN f USING (estado_cliente) ORDER BY m.receita DESC""")

    rec = consultar("reconciliação fato x mart", """
        SELECT (SELECT sum(CAST(price AS DECIMAL(18,2))) FROM fato_item_venda) AS receita_fato,
               (SELECT sum(receita_produtos) FROM mart_vendas_mensais) AS receita_mart,
               (SELECT count(*) FROM fato_item_venda) AS itens_fato,
               (SELECT sum(itens) FROM mart_vendas_mensais) AS itens_mart,
               (SELECT count(DISTINCT order_id) FROM olist_order_items) AS pedidos_com_item,
               (SELECT sum(n) FROM (SELECT count(DISTINCT order_id) AS n FROM fato_item_venda
                                    GROUP BY categoria)) AS soma_pedidos_por_categoria""")[0]
    status_itens = consultar("itens por status do pedido (fato)", """
        SELECT order_status, count(*) AS itens, count(DISTINCT order_id) AS pedidos,
               sum(CAST(price AS DECIMAL(18,2))) AS receita
        FROM fato_item_venda GROUP BY order_status ORDER BY itens DESC""")
    versao = con.execute("SELECT version()").fetchone()[0]
    con.close()

    receita_fato, receita_mart, itens_fato, itens_mart, pedidos_com_item, soma_ped_cat = rec
    soma_estados = sum(Decimal(r[1]) for r in estados)
    soma_ped_estados = sum(int(r[2]) for r in estados)
    soma_mensal = sum(Decimal(r[1]) for r in mensal)
    soma_ped_mensal = sum(int(r[2]) for r in mensal)
    top_receita = sum(Decimal(c[2]) for c in categorias)
    checagens = [
        ("Receita do KPI (fato) = soma do mart", fmt_brl(receita_fato), fmt_brl(receita_mart), receita_fato == receita_mart),
        ("Itens da fato = soma de itens do mart", fmt_int(itens_fato), fmt_int(itens_mart), itens_fato == itens_mart),
        ("Soma da receita por estado = KPI", fmt_brl(soma_estados), fmt_brl(receita), soma_estados == receita),
        ("Soma da receita mensal = KPI", fmt_brl(soma_mensal), fmt_brl(receita), soma_mensal == receita),
        ("Top 10 + outros = KPI", fmt_brl(top_receita + Decimal(outros[1])), fmt_brl(receita),
         top_receita + Decimal(outros[1]) == receita),
        ("Pedidos do KPI = pedidos distintos em olist_order_items", fmt_int(pedidos), fmt_int(pedidos_com_item),
         pedidos == pedidos_com_item),
        ("Soma de pedidos por estado = KPI (cada pedido tem um só cliente)", fmt_int(soma_ped_estados),
         fmt_int(pedidos), soma_ped_estados == pedidos),
        ("Soma de pedidos por mês = KPI (cada pedido tem uma só data)", fmt_int(soma_ped_mensal),
         fmt_int(pedidos), soma_ped_mensal == pedidos),
    ]
    falhas = [c[0] for c in checagens if not c[3]]

    gerado = datetime.now().astimezone().isoformat(timespec="seconds")
    max_pedidos_mes = max(int(m[2]) for m in mensal)
    parciais = [int(m[2]) < LIMIAR_MES_RALO * max_pedidos_mes for m in mensal]
    cobertura_top = categorias[-1][5] if categorias else 0
    n_categorias = categorias[0][6] if categorias else 0
    pct_outros = 100 * Decimal(outros[1]) / receita

    def nota_mes(i, m):
        if m[2] == 0:
            return "\nsem compras no dataset"
        return "\nmês parcial" if parciais[i] else ""

    dicas_receita = [f"{m[0]}\nReceita {fmt_brl(m[1])}\nPedidos {fmt_int(m[2])}" + nota_mes(i, m)
                     for i, m in enumerate(mensal)]
    graf_receita = grafico_colunas([m[0] for m in mensal], [float(m[1]) for m in mensal], fmt_brl,
                                   fmt_brl_curto, "g-receita", parciais, dicas_receita)
    dicas_ped = [f"{m[0]}\nPedidos {fmt_int(m[2])}" + (f"\nTicket {fmt_brl(m[3])}" if m[3] is not None else "")
                 + nota_mes(i, m) for i, m in enumerate(mensal)]
    graf_pedidos = grafico_colunas([m[0] for m in mensal], [int(m[2]) for m in mensal], fmt_int,
                                   lambda v: fmt_int(v), "g-pedidos", parciais, dicas_ped)
    meses_parciais = [m[0] for i, m in enumerate(mensal) if parciais[i] and m[2] > 0]
    meses_vazios = [m[0] for m in mensal if m[2] == 0]

    P = []
    P.append(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Painel Olist DuckDB</title>
<style>{CSS}</style>
</head>
<body>
<header>
<h1>Painel analítico do Olist em DuckDB</h1>
<p class="meta">Fonte: <code>saida/olist.duckdb</code> (tabelas <code>fato_item_venda</code> e <code>mart_vendas_mensais</code>), aberto em modo somente leitura; {e(versao)}.</p>
<p class="meta">Gerado em <time datetime="{e(gerado)}">{e(gerado)}</time> por <code>src/05_html_duckdb.py</code>. Período das compras: {e(primeira)} a {e(ultima)}.</p>
</header>
<main>
<section aria-labelledby="t-kpis">
<h2 id="t-kpis">Indicadores gerais</h2>
<ul class="kpis">
<li><span class="rotulo">Receita de produtos</span><span class="valor">{e(fmt_brl(receita))}</span><span class="det">sum(price) na fato</span></li>
<li><span class="rotulo">Pedidos</span><span class="valor">{e(fmt_int(pedidos))}</span><span class="det">count(DISTINCT order_id)</span></li>
<li><span class="rotulo">Ticket médio de produtos</span><span class="valor">{e(fmt_brl(ticket))}</span><span class="det">receita / pedidos distintos</span></li>
<li><span class="rotulo">Itens vendidos</span><span class="valor">{e(fmt_int(itens))}</span><span class="det">count(*) no grão do item</span></li>
<li><span class="rotulo">Frete</span><span class="valor">{e(fmt_brl(frete))}</span><span class="det">sum(freight_value), fora da receita</span></li>
</ul>
<p class="nota">Inclui itens de pedidos em todos os {e(fmt_int(n_status))} status (entregues, cancelados, em trânsito etc.); a tabela de status no fim da página mostra a composição.</p>
</section>

<section aria-labelledby="t-mensal">
<h2 id="t-mensal">Série mensal</h2>
<figure>
<figcaption id="g-receita">Receita de produtos por mês da compra, em R$. Colunas claras marcam meses com menos de {e(fmt_dec(100 * LIMIAR_MES_RALO, 0))}% dos pedidos do maior mês (provável cobertura parcial): {e(", ".join(meses_parciais) or "nenhum")}. Meses sem nenhuma compra no dataset aparecem vazios, sem estimativa: {e(", ".join(meses_vazios) or "nenhum")}.</figcaption>
{graf_receita}
</figure>
<figure>
<figcaption id="g-pedidos">Pedidos distintos por mês da compra (count(DISTINCT order_id) no grão do mês).</figcaption>
{graf_pedidos}
</figure>
<h3>Tabela equivalente</h3>
<div class="rolagem"><table>
<caption>Uma linha por mês; pedidos e ticket calculados na fato no grão do mês.</caption>
<thead><tr><th scope="col">Mês</th><th scope="col" class="num">Receita (R$)</th><th scope="col" class="num">Pedidos</th>
<th scope="col" class="num">Ticket (R$)</th><th scope="col" class="num">Itens</th><th scope="col">Observação</th></tr></thead>
<tbody>""")
    for i, (mes, r, p, t, n) in enumerate(mensal):
        obs = "sem compras no dataset" if p == 0 else ("mês parcial" if parciais[i] else "")
        P.append(f"<tr><td>{e(mes)}</td><td class='num'>{e(fmt_dec(r))}</td><td class='num'>{e(fmt_int(p))}</td>"
                 f"<td class='num'>{e(fmt_dec(t)) if t is not None else '-'}</td><td class='num'>{e(fmt_int(n))}</td>"
                 f"<td>{obs}</td></tr>")
    P.append(f"""</tbody></table></div>
</section>

<section aria-labelledby="t-cat">
<h2 id="t-cat">Top {TOP_N} categorias e cobertura</h2>
<p>As {e(fmt_int(len(categorias)))} maiores categorias, entre {e(fmt_int(n_categorias))}, cobrem <strong>{e(fmt_dec(cobertura_top))}%</strong> da receita de produtos.
As outras {e(fmt_int(outros[0]))} categorias somam {e(fmt_brl(outros[1]))}, ou {e(fmt_dec(pct_outros))}% da receita.</p>
<p class="nota">Receita e itens vêm do mart; pedidos e ticket de cada categoria vêm da fato. A soma dos pedidos por categoria ({e(fmt_int(soma_ped_cat))}) é maior que o total de pedidos ({e(fmt_int(pedidos))}) porque um pedido pode ter itens de mais de uma categoria; por isso não se somam pedidos entre categorias. Produtos sem categoria aparecem como <code>(sem categoria)</code>.</p>
<div class="rolagem"><table>
<caption>Ordenado por receita; cobertura acumulada calculada com janela no DuckDB.</caption>
<thead><tr><th scope="col" class="num">#</th><th scope="col">Categoria</th><th scope="col" class="num">Receita (R$)</th>
<th scope="col" class="num">% da receita</th><th scope="col" class="num">Cobertura acumulada</th><th scope="col">Participação</th>
<th scope="col" class="num">Pedidos</th><th scope="col" class="num">Ticket (R$)</th><th scope="col" class="num">Itens</th></tr></thead>
<tbody>""")
    maior_cat = float(categorias[0][2]) if categorias else 1
    for pos, cat, r, n, pct, cob, _ in categorias:
        p_cat, t_cat = pedidos_cat[cat]
        P.append(f"<tr><td class='num'>{e(pos)}</td><td>{e(cat)}</td><td class='num'>{e(fmt_dec(r))}</td>"
                 f"<td class='num'>{e(fmt_dec(pct))}%</td><td class='num'>{e(fmt_dec(cob))}%</td>"
                 f"<td><span class='barra' style='width:{100 * float(r) / maior_cat:.2f}%' aria-hidden='true'></span></td>"
                 f"<td class='num'>{e(fmt_int(p_cat))}</td><td class='num'>{e(fmt_dec(t_cat))}</td>"
                 f"<td class='num'>{e(fmt_int(n))}</td></tr>")
    P.append(f"<tr class='outros'><td class='num'></td><td>outras {e(fmt_int(outros[0]))} categorias</td>"
             f"<td class='num'>{e(fmt_dec(outros[1]))}</td><td class='num'>{e(fmt_dec(pct_outros))}%</td>"
             f"<td class='num'>{e(fmt_dec(100))}%</td><td></td><td class='num'>{e(fmt_int(outros[3]))}</td>"
             f"<td class='num'>{e(fmt_dec(Decimal(outros[1]) / outros[3]))}</td><td class='num'>{e(fmt_int(outros[2]))}</td></tr>")
    P.append("""</tbody></table></div>
</section>

<section aria-labelledby="t-uf">
<h2 id="t-uf">Estados do cliente</h2>
<div class="rolagem"><table>
<caption>Receita e frete do mart; pedidos distintos e ticket da fato no grão do estado.</caption>
<thead><tr><th scope="col">UF</th><th scope="col" class="num">Receita (R$)</th><th scope="col" class="num">% da receita</th>
<th scope="col">Participação</th><th scope="col" class="num">Pedidos</th><th scope="col" class="num">Ticket (R$)</th>
<th scope="col" class="num">Frete (R$)</th></tr></thead>
<tbody>""")
    maior_uf = float(estados[0][1]) if estados else 1
    for uf, r, p, t, fr, pct in estados:
        P.append(f"<tr><td>{e(uf)}</td><td class='num'>{e(fmt_dec(r))}</td><td class='num'>{e(fmt_dec(pct))}%</td>"
                 f"<td><span class='barra' style='width:{100 * float(r) / maior_uf:.2f}%' aria-hidden='true'></span></td>"
                 f"<td class='num'>{e(fmt_int(p))}</td><td class='num'>{e(fmt_dec(t))}</td>"
                 f"<td class='num'>{e(fmt_dec(fr))}</td></tr>")
    P.append("""</tbody></table></div>
</section>

<section aria-labelledby="t-rec">
<h2 id="t-rec">Reconciliação</h2>
<div class="rolagem"><table>
<caption>Comparações calculadas a partir das próprias consultas desta página.</caption>
<thead><tr><th scope="col">Verificação</th><th scope="col" class="num">Obtido</th><th scope="col" class="num">Referência</th>
<th scope="col">Resultado</th></tr></thead>
<tbody>""")
    for nome, a, b, ok in checagens:
        P.append(f"<tr><td>{e(nome)}</td><td class='num'>{e(a)}</td><td class='num'>{e(b)}</td>"
                 f"<td class='{'ok' if ok else 'falha'}'>{'confere' if ok else 'DIVERGE'}</td></tr>")
    P.append("""</tbody></table></div>
<h3>Itens por status do pedido</h3>
<div class="rolagem"><table>
<caption>Composição da fato por status; nenhum status foi filtrado.</caption>
<thead><tr><th scope="col">Status</th><th scope="col" class="num">Itens</th><th scope="col" class="num">Pedidos</th>
<th scope="col" class="num">Receita (R$)</th></tr></thead>
<tbody>""")
    for s, n, p, r in status_itens:
        P.append(f"<tr><td>{e(s)}</td><td class='num'>{e(fmt_int(n))}</td><td class='num'>{e(fmt_int(p))}</td>"
                 f"<td class='num'>{e(fmt_dec(r))}</td></tr>")
    P.append("""</tbody></table></div>
</section>

<section aria-labelledby="t-consultas">
<h2 id="t-consultas">Consultas executadas</h2>
<div class="rolagem"><table>
<caption>Uma execução de cada consulta, medida com <code>time.perf_counter</code>, incluindo a transferência das linhas para o Python.</caption>
<thead><tr><th scope="col">Consulta</th><th scope="col" class="num">Linhas</th><th scope="col" class="num">ms</th><th scope="col">SQL resumido</th></tr></thead>
<tbody>""")
    for c in consultas:
        sql = c["sql"] if len(c["sql"]) <= 200 else c["sql"][:197] + "..."
        P.append(f"<tr><td>{e(c['nome'])}</td><td class='num'>{e(fmt_int(c['linhas']))}</td>"
                 f"<td class='num'>{e(fmt_dec(c['ms'], 1))}</td><td><code>{e(sql)}</code></td></tr>")
    P.append(f"""</tbody></table></div>
</section>
</main>
<footer>
<p>Limitações: espelho educacional do dataset público Olist (Kaggle, 2018, CC BY-NC-SA 4.0), carregado dos quatro Excels da Aula 04.
Receita aqui é a soma de <code>price</code> dos itens, sem frete, sem pagamentos e sem descontos; pagamentos e avaliações não entram na fato.
O mês é o da data de compra. Meses nas pontas da série têm poucos pedidos e não devem ser lidos como tendência.
Os tempos valem para esta máquina e esta execução.</p>
</footer>
<script>{JS}</script>
</body>
</html>
""")
    DESTINO.write_text("\n".join(P), encoding="utf-8")
    print(f"gravado {DESTINO.relative_to(BASE)}")
    print(f"  receita {receita} | pedidos {pedidos} | ticket {ticket:.2f} | top {TOP_N} cobre {cobertura_top:.2f}%")
    for c in consultas:
        print(f"  [{c['ms']:.1f} ms] {c['nome']}")
    if falhas:
        for f in falhas:
            print("FALHA:", f)
        raise SystemExit(1)
    print("GATE F PASSOU")


if __name__ == "__main__":
    main()
