# sqlite/

Os 8 CSVs de [csvs_originais/](../csvs_originais/) carregados em um banco SQLite unico.

| arquivo | o que e |
|---|---|
| `dados.db` | o banco gerado — 8 tabelas, 17.773 linhas, 5 views de apoio; T05 cria uma view tratada |
| `csv_para_sqlite.py` | gera `dados.db` do zero a partir dos CSVs |
| `verificar.py` | confere que o banco reproduz os CSVs linha a linha |
| `rodar_sql.py` | roda os `.sql` desta pasta e grava cada resultado em `.csv` ao lado |
| `t04_cadencia_commits_diaria.sql` | R01 — commits por grupo e dia, com os dias sem commit como zero |
| `Detalhamento_dos_commits.sql` | R01 — commits de um grupo num dia (o clique no gráfico) |
| `r02_acumulo_por_etapa.sql` | R02 — cartões e horas por etapa do quadro, por grupo e sprint |
| `r02_cartoes_da_etapa.sql` | R02 — cartões de uma etapa (abrir a de maior acúmulo); parâmetros no CTE `parametros`, `'*'` = todos |
| `r03_cobertura_registro.sql` | R03 — percentual de preenchimento por campo e grupo, inclusive tamanho do cartão e `#N` no commit |
| `r04_prazo_planejado_realizado.sql` | R04 — um cartão fechado com tamanho por linha: dias planejados, dias realizados, commits ligados |
| `r04_commits_por_cartao.sql` | R04 — um vínculo commit → cartão por linha (o clique no gráfico) |
| `r04_resumo_por_tamanho.sql` | R04 — por grupo e tamanho: medianas, % acima do planejado, commits por cartão |
| `r05_contribuicao_por_integrante.sql` | R05 — valor de cada integrante por grupo, sprint e medida, com a parcela sem dono |
| `r05_gini_concentracao.sql` | R05 — índice de Gini por grupo, sprint e medida |
| `r06_cartoes_por_eixo.sql` | R06 — um cartão por linha, com o eixo de tarefa (Código, Design, Documentação, Negócio) e o responsável |
| `r06_eixo_por_integrante.sql` | R06 — parte de cada eixo nos cartões de cada integrante, por grupo e sprint, com o perfil do grupo |
| `t05_eventos_kanban.sql` | T05 — view deduplicada, classificada e sequenciada dos eventos Kanban |

```
py -3 sqlite/csv_para_sqlite.py    # reconstroi dados.db
py -3 sqlite/verificar.py          # confere
py -3 sqlite/rodar_sql.py t05_eventos_kanban.sql  # cria a view e exporta CSV
```

## Os CSVs nao sao tocados

Os arquivos de `csvs_originais/` sao abertos somente para leitura. Nenhum e
reescrito, movido ou renomeado — o banco e sempre um artefato derivado,
descartavel e reconstruivel. O executor usa modo gravavel somente para scripts
`DROP VIEW`/`CREATE VIEW`; consultas analiticas seguem em modo somente leitura.

## O que a carga faz

