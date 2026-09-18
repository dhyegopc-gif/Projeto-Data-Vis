# amostra_10linhas/

As 10 primeiras linhas de cada CSV da raiz, para leitura rapida e para testar
consultas sem carregar os arquivos inteiros.

```
py -3 amostra_10linhas/gerar_amostra.py    # regenera as amostras
```

Os CSVs da raiz sao abertos somente para leitura — as amostras sao os arquivos
derivados, com o mesmo nome do original.

## 10 linhas = 10 registros

Nao 10 linhas fisicas. `commits.mensagem` e `cartoes.descricao` trazem quebras
de linha dentro de aspas: `cartoes.csv` tem 1.238 registros em 8.876 linhas
fisicas. Cortar por linha fisica partiria um registro no meio e geraria um CSV
invalido.

Cada amostra e um **prefixo exato em bytes** do arquivo de origem: o recorte
copia as linhas originais em vez de reserializar o CSV, entao aspas, virgulas,
acentos e as quebras CRLF saem identicos. Abrir a amostra e ler as 10 primeiras
linhas do original da exatamente o mesmo resultado.

| arquivo                | registros na amostra | no original          |
| ---------------------- | -------------------- | -------------------- |
| `cartoes.csv`        | 10                   | 1.238                |
| `commits.csv`        | 10                   | 2.688                |
| `grupos.csv`         | 3                    | 3 — arquivo inteiro |
| `kanban_eventos.csv` | 10                   | 13.194               |
| `merge_requests.csv` | 10                   | 540                  |
| `pessoas.csv`        | 10                   | 83                   |
| `quadro_colunas.csv` | 10                   | 12                   |
| `sprints.csv`        | 10                   | 15                   |

`grupos.csv` tem so 3 grupos, entao a amostra e o arquivo completo.

## Cuidado ao usar

As primeiras linhas de cada arquivo sao todas do G01 e do inicio do periodo —
a amostra serve para inspecionar o formato das colunas, nao para estimar
distribuicoes. Para isso use `sqlite/dados.db`, que tem os dados completos.

---

# Grão, tipos, chaves e junções

Contrato dos 8 CSVs de `csvs_originais/`. Tudo abaixo foi medido nos arquivos,
nao no banco derivado (sql).

## Grão de cada arquivo

O que um registro representa. Um arquivo só entra em uma analise no grao que
ele declara aqui; misturar graos diferentes numa mesma soma e o erro mais caro
do conjunto.

| arquivo                | um registro e                                                                     |
| ---------------------- | --------------------------------------------------------------------------------- |
| `grupos.csv`         | Um grupo, com sua branch padrao e janela de atividade                             |
| `pessoas.csv`        | Uma pessoa vinculada a um grupo, com seu papel                                    |
| `sprints.csv`        | Uma sprint de um grupo, com inicio e prazo                                        |
| `quadro_colunas.csv` | Uma coluna do quadro Kanban de um grupo                                           |
| `commits.csv`        | Um commit, com autor, datas e linhas alteradas                                    |
| `merge_requests.csv` | Uma solicitacao de integracao (MR), com revisores e desfecho                      |
| `cartoes.csv`        | Um cartao do quadro, com responsaveis, rotulos e sprint                           |
| `kanban_eventos.csv` | A aplicacao ou remocao de um rotulo ou de uma coluna em um cartao (entrada/saida) |

