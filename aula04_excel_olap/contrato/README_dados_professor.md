# Arquivos Excel — Olist

Espelho educacional das nove tabelas Olist usadas na disciplina Data Visualization. A fonte original é o [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), publicado pela Olist no Kaggle. Segundo os metadados atuais da fonte, o conjunto usa a licença [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/): atribuição, uso não comercial e compartilhamento pela mesma licença.

Esta cópia para a aula foi exportada em 29/08/2026 do banco `olist` somente leitura da disciplina, derivado da fonte original. As nove tabelas foram redistribuídas em quatro arquivos XLSX, organizadas em abas e validadas contra as contagens do banco. A conversão de formato não altera a atribuição nem os termos da licença original.

Os quatro arquivos cobrem todo o Olist: `olist_pedidos_clientes.xlsx` (pedidos e clientes), `olist_itens_pagamentos_avaliacoes.xlsx` (itens, pagamentos e avaliações), `olist_catalogo.xlsx` (produtos, vendedores e tradução) e `olist_geolocalizacao.xlsx` (geolocalização). Cada aba tem cabeçalho e os registros completos de sua tabela. A aba de geolocalização contém 1.000.163 registros mais o cabeçalho, abaixo do limite de 1.048.576 linhas do Excel.

Use [`manifesto_olist.json`](manifesto_olist.json) para validação automática e [`SHA256SUMS`](SHA256SUMS) para verificar integridade binária.

Os arquivos de entrada não devem ser modificados durante o laboratório.

Ao reutilizar ou publicar resultados, cite: **Olist. Brazilian E-Commerce Public Dataset by Olist. Kaggle, 2018.**
