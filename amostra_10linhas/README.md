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

| arquivo | registros na amostra | no original |
|---|---|---|
| `cartoes.csv` | 10 | 1.238 |
| `commits.csv` | 10 | 2.688 |
| `grupos.csv` | 3 | 3 — arquivo inteiro |
| `kanban_eventos.csv` | 10 | 13.194 |
| `merge_requests.csv` | 10 | 540 |
| `pessoas.csv` | 10 | 83 |
| `quadro_colunas.csv` | 10 | 12 |
| `sprints.csv` | 10 | 15 |

`grupos.csv` tem so 3 grupos, entao a amostra e o arquivo completo.

## Cuidado ao usar

As primeiras linhas de cada arquivo sao todas do G01 e do inicio do periodo —
a amostra serve para inspecionar o formato das colunas, nao para estimar
distribuicoes. Para isso use `sqlite/dados.db`, que tem os dados completos.
