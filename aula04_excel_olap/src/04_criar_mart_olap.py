"""Fase E - mart OLAP no DuckDB, sem fanout.

fato_item_venda: grão order_id + order_item_id; junta itens, pedidos, clientes,
produtos e tradução por relações muitos-para-um e deriva mes da data de compra.
mart_vendas_mensais: grão mes + estado_cliente + categoria, somente com medidas
aditivas (receita_produtos, frete, itens). Pedidos e ticket não ficam no mart:
são calculados na fato com count(distinct order_id) no grão de cada consulta.
Pagamentos e avaliações não entram na fato; o script só mede o fanout que o join
direto provocaria e mostra que a pré-agregação o elimina.

Grava as tabelas em saida/olist.duckdb, saida/testes_mart.json e
saida/plano_duckdb_estado.txt (EXPLAIN ANALYZE). Falha em qualquer teste.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent.parent
DUCK = BASE / "saida" / "olist.duckdb"
DESTINO = BASE / "saida" / "testes_mart.json"
PLANO = BASE / "saida" / "plano_duckdb_estado.txt"
SEM_CATEGORIA = "(sem categoria)"
DEC = "DECIMAL(18,2)"

SQL_FATO = f"""
CREATE OR REPLACE TABLE fato_item_venda AS
SELECT
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    o.customer_id,
    c.customer_unique_id,
    o.order_status,
    o.order_purchase_timestamp                                   AS data_compra,
    CAST(date_trunc('month', o.order_purchase_timestamp) AS DATE) AS mes,
    c.customer_state                                             AS estado_cliente,
    c.customer_city                                              AS cidade_cliente,
    p.product_category_name                                      AS categoria_original,
    t.product_category_name_english                              AS categoria_ingles,
    coalesce(p.product_category_name, '{SEM_CATEGORIA}')         AS categoria,
    i.price,
    i.freight_value
FROM olist_order_items AS i
LEFT JOIN olist_orders    AS o ON o.order_id    = i.order_id
LEFT JOIN olist_customers AS c ON c.customer_id = o.customer_id
LEFT JOIN olist_products  AS p ON p.product_id  = i.product_id
LEFT JOIN product_category_name_translation AS t
       ON t.product_category_name = p.product_category_name
"""

SQL_MART = f"""
CREATE OR REPLACE TABLE mart_vendas_mensais AS
SELECT
    mes,
    estado_cliente,
    categoria,
    sum(CAST(price AS {DEC}))         AS receita_produtos,
    sum(CAST(freight_value AS {DEC})) AS frete,
    count(*)                          AS itens