`kanban_eventos.csv` e o unico arquivo cujo grao nao e homogeneo: 9.052
registros movem o cartao entre colunas do quadro e 4.106 apenas marcam um
rotulo, os dois sob a mesma coluna `coluna`. Separar antes de contar — o
criterio esta em [Regras de juncao](#regras-de-juncao).

## Convencoes de tipo

O CSV nao declara tipo: todo campo e texto no arquivo. O tipo listado e o
dominio do valor — o que o leitor pode assumir na conversao.

| tipo          | forma                            | onde                                                              |
| ------------- | -------------------------------- | ----------------------------------------------------------------- |
| `inteiro`   | digitos, sem separador de milhar | contagens, numeros de cartao e de MR                              |
| `booleano`  | `0` / `1`                    | `commits.e_merge`, `merge_requests.e_rascunho`                |
| `data`      | `AAAA-MM-DD`                   | `cartoes.prazo_em`, `sprints.inicio_em`, `sprints.prazo_em` |
| `timestamp` | ISO 8601 com milissegundos       | todos os demais campos de tempo                                   |
| `texto`     | livre                            | titulo, descricao, branch, mensagem                               |
| `lista`     | valores separados por`;`       | `rotulos`, `*_ids`                                            |

**Tres grafias de timestamp convivem.** `2026-04-22T17:38:42.296Z`, em UTC, vale
para grupos, cartoes, merge requests e kanban. Os dois campos de `commits` usam
offset explicito, e nao um so: `-03:00` em 2.144 registros e `+00:00` nos outros
544. Converter tudo para `America/Sao_Paulo` antes de derivar hora, dia ou
ordenar entre arquivos — comparar as grafias como string da resultado errado, e
tratar `+00:00` como hora local erra o dia de 544 commits.

**Campo vazio e ausencia de valor.** Nenhuma coluna do conjunto usa a string
vazia como valor com significado proprio.

Os arquivos sao UTF-8 sem BOM, com quebra CRLF, e usam aspas duplas apenas onde
o valor contem virgula, aspas ou quebra de linha.

## Chaves declaradas

| arquivo                | chave                               | registros |
| ---------------------- | ----------------------------------- | --------- |
| `grupos.csv`         | `grupo`                           | 3         |
| `pessoas.csv`        | `pessoa_id`                       | 83        |
| `sprints.csv`        | `grupo` + `sprint`              | 15        |
| `quadro_colunas.csv` | `grupo` + `quadro` + `coluna` | 12        |
| `cartoes.csv`        | `grupo` + `cartao_numero`       | 1.238     |
| `commits.csv`        | `grupo` + `commit_id`           | 2.688     |
| `merge_requests.csv` | `grupo` + `mr_numero`           | 540       |
| `kanban_eventos.csv` | sem chave natural                   | 13.194    |

Cada chave acima foi conferida: nenhuma repete.

**Por que `grupo` entra na chave.** Os identificadores de negocio nao sao unicos
sozinhos. A numeracao de cartao e de MR reinicia em 1 dentro de cada grupo — 451
dos 491 numeros de cartao e 170 dos 220 numeros de MR aparecem em mais de um
grupo. E 71 `commit_id` se repetem, em 213 registros: sao os commits do
repositorio-template, herdados identicos pelos tres forks, com o mesmo hash, a
mesma data e o mesmo titulo. `commit_id` sozinho como chave fundiria os tres
grupos em um.

**`pessoas.csv` e a excecao.** `pessoa_id` ja traz o grupo no prefixo
(`G01-A13`) e e unico no conjunto inteiro; a coluna `grupo` repete o prefixo em
83 de 83 registros. A chave e `pessoa_id` sozinho.

**`kanban_eventos.csv` nao tem chave natural.** Doze eventos do G02 aparecem
triplicados, identicos nas 6 colunas: 36 registros onde deveria haver 12. Sao
exatamente os 36 registros com `coluna` vazia. Quem precisa de chave usa uma
substituta — o numero da linha — ou deduplica declarando a decisao.

## Tipos por arquivo

Coluna `vazios` = registros sem valor.

### Arquivos de apoio

| campo                          | tipo      | vazios | dominio                                                      |
| ------------------------------ | --------- | ------ | ------------------------------------------------------------ |
| `grupos.grupo`               | texto     | —     | `G01` `G02` `G03`                                      |
| `grupos.branch_padrao`       | texto     | —     | sempre`main`                                               |
| `grupos.criado_em`           | timestamp | —     |                                                              |
| `grupos.ultima_atividade_em` | timestamp | —     |                                                              |
| `pessoas.grupo`              | texto     | —     | redundante com o prefixo do id                               |
| `pessoas.pessoa_id`          | texto     | —     | `Gnn-Ann`                                                  |
| `pessoas.papel`              | texto     | —     | `maintainer` 64, `reporter` 12, `owner` 6, `guest` 1 |
| `pessoas.situacao`           | texto     | —     | sempre`active`                                             |
| `sprints.grupo`              | texto     | —     |                                                              |
| `sprints.sprint`             | texto     | —     | `Sprint 01` .. `Sprint 05`                               |
| `sprints.situacao`           | texto     | —     | sempre`active`                                             |
| `sprints.inicio_em`          | data      | 10     | so o G03 preenche                                            |
| `sprints.prazo_em`           | data      | 10     | so o G03 preenche                                            |
| `quadro_colunas.grupo`       | texto     | —     |                                                              |
| `quadro_colunas.quadro`      | texto     | —     | sempre`Scrum Board`                                        |
| `quadro_colunas.posicao`     | inteiro   | —     | `0` Backlog .. `3` Review                                |
| `quadro_colunas.coluna`      | texto     | —     | 4 colunas, iguais nos 3 grupos                               |

### cartoes.csv — 1.238 registros

| campo                | tipo      | vazios | dominio                         |
| -------------------- | --------- | ------ | ------------------------------- |
| `grupo`            | texto     | —     |                                 |
| `cartao_numero`    | inteiro   | —     | reinicia em 1 por grupo         |
| `titulo`           | texto     | —     |                                 |
| `descricao`        | texto     | 538    | contem quebras de linha e`;`  |
| `situacao`         | texto     | —     | `closed` 1.174, `opened` 64 |
| `criado_em`        | timestamp | —     |                                 |
| `atualizado_em`    | timestamp | —     |                                 |
| `fechado_em`       | timestamp | 64     | preenchido se e so se`closed` |
| `prazo_em`         | data      | 1.214  | so 24 cartoes tem prazo         |
| `autor_id`         | texto     | —     | pessoa ou`[externo]`          |
| `fechado_por_id`   | texto     | 64     | pessoa ou`[externo]`          |
| `responsaveis_ids` | lista     | 37     | sempre 1 valor                  |
| `rotulos`          | lista     | 8      | 1 a 6 valores                   |
| `sprint`           | texto     | 64     |                                 |
| `peso`             | —        | 1.238  | coluna morta: 100% vazia        |
| `comentarios`      | inteiro   | —     |                                 |
| `tempo_estimado_s` | inteiro   | —     | segundos                        |
| `tempo_gasto_s`    | inteiro   | —     | coluna morta: constante`0`    |

### commits.csv — 2.688 registros

| campo                  | tipo      | vazios | dominio                             |
| ---------------------- | --------- | ------ | ----------------------------------- |
| `grupo`              | texto     | —     |                                     |
| `commit_id`          | texto     | —     | hash curto de 8 caracteres          |
| `autor_id`           | texto     | —     | pessoa,`[bot]` ou `[externo]`   |
| `autorado_em`        | timestamp | —     | offset explicito: `-03:00` ou `+00:00` |
| `commitado_em`       | timestamp | —     | offset explicito: `-03:00` ou `+00:00` |
| `e_merge`            | booleano  | —     | `1` em 762                        |
| `linhas_adicionadas` | inteiro   | —     |                                     |
| `linhas_removidas`   | inteiro   | —     |                                     |
| `linhas_total`       | inteiro   | —     | = adicionadas + removidas nos 2.688 |
| `titulo`             | texto     | 1      |                                     |
| `mensagem`           | texto     | 1      | contem quebras de linha             |

### merge_requests.csv — 540 registros

| campo                | tipo      | vazios | dominio                                                              |
| -------------------- | --------- | ------ | -------------------------------------------------------------------- |
| `grupo`            | texto     | —     |                                                                      |
| `mr_numero`        | inteiro   | —     | reinicia em 1 por grupo                                              |
| `titulo`           | texto     | —     |                                                                      |
| `descricao`        | texto     | 118    | contem quebras de linha e`;`                                       |
| `situacao`         | texto     | —     | `merged` 500, `closed` 39, `opened` 1                          |
| `criado_em`        | timestamp | —     |                                                                      |
| `atualizado_em`    | timestamp | —     |                                                                      |
| `merged_em`        | timestamp | 40     | preenchido se e so se`merged`                                      |
| `fechado_em`       | timestamp | 501    | preenchido se e so se`closed`                                      |
| `branch_origem`    | texto     | —     |                                                                      |
| `branch_destino`   | texto     | —     | `main` 463, `dev` 74, `develop` 2, `feat/edicao-cadastros` 1 |
| `autor_id`         | texto     | —     | pessoa ou`[externo]`                                               |
| `merged_por_id`    | texto     | 40     | pessoa ou`[externo]`                                               |
| `revisores_ids`    | lista     | 123    | sempre 1 valor                                                       |
| `responsaveis_ids` | lista     | 35     | sempre 1 valor                                                       |
| `e_rascunho`       | booleano  | —     | `1` em 5                                                           |
| `comentarios`      | inteiro   | —     |                                                                      |
| `sprint`           | texto     | 98     |                                                                      |
| `rotulos`          | lista     | 167    | 1 a 5 valores                                                        |

### kanban_eventos.csv — 13.194 registros

| campo             | tipo      | vazios | dominio                                            |
| ----------------- | --------- | ------ | -------------------------------------------------- |
| `grupo`         | texto     | —     |                                                    |
| `cartao_numero` | inteiro   | —     |                                                    |
| `acao`          | texto     | —     | `add` 8.445, `remove` 4.749                    |
| `coluna`        | texto     | 36     | coluna de quadro**ou** rotulo — ver juncoes |
| `pessoa_id`     | texto     | —     | pessoa ou`[externo]`                             |
| `ocorrido_em`   | timestamp | —     |                                                    |

## Campos multivalorados

Cinco campos foram desenhados para listas separadas por `;`. So dois carregam
mais de um valor de fato:

| campo                               | valores por registro | preenchidos |
| ----------------------------------- | -------------------- | ----------- |
| `cartoes.rotulos`                 | 1 a 6                | 1.230       |
| `merge_requests.rotulos`          | 1 a 5                | 373         |
| `cartoes.responsaveis_ids`        | sempre 1             | 1.201       |
| `merge_requests.revisores_ids`    | sempre 1             | 417         |
| `merge_requests.responsaveis_ids` | sempre 1             | 505         |

Os tres campos `_ids` tem nome plural e conteudo singular: nenhum `;` ocorre
neles hoje. Dividir por `;` mesmo assim nao custa nada e aceita a lista se ela
aparecer amanha.

Regras do campo `rotulos`, conferidas nos 1.603 registros preenchidos:

- separador `;` sem espaco em volta; nenhuma parte sai vazia;
- sem valor repetido dentro do mesmo registro;
- ordem alfabetica em 100% dos registros — a ordem nao significa nada, nao
  serve para inferir um rotulo principal;
- 82 grafias distintas em `cartoes`; as 62 de `merge_requests` sao um
  subconjunto delas.

**`;` em texto livre nao e separador.** Ele aparece como pontuacao em
`cartoes.descricao` (83 registros), `merge_requests.descricao` (59),
`commits.mensagem` (18) e `commits.titulo` (4). Dividir apenas os cinco campos
da tabela acima.

**Dividir multiplica o registro.** Um cartao com 4 rotulos vira 4 linhas, e
qualquer soma sobre a explosao conta o cartao 4 vezes. Em
[schema.sql](schema.sql) isso e resolvido pelas pontes `ponte_cartao_rotulo` e
`ponte_mr_rotulo`, com `peso_alocacao` = 1/`qtd_rotulos` para somar sem dupla
contagem.

## Regras de juncao

| de                                                               | para               | chave da juncao                        |
| ---------------------------------------------------------------- | ------------------ | -------------------------------------- |
| qualquer arquivo                                                 | `grupos`         | `grupo`                              |
| `cartoes`, `commits`, `merge_requests`, `kanban_eventos` | `pessoas`        | campo de pessoa =`pessoa_id`         |
| `cartoes`, `merge_requests`                                  | `sprints`        | `grupo` + `sprint`                 |
| `kanban_eventos`                                               | `cartoes`        | `grupo` + `cartao_numero`          |
| `kanban_eventos`                                               | `quadro_colunas` | `grupo` + `coluna` (casa em parte) |

**`grupo` entra em toda juncao, menos a de pessoa.** Juntar `kanban_eventos` a
`cartoes` so por `cartao_numero` devolve 35.289 linhas no lugar de 13.194 —
quase o triplo. Juntar `cartoes` a `sprints` so por `sprint` tambem triplica: os
cinco nomes de sprint existem nos tres grupos.

**Pessoa e global, nao por grupo.** A juncao e so por `pessoa_id`. Juntar por
`grupo` + `pessoa_id` perde a atuacao cruzada que existe nos dados: 6 commits e
3 MRs autorados por gente de outro grupo, e 15 MRs com revisor de outro grupo.

**Duas sentinelas ficam fora do roster.** `[externo]` e `[bot]` aparecem nos
campos de pessoa mas nao existem em `pessoas.csv`. Juncao interna as descarta em
silencio: 552 commits, 350 eventos de kanban, 24 cartoes e 22 MRs. Usar juncao
externa e trata-las como valores proprios. Dos 83 do roster, so 24 produzem
algum registro.

**`kanban_eventos.coluna` mistura dois assuntos.** Das 88 grafias do campo, 4
sao colunas do Scrum Board e 84 sao rotulos. A juncao com `quadro_colunas` casa
9.052 registros; os outros 4.106 sao marcacao de rotulo e 36 estao vazios — os
mesmos triplicados. A propria juncao e o discriminador: casou, e movimento de
coluna; nao casou, e rotulo. Juncao interna aqui so vale declarando que se esta
contando movimento e nada mais.

Cuidado: as 4 colunas do quadro tambem vazam para `cartoes.rotulos` como rotulo.
A grafia sozinha nao decide — quem decide e o par `grupo` + `coluna` contra
`quadro_colunas`.

**Integridade conferida.** Sem orfaos em `cartoes` -> `sprints`, em
`merge_requests` -> `sprints` e em `kanban_eventos` -> `cartoes`; todo `grupo`
existe em `grupos.csv`. Tres cartoes nao tem nenhum evento de kanban: G02 457,
G03 19 e G03 20.
