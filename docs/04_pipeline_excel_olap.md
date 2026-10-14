# 04 — Pipeline do Excel ao OLAP com SQLite e DuckDB

> Registro da Aula 04 (laboratório "do Excel ao OLAP com SQLite, DuckDB e IA").
> **Executado em 13/10/2026, depois da correção do professor de 10/10/2026 (issue #1)**, que apontou a
> falta do registro da Aula 04. A aula foi em 05/09/2026; o laboratório não foi feito naquela data e este
> documento não finge que foi.
>
> O código dos scripts foi escrito com assistência de IA (Claude Code), não com o OpenCode Zen proposto no
> roteiro. O grupo responde pela execução, pelos gates e por este texto. Todos os números abaixo foram
> copiados dos arquivos que os scripts gravaram em `aula04_excel_olap/saida/` na reconstrução completa de
> 13/10/2026 (`perfil_excel.json` gravado às 21:15:14 e `medicoes_tempo.json` às 21:17:24, horário de
> Brasília). Os únicos valores que não vêm de `saida/` são os SHA256 do manifesto e do `SHA256SUMS`,
> calculados com `sha256sum`. Nada foi digitado à mão nos HTMLs.

Pasta do laboratório: [`aula04_excel_olap/`](../aula04_excel_olap/README.md).

| Etapa | Script | Evidência gravada |
| --- | --- | --- |
| A. Perfil dos Excels | `src/00_perfil_excel.py` | `saida/perfil_excel.json` |
| B. Excel para SQLite | `src/01_excel_para_sqlite.py` | `saida/olist.sqlite`, `saida/carga_sqlite.json` |
| C. HTML lido do SQLite | `src/02_html_sqlite.py` | `saida/relatorio_sqlite.html` |
| D. SQLite para DuckDB | `src/03_sqlite_para_duckdb.py` | `saida/olist.duckdb`, `saida/reconciliacao_duckdb.json` |
| E. Mart OLAP | `src/04_criar_mart_olap.py` | `saida/testes_mart.json`, `saida/plano_duckdb_estado.txt` |
| F. HTML lido do DuckDB | `src/05_html_duckdb.py` | `saida/dashboard_duckdb.html` |
| Consulta comparada | `src/06_comparar_sqlite_duckdb.py` | `saida/medicoes_tempo.json` |

Os logs de terminal de cada script estão em `saida/logs/`.

## 1. Proveniência

Os quatro Excels e o contrato vieram do repositório público da disciplina
(`afonsolelis/aulas_mackenzie`, pasta `aulas/data_visualization/aula_04_do_excel_ao_olap_com_sqlite_duckdb_e_ia/dados/`),
baixados de `https://raw.githubusercontent.com/afonsolelis/aulas_mackenzie/HEAD/aulas/data_visualization/aula_04_do_excel_ao_olap_com_sqlite_duckdb_e_ia/dados/<arquivo>`.
Nenhum deles veio como ponteiro Git LFS; os quatro chegaram como planilhas `.xlsx` de verdade.

A fonte original é o *Brazilian E-Commerce Public Dataset by Olist* (Kaggle, 2018), licença CC BY-NC-SA 4.0.
Segundo o README dos dados (copiado em `aula04_excel_olap/contrato/README_dados_professor.md`), a cópia da
aula foi exportada em 29/08/2026 do banco `olist` da disciplina. O manifesto declara `"generated_on": "2026-08-29"`.

| Arquivo | Bytes | SHA256 (lido pelo script 00) | Confere com manifesto e `SHA256SUMS` |
| --- | ---: | --- | --- |
| `olist_pedidos_clientes.xlsx` | 21.771.168 | `14cd1619a42622ac95dafadb846e4a1e720bb0fd48e9c89e2274a497e51ae16d` | sim |
| `olist_itens_pagamentos_avaliacoes.xlsx` | 27.344.755 | `09bd9e6ab018159a397be00e9508d2ac7bd50362ec33e69bf47c5b5b289aa816` | sim |
| `olist_catalogo.xlsx` | 2.762.708 | `66fef4320d2a3283da6844477867878d442caec9e5d3f4e090cbbad07ca4cf70` | sim |
| `olist_geolocalizacao.xlsx` | 31.279.540 | `a18970cbc82583a2e6194f1e934831fca8e8c06bec2546f99599c0783f8dafa2` | sim |

Arquivos de contrato guardados em `aula04_excel_olap/contrato/`: `manifesto_olist.json`
(SHA256 `d0e930f1b0a97567af5aabcdc6fa26bd501916564f99f580634d3059978ca0b6`) e `SHA256SUMS`
(SHA256 `339f0b5af0fe7480a5efd248696df5b62622e4ecde200253a79b3889249e1cbc`). O `requirements.txt` do
laboratório (`duckdb==1.5.5`, `openpyxl==3.1.5`) foi copiado sem mudança.

**Entrada imutável.** Os Excels ficam em `aula04_excel_olap/entrada/`, marcados como somente leitura. O
script 01 calcula o SHA256 dos quatro arquivos antes e depois da carga; os dois conjuntos são iguais aos
valores da tabela acima (`"entrada_intacta": true` em `carga_sqlite.json`).

## 2. Gate A — perfil dos Excels

Leitura com `openpyxl` em `read_only=True`, linha a linha (`iter_rows(values_only=True)`), sem montar a aba em
memória e sem pandas. O script também confere o SHA256, os cabeçalhos (sem vazio nem repetição) e a presença
das colunas da chave candidata.

Resultado: **passou** — 4 arquivos, 9 abas, 9 de 9 contagens iguais ao manifesto. Tempo total: 68,708 s.

| Tabela (aba) | Arquivo | Linhas de dados | Manifesto |
| --- | --- | ---: | ---: |
| `olist_orders` | `olist_pedidos_clientes.xlsx` | 99.441 | 99.441 |
| `olist_customers` | `olist_pedidos_clientes.xlsx` | 99.441 | 99.441 |
| `olist_order_items` | `olist_itens_pagamentos_avaliacoes.xlsx` | 112.650 | 112.650 |
| `olist_order_payments` | `olist_itens_pagamentos_avaliacoes.xlsx` | 103.886 | 103.886 |
| `olist_order_reviews` | `olist_itens_pagamentos_avaliacoes.xlsx` | 99.224 | 99.224 |
| `olist_products` | `olist_catalogo.xlsx` | 32.951 | 32.951 |
| `olist_sellers` | `olist_catalogo.xlsx` | 3.095 | 3.095 |
| `product_category_name_translation` (aba `product_category_name_translati`) | `olist_catalogo.xlsx` | 71 | 71 |
| `olist_geolocation` | `olist_geolocalizacao.xlsx` | 1.000.163 | 1.000.163 |

Achados do perfil que mudaram o código:

- O Excel limita nome de aba a 31 caracteres. A tabela `product_category_name_translation` está na aba
  `product_category_name_translati`; os scripts localizam a aba pelo nome da tabela e, se não acharem, pelo
  nome cortado em 31 caracteres.
- Em `read_only`, o openpyxl não devolve as células vazias do fim da linha. Em `olist_products` faltaram 12
  células desse tipo; os scripts completam a linha com nulo. Nenhuma aba tem célula preenchida fora do
  cabeçalho.
- As datas chegam como texto `AAAA-MM-DD HH:MM:SS`. `price`, `freight_value` e `payment_value` misturam
  `int` e `float` (valores inteiros vêm como `int`).
- Algumas colunas de texto têm células gravadas como número no Excel: 316 em `review_comment_title`, 28 em
  `review_comment_message` e 1 em `seller_city`.

## 3. Gate B — carga no SQLite

Esquema explícito para as nove tabelas (o DDL completo está em `carga_sqlite.json`, chave `ddl`):
identificadores e categorias em `TEXT`; contagens, dimensões e prefixos de CEP em `INTEGER`; valores e
coordenadas em `REAL`; datas em `TEXT` no formato ISO 8601 `AAAA-MM-DDTHH:MM:SS`. Chave primária nas chaves
candidatas do manifesto; `olist_geolocation` fica sem chave, porque o prefixo de CEP se repete.

Parâmetros: `PRAGMA foreign_keys = ON` (conferido depois de ligado), pais antes de filhos (clientes,
vendedores, produtos, tradução, geolocalização, pedidos, itens, pagamentos, avaliações), uma transação por
aba, `executemany` em lotes de 5.000 linhas, nove índices e `ANALYZE` depois da carga (1,158 s). Nulos
preservados: célula vazia vira `NULL`, nunca texto vazio ou zero.

Resultado: **passou**. Tempo total: 116,162 s. Banco: `saida/olist.sqlite`, 176.566.272 bytes.

| Tabela | Linhas no SQLite | Manifesto | Chave candidata | Chaves distintas | Lotes | Carga (s) |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `olist_customers` | 99.441 | 99.441 | `customer_id` | 99.441 | 20 | 13,026 |
| `olist_sellers` | 3.095 | 3.095 | `seller_id` | 3.095 | 1 | 1,169 |
| `olist_products` | 32.951 | 32.951 | `product_id` | 32.951 | 7 | 2,477 |
| `product_category_name_translation` | 71 | 71 | `product_category_name` | 71 | 1 | 1,021 |
| `olist_geolocation` | 1.000.163 | 1.000.163 | (sem chave) | — | 201 | 30,606 |
| `olist_orders` | 99.441 | 99.441 | `order_id` | 99.441 | 20 | 15,784 |
| `olist_order_items` | 112.650 | 112.650 | `order_id + order_item_id` | 112.650 | 23 | 16,494 |
| `olist_order_payments` | 103.886 | 103.886 | `order_id + payment_sequential` | 103.886 | 21 | 14,185 |
| `olist_order_reviews` | 99.224 | 99.224 | `review_id + order_id` | 99.224 | 20 | 15,288 |

- Tabelas no banco: 9.
- `PRAGMA integrity_check`: `ok`.
- `PRAGMA foreign_key_check`: 0 linhas.

### Chaves estrangeiras

As seis relações do roteiro foram declaradas no `CREATE TABLE` e lidas de volta com `PRAGMA foreign_key_list`
(6 FKs). Além do `foreign_key_check`, o script conta, para cada relação, as linhas filhas sem pai por
`LEFT JOIN`:

| Relação | Linhas órfãs |
| --- | ---: |
| `olist_orders.customer_id → olist_customers.customer_id` | 0 |
| `olist_order_items.order_id → olist_orders.order_id` | 0 |
| `olist_order_items.product_id → olist_products.product_id` | 0 |
| `olist_order_items.seller_id → olist_sellers.seller_id` | 0 |
| `olist_order_payments.order_id → olist_orders.order_id` | 0 |
| `olist_order_reviews.order_id → olist_orders.order_id` | 0 |

Nenhuma FK falhou com os dados reais da fonte, então não houve linha descartada nem decisão de exceção. A
geolocalização não recebeu FK, como pede o roteiro.

### Nulos e conversões

Os nulos de cada coluna no SQLite são comparados com os nulos contados no perfil do Excel; todos conferem.

| Coluna | Nulos no Excel | Nulos no SQLite |
| --- | ---: | ---: |
| `olist_products.product_category_name` | 610 | 610 |
| `olist_products.product_name_lenght`, `product_description_lenght`, `product_photos_qty` | 610 cada | 610 cada |
| `olist_products.product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm` | 2 cada | 2 cada |
| `olist_orders.order_approved_at` | 160 | 160 |
| `olist_orders.order_delivered_carrier_date` | 1.783 | 1.783 |
| `olist_orders.order_delivered_customer_date` | 2.965 | 2.965 |
| `olist_order_reviews.review_comment_title` | 87.656 | 87.656 |
| `olist_order_reviews.review_comment_message` | 58.247 | 58.247 |

Conversões registradas pela carga: 492.297 datas normalizadas em `olist_orders`, 112.650 em
`olist_order_items` e 198.448 em `olist_order_reviews`; 344 números convertidos para texto em
`olist_order_reviews` e 1 em `olist_sellers`. Nenhum valor ficou fora do tipo declarado (o script pararia
com erro de conversão).

## 4. Gate C — HTML lido do SQLite

`saida/relatorio_sqlite.html` abre `olist.sqlite` com URI `mode=ro`, declara a fonte (`saida/olist.sqlite`) e a
data de geração (2026-10-13T21:17:15-03:00), escapa todo texto e mostra: contagem das nove tabelas, as seis
relações declaradas, o resultado do `integrity_check` e do `foreign_key_check`, pedidos por status com
percentual calculado no banco por janela, os cinco pedidos mais recentes e a duração de cada consulta.

Conferência com o terminal: `SELECT count(*) FROM olist_orders` executado à parte devolveu 99441; o HTML
mostra `olist_orders` com 99.441. **Passou.**

Pedidos por status, como aparecem na página: delivered 96.478 (97,02%), shipped 1.107 (1,11%), canceled 625
(0,63%), unavailable 609 (0,61%), invoiced 314 (0,32%), processing 301 (0,30%), created 5 (0,01%) e
approved 2 (0,00%).

## 5. Gate D — SQLite para DuckDB

O script instala e carrega a extensão oficial `sqlite` do DuckDB (registrada no catálogo como
`sqlite_scanner`, versão `f79b1db`), anexa `olist.sqlite` como `sqlite_src` em modo somente leitura e cria as
nove tabelas no catálogo `main` com `CREATE OR REPLACE TABLE ... AS SELECT`. As colunas de data passam para
`TIMESTAMP` por `CAST` explícito; texto, inteiro e real viram `VARCHAR`, `BIGINT` e `DOUBLE`, e o script
confere esses tipos coluna a coluna. A extensão foi baixada da rede na primeira execução, no mesmo dia; na
execução registrada aqui ela já estava instalada.

Resultado: **passou** — 9 tabelas nativas (`BASE TABLE`), 9 de 9 contagens iguais, nulos das colunas
convertidas para `TIMESTAMP` iguais nos dois bancos (160, 1.783 e 2.965 nas três datas de `olist_orders` que
têm nulo; 0 nas demais). `ANALYZE` executado. Tempo total: 2,267 s; arquivo com as nove tabelas:
40.906.752 bytes.

| Tabela | SQLite | DuckDB |
| --- | ---: | ---: |
| `olist_customers` | 99.441 | 99.441 |
| `olist_geolocation` | 1.000.163 | 1.000.163 |
| `olist_order_items` | 112.650 | 112.650 |
| `olist_order_payments` | 103.886 | 103.886 |
| `olist_order_reviews` | 99.224 | 99.224 |
| `olist_orders` | 99.441 | 99.441 |
| `olist_products` | 32.951 | 32.951 |
| `olist_sellers` | 3.095 | 3.095 |
| `product_category_name_translation` | 71 | 71 |

## 6. Gate E — fato e mart sem fanout

`fato_item_venda`, no grão `order_id + order_item_id`, junta itens, pedidos, clientes, produtos e tradução
por relações muitos-para-um e deriva `mes` (primeiro dia do mês da compra). `mart_vendas_mensais`, no grão
`mes + estado_cliente + categoria`, guarda só `receita_produtos`, `frete` e `itens`. Pedidos e ticket não
ficam no mart. Pagamentos e avaliações não entram na fato.

Resultado: **passou** — 17 de 17 testes.

| Teste | Obtido |
| --- | --- |
| `price` e `freight_value` com no máximo 2 casas (linhas fora) | 0 |
| Linhas da fato = linhas de `olist_order_items` | 112.650 = 112.650 |
| Unicidade de `order_id + order_item_id` na fato | 112.650 chaves distintas |
| Itens sem pedido, sem cliente/estado, com categoria nula, sem mês | 0, 0, 0, 0 |
| `sum(price)` antes dos joins = depois (fato) | 13591643.70 = 13591643.70 |
| `sum(price)` da fato = `sum(receita_produtos)` do mart | 13591643.70 |
| `sum(freight_value)` da fato = `sum(frete)` do mart | 2251909.54 |
| `sum(itens)` do mart = linhas da fato | 112.650 |
| Soma em `DOUBLE` arredondada = soma em `DECIMAL(18,2)` | 13591643.70 |
| Unicidade de `mes + estado_cliente + categoria` no mart | 11.823 linhas, 11.823 chaves |
| Colunas do mart | `mes, estado_cliente, categoria, receita_produtos, frete, itens` |
| Colunas de pedido ou ticket no mart | nenhuma |
| Join com pagamentos pré-agregados por pedido | 112.650 linhas, `sum(price)` 13591643.70 |

O que o script mediu para justificar as regras (nada disso foi usado no painel):

- **Não aditividade de pedidos.** Há 98.666 pedidos distintos na fato; somar os pedidos distintos de cada
  categoria dá 99.470, porque 786 pedidos têm itens de mais de uma categoria.
- **Fanout evitado.** O join direto de itens com pagamentos gera 117.601 linhas e faria `sum(price)` chegar a
  14209115.34. O join direto de itens com avaliações gera 112.372 linhas, e 547 pedidos têm mais de uma
  avaliação. Com pagamentos pré-agregados por pedido, a fato continua com 112.650 linhas.
- **Categorias.** 74 categorias na fato, contando o rótulo `(sem categoria)`, que cobre 1.603 itens de
  produtos sem categoria. Duas categorias não têm tradução para o inglês: `portateis_cozinha_e_preparadores_de_alimentos`
  (15 itens) e `pc_gamer` (9 itens). O painel usa o nome original em português, então nenhuma some.
- **Período.** De 2016-09 a 2018-09, com 24 meses distintos que têm compra.
- **Plano.** `EXPLAIN ANALYZE` da consulta de receita por estado sobre o mart está em
  `saida/plano_duckdb_estado.txt` (tempo total informado pelo DuckDB: 0.0037s; 27 linhas no resultado).

Tempos: fato 0,531 s, mart 0,023 s, script inteiro 0,914 s.

## 7. Gate F — painel lido do DuckDB

`saida/dashboard_duckdb.html` abre só `olist.duckdb`, em modo somente leitura (o script não importa
`sqlite3`), declara a fonte e a data de geração (2026-10-13T21:17:19-03:00) e calcula pedidos e ticket na
fato com `count(DISTINCT order_id)` no grão de cada consulta. Mostra:

- **KPIs:** receita de produtos R$ 13.591.643,70; pedidos 98.666; ticket médio de produtos R$ 137,75; itens
  112.650; frete R$ 2.251.909,54 (fora da receita). Inclui itens dos 7 status de pedido; a composição por
  status está na página.
- **Série mensal** de receita e de pedidos, em dois gráficos separados (escalas diferentes não dividem eixo),
  com tabela equivalente. O calendário vai de 2016-09 a 2018-09; 2016-11 não tem nenhuma compra e aparece com
  zero, sem estimativa. Os meses 2016-09, 2016-12 e 2018-09 têm menos de 1% dos pedidos do maior mês e estão
  marcados como parciais.
- **Top 10 categorias com cobertura:** as 10 maiores, entre 74, cobrem 62,36% da receita; as outras 64
  categorias somam R$ 5.115.686,14, ou 37,64%, e aparecem numa linha "outras" na tabela. A página explica por
  que a soma dos pedidos por categoria (99.470) passa do total (98.666).
- **Estados** com receita, participação, pedidos, ticket e frete (27 UFs; SP lidera com R$ 5.202.955,05,
  38,28% da receita e 41.375 pedidos).
- **Reconciliação** calculada na própria página: receita do KPI = soma do mart = soma por estado = soma
  mensal = top 10 + outros (R$ 13.591.643,70 em todos); itens da fato = itens do mart (112.650); pedidos do
  KPI = pedidos distintos em `olist_order_items` = soma por estado = soma por mês (98.666). Todas conferem.
- **Consultas executadas**, com duração e SQL resumido.

Resultado: **passou**. Os dois HTMLs não carregam nada da rede: CSS e o pequeno script de dica estão
embutidos, as fontes são as do sistema e não há CDN nem Google Fonts.

## 8. Consulta comparada SQLite × DuckDB

Mesma pergunta nos dois bancos: receita (em centavos inteiros), pedidos distintos e itens por mês da compra,
juntando `olist_order_items` e `olist_orders`. No DuckDB a consulta lê as tabelas nativas copiadas do
SQLite, não o mart, para que o trabalho seja equivalente. Os dois resultados são **iguais linha a linha**:
24 meses, 1359164370 centavos, 98.666 pedidos e 112.650 itens somados.

Máquina: Windows 11 (`Windows-11-10.0.26300-SP0`, AMD64), Intel Core i9-9900K @ 3.60GHz, 16 núcleos lógicos,
31,8 GiB de memória; Python 3.13.15, SQLite 3.50.4, DuckDB 1.5.5 (16 threads; o SQLite usa uma).

Protocolo: cinco execuções de cada tipo, mediana, relógio `time.perf_counter`. **Fria:** um processo Python
novo por execução, que abre a conexão e roda a consulta uma vez (o tempo de abrir a conexão é medido à
parte). **Aquecida:** uma conexão, uma execução descartada e cinco medidas. O cache de arquivos do Windows
não foi esvaziado: "fria" quer dizer processo e conexão novos, não disco frio.

| Banco | Fria: mediana (mín.–máx.) | Aquecida: mediana (mín.–máx.) | Abrir conexão (mediana) | Execução descartada |
| --- | ---: | ---: | ---: | ---: |
| SQLite | 185,936 ms (184,213–193,195) | 180,567 ms (179,123–207,427) | 0,449 ms | 187,777 ms |
| DuckDB | 62,925 ms (61,880–63,948) | 60,881 ms (59,159–68,394) | 15,509 ms | 67,946 ms |

Leitura: nesta máquina, nesta consulta e nesta execução, o DuckDB respondeu a agregação mensal com mediana
perto de um terço da do SQLite, e abrir a conexão custou mais no DuckDB. Nos dois bancos as faixas da
execução fria e da aquecida se sobrepõem, então a diferença entre fria e aquecida fica dentro da variação
observada. **Esse resultado descreve este caso e não prova superioridade universal de um mecanismo:** o
DuckDB usou 16 threads contra uma do SQLite, o SQLite não tem índice pensado para essa agregação, o cache do
sistema operacional estava quente e o volume é pequeno.

## 9. Desvios do roteiro e por quê

- **Ferramenta de IA.** O roteiro usa OpenCode Zen; aqui o código foi escrito com Claude Code e executado no
  terminal local. O protocolo de controle foi o mesmo: uma etapa por vez, execução e gate antes da próxima.
- **Ambiente.** Windows 11 local em vez de GitHub Codespaces; venv em `aula04_excel_olap/.venv`; comandos em
  PowerShell (ver o README da pasta). O cliente `sqlite3` de linha de comando não está instalado nesta
  máquina; `.tables`, `integrity_check` e `foreign_key_check` foram conferidos pelo módulo `sqlite3` do
  Python, com os mesmos PRAGMAs, dentro dos scripts 01 e 02.
- **Sétimo script.** O roteiro lista seis scripts, mas pede a consulta comparada com cinco execuções e
  mediana. Ela ficou em `src/06_comparar_sqlite_duckdb.py`, que grava `saida/medicoes_tempo.json`.
- **Contrato fora de `../dados/`.** O manifesto e o `SHA256SUMS` ficam em `aula04_excel_olap/contrato/`.
- **Transação por aba.** O README do laboratório pede transação por aba e o material fala em transação por
  arquivo; segui o README.
- **Arquivos extras de evidência.** `carga_sqlite.json`, `testes_mart.json`, `plano_duckdb_estado.txt` e os
  logs em `saida/logs/` não estão na árvore do roteiro; foram gravados para que este registro tenha fonte.
- **Datas.** No SQLite ficam como texto ISO 8601 com `T` entre data e hora; no DuckDB viram `TIMESTAMP`.
- **Medidas do mart em `DECIMAL(18,2)`.** Permite que as somas reconciliem exatamente (fato, mart, estados,
  meses, top 10 + outros), sem diferença de arredondamento de ponto flutuante.

## 10. Limitações

- Um dataset público, um espelho educacional dele, uma máquina e uma execução registrada. Os tempos mudam
  com outra máquina, outra versão ou outro estado de cache.
- Receita é a soma de `price` dos itens: sem frete, sem pagamentos, sem descontos. A fato inclui itens de
  pedidos em todos os status, inclusive cancelados (542 itens de 461 pedidos cancelados, conforme a página).
- Pedidos sem nenhum item não entram na fato: `olist_orders` tem 99.441 pedidos e a fato tem 98.666 pedidos
  distintos.
- O mês é o da data de compra. As pontas da série têm poucos pedidos e não devem ser lidas como tendência.
- Células de texto que o Excel guardou como número (344 em avaliações, 1 em vendedores) voltaram para texto,
  mas zeros à esquerda que o Excel tenha descartado não podem ser recuperados a partir dos `.xlsx`. Na
  inspeção manual, o único `seller_city` numérico tem sete dígitos e parece um CEP digitado no lugar da cidade.
- A geolocalização foi carregada e reconciliada, mas não foi usada no mart nem nos painéis.

## 11. Caminhos dos dois HTMLs

- [`aula04_excel_olap/saida/relatorio_sqlite.html`](../aula04_excel_olap/saida/relatorio_sqlite.html) — inventário operacional lido do SQLite.
- [`aula04_excel_olap/saida/dashboard_duckdb.html`](../aula04_excel_olap/saida/dashboard_duckdb.html) — painel analítico lido do DuckDB.

Abrem direto do disco ou com `.venv\Scripts\python.exe -m http.server 8000 -d saida`.

## 12. Como reconstruir

Os Excels (`entrada/`), os bancos (`*.sqlite`, `*.duckdb`) e o venv (`.venv/`) não vão para o git; estão no
`.gitignore` da pasta. Tudo em `saida/` se reconstrói a partir dos quatro Excels:

1. Criar o venv com Python 3.13 e instalar `requirements.txt`.
2. Baixar os quatro `.xlsx` para `entrada/` e conferir o SHA256 com `contrato/SHA256SUMS`.
3. Apagar `saida/` e rodar, em ordem, `00` a `06` com `.venv\Scripts\python.exe -I src\<script>.py`. Cada
   script sai com código 1 se o gate dele falhar.

Os comandos completos estão em [`aula04_excel_olap/README.md`](../aula04_excel_olap/README.md). A execução
registrada aqui foi uma reconstrução completa, com `saida/` apagada antes de rodar o script 00; somando os
tempos gravados, a leitura dos Excels (68,708 s no perfil e 116,162 s na carga) responde por quase todo o
tempo do pipeline.
