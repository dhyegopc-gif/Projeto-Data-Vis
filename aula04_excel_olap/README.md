# Aula 04 — do Excel ao OLAP com SQLite e DuckDB

Execução do laboratório da Aula 04 (Data Visualization, prof. Afonso Lelis) pelo grupo.
O registro com proveniência, gates, reconciliações e tempos está em
[`../docs/04_pipeline_excel_olap.md`](../docs/04_pipeline_excel_olap.md).

## Pastas

| Pasta | Conteúdo | Vai para o git? |
| --- | --- | --- |
| `contrato/` | `manifesto_olist.json`, `SHA256SUMS` e README dos dados, copiados do repositório do professor | sim |
| `entrada/` | os quatro `.xlsx` (imutáveis, somente leitura) | não (`.gitignore`) |
| `src/` | os scripts `00` a `06` | sim |
| `saida/` | relatórios JSON, HTMLs, plano e logs | sim, menos `olist.sqlite` e `olist.duckdb` |

## Como reconstruir (Windows, PowerShell)

Na pasta `aula04_excel_olap`:

```powershell
# 1. Ambiente (Python 3.13; o "python" da Microsoft Store não serve)
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Entrada: baixar os quatro .xlsx para entrada\ e conferir o SHA256
$base = "https://raw.githubusercontent.com/afonsolelis/aulas_mackenzie/HEAD/aulas/data_visualization/aula_04_do_excel_ao_olap_com_sqlite_duckdb_e_ia/dados"
New-Item -ItemType Directory -Force entrada | Out-Null
foreach ($f in "olist_pedidos_clientes.xlsx","olist_itens_pagamentos_avaliacoes.xlsx","olist_catalogo.xlsx","olist_geolocalizacao.xlsx") {
  Invoke-WebRequest "$base/$f" -OutFile "entrada\$f"
}
Get-FileHash entrada\*.xlsx -Algorithm SHA256   # comparar com contrato\SHA256SUMS

# 3. Pipeline, em ordem (cada script falha se o gate dele não passar)
Remove-Item saida\* -Recurse -Force -ErrorAction SilentlyContinue
.venv\Scripts\python.exe -I src\00_perfil_excel.py          # perfil_excel.json
.venv\Scripts\python.exe -I src\01_excel_para_sqlite.py     # olist.sqlite, carga_sqlite.json
.venv\Scripts\python.exe -I src\02_html_sqlite.py           # relatorio_sqlite.html
.venv\Scripts\python.exe -I src\03_sqlite_para_duckdb.py    # olist.duckdb, reconciliacao_duckdb.json (baixa a extensão sqlite na 1a vez)
.venv\Scripts\python.exe -I src\04_criar_mart_olap.py       # fato e mart, testes_mart.json, plano_duckdb_estado.txt
.venv\Scripts\python.exe -I src\05_html_duckdb.py           # dashboard_duckdb.html
.venv\Scripts\python.exe -I src\06_comparar_sqlite_duckdb.py  # medicoes_tempo.json

# 4. Ver os HTMLs
.venv\Scripts\python.exe -m http.server 8000 -d saida
```

Os HTMLs não carregam nada da rede (CSS e script embutidos, fontes do sistema) e também abrem direto do disco.
O pipeline completo levou alguns minutos nesta máquina; a maior parte é a leitura dos Excels pelo openpyxl.
