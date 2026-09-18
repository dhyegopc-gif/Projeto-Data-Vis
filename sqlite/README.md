# sqlite/

Os 8 CSVs da raiz do projeto carregados em um banco SQLite unico.

| arquivo | o que e |
|---|---|
| `dados.db` | o banco gerado — 8 tabelas, 17.773 linhas |
| `csv_para_sqlite.py` | gera `dados.db` do zero a partir dos CSVs |
| `verificar.py` | confere que o banco reproduz os CSVs linha a linha |

```
py -3 sqlite/csv_para_sqlite.py    # reconstroi dados.db
py -3 sqlite/verificar.py          # confere
```

## Os CSVs nao sao tocados

Os arquivos da raiz sao abertos somente para leitura. Nenhum e reescrito,
movido ou renomeado — o banco e sempre um artefato derivado, descartavel e
reconstruivel.

## O que a carga faz

Uma tabela por CSV, com o mesmo nome do arquivo, as mesmas colunas e a mesma
ordem. Nenhuma linha e filtrada, deduplicada ou normalizada: este e o estagio
bruto, fiel a origem. A modelagem dimensional descrita em
[modelagem/schema.sql](../modelagem/schema.sql) e uma camada seguinte, que
consome estas tabelas — inclusive as 24 duplicatas de `kanban_eventos` e os
213 commits herdados do repositorio-template, que continuam aqui.

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

## As duas unicas decisoes de conversao

**Tipo das colunas.** Inferido do conteudo: `INTEGER` quando todos os valores
preenchidos sao inteiros, `REAL` quando sao numericos, `TEXT` no resto. Como o
SQLite tem tipagem dinamica, o valor gravado continua identico ao do CSV — a
declaracao so garante que `ORDER BY cartao_numero` e `SUM(linhas_adicionadas)`
se comportem como numero e nao como texto. Timestamps ficam em `TEXT` no ISO
8601 original, que e o formato que `date()`, `strftime()` e comparacao de
string entendem no SQLite. `cartoes.peso` ficou `TEXT` por ser 100% nulo na
origem.

**Campo vazio vira `NULL`.** Nenhuma coluna do conjunto usa a string vazia como
valor com significado proprio.

`verificar.py` fecha o circulo: le o banco de volta, converte para texto
(`NULL` -> vazio) e compara com o CSV. As 8 tabelas batem linha a linha, na
mesma ordem.

## Indices

Criados sobre as chaves naturais e as colunas de join mais usadas (`grupo`,
`cartao_numero`, `commit_id`, `mr_numero`, `autor_id`, `pessoa_id`, `sprint`).
Nenhum e `UNIQUE`: `kanban_eventos` tem repeticoes legitimas na origem.

## Consulta rapida

```sql
-- commits por grupo, fora do historico herdado do template
SELECT c.grupo, COUNT(*) AS commits, SUM(c.linhas_total) AS linhas
FROM   commits c
JOIN   grupos  g ON g.grupo = c.grupo
WHERE  c.commitado_em >= g.criado_em
GROUP  BY c.grupo;
```
