"""Fase C - HTML operacional lido do SQLite.

Abre saida/olist.sqlite em modo somente leitura (URI mode=ro) e gera
saida/relatorio_sqlite.html: contagem das nove tabelas, relações declaradas,
pedidos por status, cinco pedidos mais recentes e a duração de cada consulta.
Todo número da página sai de uma consulta executada agora; o texto é escapado.
"""
import html
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BANCO = BASE / "saida" / "olist.sqlite"
DESTINO = BASE / "saida" / "relatorio_sqlite.html"

CSS = """
:root{--fundo:#fafaf7;--superficie:#ffffff;--texto:#141413;--texto-2:#52514e;--borda:#dedcd5;
--barra:#2a78d6;--zebra:#f4f3ee;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--fundo:#141413;--superficie:#1d1d1b;
--texto:#f0efec;--texto-2:#c3c2b7;--borda:#3a3936;--barra:#3987e5;--zebra:#232321;color-scheme:dark}}
:root[data-theme="dark"]{--fundo:#141413;--superficie:#1d1d1b;--texto:#f0efec;--texto-2:#c3c2b7;
--borda:#3a3936;--barra:#3987e5;--zebra:#232321;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--texto);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
header,main,footer{max-width:1100px;margin:0 auto;padding:0 16px}
header{padding-top:28px}
h1{font-size:1.6rem;margin:0 0 4px}
h2{font-size:1.15rem;margin:0 0 10px}
.meta{color:var(--texto-2);font-size:.9rem;margin:2px 0}
code,.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace;font-size:.85em;overflow-wrap:anywhere}
.meta,p{overflow-wrap:anywhere}
section{background:var(--superficie);border:1px solid var(--borda);border-radius:4px;padding:16px;margin:16px 0}
.rolagem{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
caption{text-align:left;color:var(--texto-2);font-size:.85rem;padding-bottom:6px}
th,td{padding:6px 8px;border-bottom:1px solid var(--borda);text-align:left;vertical-align:top}
th{font-weight:600}
td.num,th.num{text-align:right;white-space:nowrap}
tbody tr:nth-child(even){background:var(--zebra)}
.barra{display:inline-block;height:10px;border-radius:0 4px 4px 0;background:var(--barra);vertical-align:middle}
footer{color:var(--texto-2);font-size:.85rem;padding-bottom:32px}
"""


def e(valor):
    return html.escape("" if valor is None else str(valor))


def fmt_int(n):
    return f"{n:,}".replace(",", ".")