FROM fato_item_venda
GROUP BY mes, estado_cliente, categoria
"""

SQL_PLANO = """
EXPLAIN ANALYZE
SELECT estado_cliente, sum(receita_produtos) AS receita
FROM mart_vendas_mensais
GROUP BY estado_cliente
ORDER BY receita DESC
"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    inicio = time.perf_counter()
    con = duckdb.connect(str(DUCK))
    um = lambda sql: con.execute(sql).fetchone()
    testes, falhas = [], []

    def teste(nome, obtido, esperado, detalhe=""):
        ok = obtido == esperado
        testes.append({"teste": nome, "obtido": obtido, "esperado": esperado, "passou": ok, "detalhe": detalhe})
        if not ok:
            falhas.append(f"{nome}: obtido {obtido}, esperado {esperado}")
        print(f"  [{'ok' if ok else 'FALHA'}] {nome}: {obtido}", flush=True)

    t0 = time.perf_counter()
    con.execute(SQL_FATO)
    seg_fato = round(time.perf_counter() - t0, 3)
    t0 = time.perf_counter()
    con.execute(SQL_MART)
    seg_mart = round(time.perf_counter() - t0, 3)
    con.execute("ANALYZE")

    # Valores com mais de duas casas tornariam a soma decimal diferente da original.
    precos_fora = um("SELECT count(*) FROM olist_order_items WHERE round(price, 2) <> price "
                     "OR round(freight_value, 2) <> freight_value")[0]
    teste("price e freight_value com no máximo 2 casas", precos_fora, 0,
          "condição para reconciliar somas em DECIMAL(18,2) sem arredondar")

    itens = um("SELECT count(*) FROM olist_order_items")[0]
    linhas_fato, chaves_fato = um(
        "SELECT count(*), count(DISTINCT (order_id, order_item_id)) FROM fato_item_venda")
    teste("fanout: linhas da fato = linhas de olist_order_items", linhas_fato, itens)
    teste("unicidade de order_id + order_item_id na fato", chaves_fato, linhas_fato)

    sem_pedido, sem_cliente, sem_produto, sem_mes = um("""
        SELECT count(*) FILTER (WHERE customer_id IS NULL), count(*) FILTER (WHERE estado_cliente IS NULL),
               count(*) FILTER (WHERE categoria IS NULL), count(*) FILTER (WHERE mes IS NULL)
        FROM fato_item_venda""")
    teste("itens sem pedido correspondente", sem_pedido, 0)
    teste("itens sem cliente/estado", sem_cliente, 0)
    teste("itens com categoria nula depois do rótulo", sem_produto, 0,
          f"produto sem categoria recebe o rótulo '{SEM_CATEGORIA}' e continua visível")
    teste("itens sem mês", sem_mes, 0)

    soma_itens = um(f"SELECT sum(CAST(price AS {DEC})), sum(CAST(freight_value AS {DEC})) FROM olist_order_items")
    soma_fato = um(f"SELECT sum(CAST(price AS {DEC})), sum(CAST(freight_value AS {DEC})) FROM fato_item_venda")
    soma_mart = um("SELECT sum(receita_produtos), sum(frete), sum(itens) FROM mart_vendas_mensais")
    teste("sum(price) antes dos joins = depois (fato)", str(soma_fato[0]), str(soma_itens[0]))
    teste("sum(price) da fato = sum(receita_produtos) do mart", str(soma_mart[0]), str(soma_fato[0]))
    teste("sum(freight_value) da fato = sum(frete) do mart", str(soma_mart[1]), str(soma_fato[1]))
    teste("sum(itens) do mart = linhas da fato", int(soma_mart[2]), linhas_fato)
    soma_double = um("SELECT round(sum(price), 2) FROM olist_order_items")[0]
    teste("sum(price) em DOUBLE arredondada = soma DECIMAL", f"{soma_double:.2f}", str(soma_itens[0]))

    linhas_mart, chaves_mart = um(
        "SELECT count(*), count(DISTINCT (mes, estado_cliente, categoria)) FROM mart_vendas_mensais")
    teste("unicidade de mes + estado_cliente + categoria no mart", chaves_mart, linhas_mart)
    colunas_mart = [r[0] for r in con.execute("DESCRIBE mart_vendas_mensais").fetchall()]
    teste("colunas do mart (somente dimensões e medidas aditivas)", colunas_mart,
          ["mes", "estado_cliente", "categoria", "receita_produtos", "frete", "itens"])
    proibidas = [c for c in colunas_mart if any(p in c.lower() for p in ("pedido", "ticket", "order"))]
    teste("mart não armazena pedidos distintos nem ticket", proibidas, [])

    # Não aditividade: somar pedidos distintos por categoria conta o mesmo pedido mais de uma vez.
    pedidos_total = um("SELECT count(DISTINCT order_id) FROM fato_item_venda")[0]
    soma_por_categoria = um("""SELECT sum(n) FROM (SELECT categoria, count(DISTINCT order_id) AS n
                                FROM fato_item_venda GROUP BY categoria)""")[0]
    pedidos_multicategoria = um("""SELECT count(*) FROM (SELECT order_id FROM fato_item_venda
                                   GROUP BY order_id HAVING count(DISTINCT categoria) > 1)""")[0]

    # Fanout que o join direto com pagamentos/avaliações provocaria (medido, não usado).
    join_pag = um(f"""SELECT count(*), sum(CAST(i.price AS {DEC})) FROM olist_order_items i
                      JOIN olist_order_payments p ON p.order_id = i.order_id""")
    pag_preagregado = um(f"""
        WITH pag AS (SELECT order_id, sum(payment_value) AS pagamento, count(*) AS parcelas_registro
                     FROM olist_order_payments GROUP BY order_id)
        SELECT count(*), sum(CAST(f.price AS {DEC})) FROM fato_item_venda f LEFT JOIN pag USING (order_id)""")
    teste("join com pagamentos pré-agregados por pedido mantém o grão", pag_preagregado[0], linhas_fato)
    teste("join com pagamentos pré-agregados mantém sum(price)", str(pag_preagregado[1]), str(soma_fato[0]))
    join_rev = um("""SELECT count(*) FROM olist_order_items i JOIN olist_order_reviews r ON r.order_id = i.order_id""")
    pedidos_varias_avaliacoes = um("""SELECT count(*) FROM (SELECT order_id FROM olist_order_reviews
                                      GROUP BY order_id HAVING count(*) > 1)""")[0]

    categorias = um("SELECT count(DISTINCT categoria) FROM fato_item_venda")[0]
    sem_traducao = con.execute("""
        SELECT categoria, count(*) AS itens FROM fato_item_venda
        WHERE categoria_original IS NOT NULL AND categoria_ingles IS NULL
        GROUP BY categoria ORDER BY itens DESC""").fetchall()
    itens_sem_categoria = um(f"SELECT count(*) FROM fato_item_venda WHERE categoria = '{SEM_CATEGORIA}'")[0]
    meses = um("SELECT min(mes), max(mes), count(DISTINCT mes) FROM fato_item_venda")
    status = con.execute("SELECT order_status, count(*) FROM fato_item_venda GROUP BY 1 ORDER BY 2 DESC").fetchall()

    plano = con.execute(SQL_PLANO).fetchall()
    PLANO.write_text("-- " + " ".join(SQL_PLANO.split()) + "\n\n" + "\n".join(str(r[-1]) for r in plano),
                     encoding="utf-8")
    con.close()

    rel = {
        "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "script": "src/04_criar_mart_olap.py",
        "banco": "saida/olist.duckdb",
        "sql_fato": " ".join(SQL_FATO.split()),
        "sql_mart": " ".join(SQL_MART.split()),
        "grao_fato": ["order_id", "order_item_id"],
        "grao_mart": ["mes", "estado_cliente", "categoria"],
        "linhas_fato": linhas_fato,
        "linhas_mart": linhas_mart,
        "soma_price_itens": str(soma_itens[0]),
        "soma_price_fato": str(soma_fato[0]),
        "soma_receita_mart": str(soma_mart[0]),
        "soma_frete_mart": str(soma_mart[1]),
        "nao_aditividade": {
            "pedidos_distintos_total": pedidos_total,
            "soma_de_pedidos_distintos_por_categoria": int(soma_por_categoria),
            "pedidos_com_mais_de_uma_categoria": pedidos_multicategoria,
        },
        "fanout_evitado": {
            "linhas_join_direto_itens_pagamentos": join_pag[0],
            "soma_price_join_direto_itens_pagamentos": str(join_pag[1]),
            "linhas_join_direto_itens_avaliacoes": join_rev[0],
            "pedidos_com_mais_de_uma_avaliacao": pedidos_varias_avaliacoes,
            "linhas_fato_com_pagamentos_pre_agregados": pag_preagregado[0],
        },
        "categorias_distintas_na_fato": categorias,
        "itens_sem_categoria": itens_sem_categoria,
        "categorias_sem_traducao": [{"categoria": c, "itens": n} for c, n in sem_traducao],
        "periodo_mes": {"primeiro": str(meses[0]), "ultimo": str(meses[1]), "meses_distintos": meses[2]},
        "itens_por_status_do_pedido": [{"status": s, "itens": n} for s, n in status],
        "plano_explain_analyze": "saida/plano_duckdb_estado.txt",
        "segundos": {"fato": seg_fato, "mart": seg_mart, "total": round(time.perf_counter() - inicio, 3)},
        "testes": testes,
        "gate": {"falhas": falhas, "passou": not falhas},
    }
    DESTINO.write_text(json.dumps(rel, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"gravado {DESTINO.relative_to(BASE)} e {PLANO.relative_to(BASE)}")
    if falhas:
        for f in falhas:
            print("FALHA:", f)
        raise SystemExit(1)
    print("GATE E PASSOU")


if __name__ == "__main__":
    main()