Uma tabela por CSV, com o mesmo nome do arquivo, as mesmas colunas e a mesma
ordem — mais `evento_id` em `kanban_eventos` (ver [Chaves primarias](#chaves-primarias)).
Nenhuma linha e filtrada ou deduplicada: as 24 duplicatas de
`kanban_eventos` e os 213 commits herdados do repositorio-template continuam
aqui. A modelagem dimensional de [modelagem/schema.sql](../modelagem/schema.sql)
e uma camada seguinte, que consome estas tabelas.

Duas regras dos R04 e R05 aparecem em mais de um `.sql`, copiadas de propósito
para cada arquivo rodar sozinho (o padrão do R02): o **tamanho do cartão** (token
exato `PP`/`SIZE_PP` ... `GG`/`SIZE_GG`; `P1`–`P8` são prioridade) e o **vínculo
commit → cartão** (`#N` no título, ou na mensagem quando o título não cita número,
com N no mesmo grupo). O SQLite não tem regex: o número é lido cortando o texto
em cada `#` e usando `CAST(trecho AS INTEGER)`, que para no primeiro não-dígito.
Os geradores de `dashboard/` recontam as duas regras em Python e param se o
resultado divergir.

A view T05 expoe chaves naturais (grupo/cartao, pessoa, coluna e rotulo) para a
carga dimensional resolver as SKs. As dimensoes modeladas nao existem em
`dados.db`; portanto, a view nao inventa chaves substitutas.

| tabela | linhas |
|---|---|
| `cartoes` | 1.238 |
| `commits` | 2.688 |
| `grupos` | 3 |
| `kanban_eventos` | 13.194 |
| `merge_requests` | 540 |
| `pessoas` | 83 |
| `quadro_colunas` | 12 |
| `sprints` | 15 |

## Datas: um fuso so, uma grafia so

Os CSVs trazem tres grafias de tempo: UTC com `Z` (grupos, cartoes, MRs,
kanban), offset `-03:00` ou `+00:00` (os dois campos de `commits`) e data pura
`AAAA-MM-DD` (prazos e sprints). Comparar essas grafias como texto da resultado
errado, e agrupar por dia sem converter joga 397 commits no dia vizinho.

A carga converte todo timestamp para o fuso unico do
[contrato de dados](../modelagem/Contrato_de_dados.md), **America/Sao_Paulo**, e
grava em ISO 8601 sem offset:

| tipo declarado | forma gravada | colunas |
|---|---|---|
| `DATETIME` | `2026-04-22T14:38:42.296` (hora de Brasilia) | `criado_em`, `atualizado_em`, `fechado_em`, `merged_em`, `ultima_atividade_em`, `ocorrido_em`, `autorado_em`, `commitado_em` |
| `DATE` | `2026-04-23` | `cartoes.prazo_em`, `sprints.inicio_em`, `sprints.prazo_em` |

Com uma grafia so, tudo funciona direto no SQLite:

```sql
-- filtro por periodo: comparacao de texto ja e comparacao de tempo
WHERE ocorrido_em >= '2026-05-01' AND ocorrido_em < '2026-06-01'

-- agrupamento diario e por hora, ja no dia/hora locais
GROUP BY date(autorado_em)
GROUP BY strftime('%H', autorado_em)

-- duracao em horas
(julianday(fechado_em) - julianday(criado_em)) * 24
```

O offset nao e gravado de proposito: com offset, `date()` do SQLite converte de
volta para UTC e o dia volta a sair errado. O instante nao se perde — o
`verificar.py` confere, valor a valor, que a hora local gravada e o mesmo
instante do CSV. Desde 2019 o Brasil nao tem horario de verao e o dado mais
antigo e de 2022, entao a hora local e continua, sem hora repetida.

## Chaves primarias

Cada tabela declara a chave do [contrato de dados](../modelagem/Contrato_de_dados.md#chaves-declaradas),
e o banco recusa um registro que a repita:

| tabela | chave primaria |
|---|---|
| `grupos` | `grupo` |
| `pessoas` | `pessoa_id` |
| `sprints` | `grupo`, `sprint` |
| `quadro_colunas` | `grupo`, `quadro`, `coluna` |
| `cartoes` | `grupo`, `cartao_numero` |
| `commits` | `grupo`, `commit_id` |
| `merge_requests` | `grupo`, `mr_numero` |
| `kanban_eventos` | `evento_id` (substituta) |

**`grupo` entra na chave** porque os identificadores de negocio nao sao unicos
sozinhos. A numeracao de cartao e de MR reinicia em 1 dentro de cada grupo, e
71 `commit_id` se repetem entre os grupos, em 213 registros — os commits do
repositorio-template herdados pelos tres forks. Todo join com essas tabelas usa
o par, nunca o numero ou o hash sozinho. `pessoa_id` e a excecao: ja traz o
grupo no prefixo (`G01-A13`) e e unico no conjunto inteiro.

**`kanban_eventos` nao tem chave natural**: 12 eventos do G02 aparecem
triplicados, identicos nas 6 colunas (os 36 registros com `coluna` vazia). A
tabela ganha `evento_id` como primeira coluna — o numero do registro no CSV,
1 para o primeiro apos o cabecalho. E a unica coluna do banco que nao vem do
CSV; ela distingue as copias sem descartar nenhuma. Quem for contar eventos
decide se deduplica, e declara a decisao.

## Campos multivalorados: intactos na tabela, divididos nas views

`rotulos` e os campos `*_ids` ficam gravados como no CSV, com o `;` original.
Cada um tem uma view com uma linha por valor:

| view | chave | valor | registros | linhas |
|---|---|---|---|---|
| `v_cartoes_rotulos` | `grupo`, `cartao_numero` | `rotulo` | 1.230 | 3.660 |
| `v_cartoes_responsaveis_ids` | `grupo`, `cartao_numero` | `pessoa_id` | 1.201 | 1.201 |
| `v_merge_requests_rotulos` | `grupo`, `mr_numero` | `rotulo` | 373 | 701 |
| `v_merge_requests_revisores_ids` | `grupo`, `mr_numero` | `pessoa_id` | 417 | 417 |
| `v_merge_requests_responsaveis_ids` | `grupo`, `mr_numero` | `pessoa_id` | 505 | 505 |

Toda view traz tambem `ordem`, `qtd_valores` e `peso_alocacao` (= 1/`qtd_valores`).
**Dividir multiplica o registro**: um cartao com 4 rotulos vira 4 linhas. Para
contar cartoes por rotulo use `COUNT(DISTINCT ...)`; para somar uma medida do
cartao por rotulo sem dupla contagem, multiplique por `peso_alocacao`. Os
rotulos saem na grafia bruta; a normalizacao (82 grafias -> 50) e da `dim_rotulo`
em `schema.sql`. `;` em texto livre (`descricao`, `mensagem`, `titulo`) nao e
separador e nao e dividido.

## Demais conversoes

**Tipo das colunas.** Inferido do conteudo: `INTEGER` quando todos os valores
preenchidos sao inteiros, `REAL` quando sao numericos, `DATE`/`DATETIME` como
acima, `TEXT` no resto. Um timestamp sem fuso faz a carga parar, em vez de
gravar uma hora possivelmente 3h errada. `cartoes.peso` ficou `TEXT` por ser
100% nulo na origem.

**Campo vazio vira `NULL`.** Nenhuma coluna do conjunto usa a string vazia como
valor com significado proprio.

## Conferencia

`verificar.py` fecha o circulo em tres partes: (1) le cada tabela de volta e
compara com o CSV — texto igual, e nas colunas `DATETIME` o mesmo instante;
(2) confirma a chave primaria de cada tabela e que `evento_id` e o numero do
registro; (3) remonta cada campo
multivalorado a partir da view e compara com o original.

## Indices

Cada chave primaria ja e um indice. Alem delas, ha indices sobre as colunas de
join que a chave nao cobre (`autor_id`, `pessoa_id`, `sprint`, `coluna`,
`pessoas.grupo`, `kanban_eventos(grupo, cartao_numero)`) e sobre
`(grupo, data)` em `commits` e `kanban_eventos`, para os filtros por periodo.

## Consulta rapida

```sql
-- commits autorais por dia, fora do historico herdado do template
SELECT c.grupo, date(c.autorado_em) AS dia, COUNT(*) AS commits
FROM   commits c
JOIN   grupos  g ON g.grupo = c.grupo
WHERE  c.commitado_em >= g.criado_em
  AND  c.e_merge = 0
GROUP  BY c.grupo, dia
ORDER  BY c.grupo, dia;

-- cartoes por rotulo, sem dupla contagem de comentarios
SELECT r.rotulo,
       COUNT(DISTINCT r.grupo || '-' || r.cartao_numero) AS cartoes,
       SUM(c.comentarios * r.peso_alocacao)              AS comentarios_alocados
FROM   v_cartoes_rotulos r
JOIN   cartoes c USING (grupo, cartao_numero)
GROUP  BY r.rotulo
ORDER  BY cartoes DESC;
```