def fmt_dec(x, casas=2):
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    uri = BANCO.resolve().as_uri() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    consultas = []

    def consultar(nome, sql, params=()):
        t0 = time.perf_counter()
        linhas = con.execute(sql, params).fetchall()
        ms = (time.perf_counter() - t0) * 1000
        consultas.append({"nome": nome, "sql": " ".join(sql.split()), "ms": ms, "linhas": len(linhas)})
        return linhas

    tabelas = [r[0] for r in consultar(
        "catálogo", "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    sql_contagens = " UNION ALL ".join(f"SELECT '{t}', count(*) FROM {t}" for t in tabelas)
    contagens = consultar("contagem das tabelas", sql_contagens)

    relacoes = consultar("relações declaradas", """
        SELECT m.name, f."from", f."table", f."to"
        FROM sqlite_master m, pragma_foreign_key_list(m.name) f
        WHERE m.type = 'table' ORDER BY m.name, f."from" """)
    fk_check = consultar("foreign_key_check", "PRAGMA foreign_key_check")
    integridade = consultar("integrity_check", "PRAGMA integrity_check")

    status = consultar("pedidos por status", """
        SELECT order_status, count(*) AS pedidos,
               100.0 * count(*) / sum(count(*)) OVER () AS percentual
        FROM olist_orders GROUP BY order_status ORDER BY pedidos DESC""")

    recentes = consultar("cinco pedidos recentes", """
        SELECT o.order_id, o.order_status, o.order_purchase_timestamp, c.customer_city, c.customer_state
        FROM olist_orders AS o JOIN olist_customers AS c ON c.customer_id = o.customer_id
        ORDER BY o.order_purchase_timestamp DESC LIMIT 5""")
    con.close()

    gerado = datetime.now().astimezone().isoformat(timespec="seconds")
    maior_status = max(p for _, p, _ in status) if status else 1
    total_pedidos = sum(p for _, p, _ in status)

    partes = [f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inventário Olist SQLite</title>
<style>{CSS}</style>
</head>
<body>
<header>
<h1>Inventário operacional do Olist em SQLite</h1>
<p class="meta">Fonte: <code>saida/olist.sqlite</code>, aberto em modo somente leitura (<code>mode=ro</code>).</p>
<p class="meta">Gerado em <time datetime="{e(gerado)}">{e(gerado)}</time> por <code>src/02_html_sqlite.py</code>.</p>
</header>
<main>
<section aria-labelledby="t-contagens">
<h2 id="t-contagens">Contagem das tabelas</h2>
<div class="rolagem"><table>
<caption>{e(fmt_int(len(contagens)))} tabelas lidas do catálogo <code>sqlite_master</code>; contagem por <code>count(*)</code>.</caption>
<thead><tr><th scope="col">Tabela</th><th scope="col" class="num">Linhas</th></tr></thead>
<tbody>"""]
    for t, n in contagens:
        partes.append(f"<tr><td><code>{e(t)}</code></td><td class='num'>{e(fmt_int(n))}</td></tr>")
    partes.append(f"""</tbody></table></div>
</section>
<section aria-labelledby="t-relacoes">
<h2 id="t-relacoes">Relações declaradas e integridade</h2>
<p><code>PRAGMA integrity_check</code>: <strong>{e(integridade[0][0])}</strong>.
<code>PRAGMA foreign_key_check</code>: {e(fmt_int(len(fk_check)))} linhas com violação.
Chaves estrangeiras declaradas: {e(fmt_int(len(relacoes)))}.</p>
<div class="rolagem"><table>
<caption>Lidas de <code>pragma_foreign_key_list</code>.</caption>
<thead><tr><th scope="col">Tabela filha</th><th scope="col">Coluna</th><th scope="col">Referência</th></tr></thead>
<tbody>""")
    for t, de, pai, para in relacoes:
        partes.append(f"<tr><td><code>{e(t)}</code></td><td><code>{e(de)}</code></td>"
                      f"<td><code>{e(pai)}({e(para)})</code></td></tr>")
    partes.append(f"""</tbody></table></div>
</section>
<section aria-labelledby="t-status">
<h2 id="t-status">Pedidos por status</h2>
<div class="rolagem"><table>
<caption>{e(fmt_int(total_pedidos))} pedidos em <code>olist_orders</code>; o percentual é calculado no banco com janela.</caption>
<thead><tr><th scope="col">Status</th><th scope="col" class="num">Pedidos</th><th scope="col" class="num">%</th>
<th scope="col">Participação</th></tr></thead>
<tbody>""")
    for s, p, pct in status:
        largura = 100.0 * p / maior_status
        partes.append(f"<tr><td>{e(s)}</td><td class='num'>{e(fmt_int(p))}</td><td class='num'>{e(fmt_dec(pct))}</td>"
                      f"<td><span class='barra' style='width:{largura:.2f}%' aria-hidden='true'></span></td></tr>")
    partes.append("""</tbody></table></div>
</section>
<section aria-labelledby="t-recentes">
<h2 id="t-recentes">Cinco pedidos mais recentes</h2>
<div class="rolagem"><table>
<caption>Ordenados por <code>order_purchase_timestamp</code> decrescente; uma linha por pedido, porque <code>customer_id</code> é único em clientes.</caption>
<thead><tr><th scope="col">Pedido</th><th scope="col">Status</th><th scope="col">Compra</th>
<th scope="col">Cidade</th><th scope="col">UF</th></tr></thead>
<tbody>""")
    for oid, st, ts, cid, uf in recentes:
        partes.append(f"<tr><td class='mono'>{e(oid)}</td><td>{e(st)}</td><td class='mono'>{e(ts)}</td>"
                      f"<td>{e(cid)}</td><td>{e(uf)}</td></tr>")
    partes.append("""</tbody></table></div>
</section>
<section aria-labelledby="t-consultas">
<h2 id="t-consultas">Consultas executadas</h2>
<div class="rolagem"><table>
<caption>Duração medida com <code>time.perf_counter</code> em uma execução, incluindo a leitura das linhas pelo Python.</caption>
<thead><tr><th scope="col">Consulta</th><th scope="col" class="num">Linhas</th><th scope="col" class="num">ms</th>
<th scope="col">SQL resumido</th></tr></thead>
<tbody>""")
    for c in consultas:
        sql = c["sql"] if len(c["sql"]) <= 160 else c["sql"][:157] + "..."
        partes.append(f"<tr><td>{e(c['nome'])}</td><td class='num'>{e(fmt_int(c['linhas']))}</td>"
                      f"<td class='num'>{e(fmt_dec(c['ms'], 1))}</td><td><code>{e(sql)}</code></td></tr>")
    partes.append("""</tbody></table></div>
</section>
</main>
<footer>
<p>Limitações: inventário de um espelho educacional do dataset público Olist (Kaggle, 2018, CC BY-NC-SA 4.0),
carregado dos quatro Excels da Aula 04. Os tempos valem para esta máquina e esta execução.</p>
</footer>
</body>
</html>
""")
    DESTINO.write_text("\n".join(partes), encoding="utf-8")
    print(f"gravado {DESTINO.relative_to(BASE)}")
    for t, n in contagens:
        print(f"  {t}: {n}")
    for c in consultas:
        print(f"  [{c['ms']:.1f} ms] {c['nome']}")


if __name__ == "__main__":
    main()
