# dashboard/

Tela do requisito [R01 — Ritmo de registro ao longo dos dias](../requisitos/Requisitos.MD#r01--ritmo-de-registro-ao-longo-dos-dias),
para a orientadora pedagógica escolher com qual grupo conversar sobre ritmo de
trabalho e sobre qual período.

| arquivo                        | o que é                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------ |
| `r01_ritmo_de_registro.html` | o dashboard: um arquivo só, abre no navegador sem internet                    |
| `r01_ritmo_de_registro_pb.html` | o mesmo dashboard em preto, branco e cinza (impressão, projetor, leitura sem cor) |
| `gerar_r01.py`               | gera o HTML a partir de`sqlite/dados.db` e confere contra o t04              |
| `r01_modelo.html`            | o modelo da página (layout, estilo e código); o gerador injeta os dados nele |
| `05_fluxo_interacao_R01.md`  | fluxo de interação anotado: ciclo da métrica, divergências e suportes      |

```
py -3 dashboard/gerar_r01.py
```

O gerador grava as duas versões de uma vez, a partir do mesmo modelo: a P&B
só troca a paleta (tema `TEMA_PB` em `gerar_r01.py`), então dados, textos e
comportamento são sempre idênticos.

Versões publicadas (privadas; compartilhar pelo menu Share):

- colorida: <https://claude.ai/artifact/J8vMTWGFyRVzfqxYK9nNXo>
- preto, branco e cinza: <https://claude.ai/artifact/McKykihF3fN4L9pgwgynS2>

## De onde vêm os números

Mesma regra de [t04_cadencia_commits_diaria.sql](../sqlite/t04_cadencia_commits_diaria.sql)
e [Detalhamento_dos_commits.sql](../sqlite/Detalhamento_dos_commits.sql):

- grão: um commit, identificado por (`grupo`, `commit_id`);
- dia: `date(autorado_em)`, já em America/Sao_Paulo (a carga converte o fuso);
- fora da contagem: commits de merge (`e_merge = 1`) e o histórico herdado do
  repositório-template (`commitado_em < grupos.criado_em`), o mesmo corte da
  `vw_commit_autoral` do [schema.sql](../modelagem/schema.sql);
- janela: do primeiro ao último commit autoral dos grupos, 23/04/2026 a
  13/07/2026 (82 dias), com os dias sem commit como zero.

| grupo | registros em`commits` | merges | herdados do template  | contados no R01 |
| ----- | ----------------------- | ------ | --------------------- | --------------- |
| G01   | 662                     | 197    | 71 (10 deles merges)  | 404             |
| G02   | 1.067                   | 300    | 71 (10 deles merges)  | 706             |
| G03   | 959                     | 265    | 71 (10 deles merges)  | 633             |
| total | 2.688                   | 762    | 213 (30 deles merges) | 1.743           |

**Conferência.** Antes de gravar o HTML, `gerar_r01.py` roda o t04 e compara
dia a dia com os dados que vai embutir. Se um único dia divergir, ele para sem
gravar. O total embutido também tem de ser igual à soma do t04.

## O que a tela mostra

- **Filtros**, numa linha acima de tudo: grupo (um por vez), períodos prontos
  (todo o registro, últimos 30 e 14 dias, e as sprints do G03, único grupo com
  datas de sprint), datas De/Até e o limiar de silêncio.
- **Resumo**: commits no período, dias com commit, maior silêncio e dia de pico.
- **Commits por dia**: colunas com todos os dias do período. Dia sem commit
  tem uma marca cinza na linha de base. Faixas marcam silêncios a partir do
  limiar. Uma linha marca 26/06, fim da Sprint 05 do G03.
- **Lista do dia**: clicar num dia (ou setas + Enter no teclado) abre os
  commits que formam o total, com hora, autor, título e linhas alteradas.
  Autoria `[externo]` ou `[bot]` vem marcada como não resolvida.
- **Por dia da semana** e **Silêncios no período**, sobre o mesmo recorte.
- **Rodapé**: nota de origem, o que ficou fora da contagem, qualidade do
  registro e o que a tela não sustenta.
- **Visão em tabela** do gráfico diário (botão "Ver como tabela").

## Decisões de projeto

| decisão                                           | por quê                                                                                                           |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Um grupo por vez, cada um na sua escala            | O requisito veta comparar grupos de tamanhos diferentes sem normalizar                                             |
| Silêncio = 3 dias seguidos sem commit, ajustável | Premissa nossa: um a mais que um fim de semana. Não vem da cliente                                                |
| Marco em 26/06 para todos os grupos                | É a última sprint com data do conjunto (G03). G01 e G02 não têm datas de sprint; a tela diz de quem é o marco |
| Dia pela data de autoria, não de commit           | Segue o t04 e o requisito. 98 commits contados têm as duas datas diferentes; em 10 o dia muda                     |
| Dia de pico aberto na lista ao carregar            | A tela abre mostrando o que faz, sem esperar um clique                                                             |
| Sem rede                                           | Fontes do sistema, dados e código dentro do HTML; abre offline e não avisa terceiros                             |

## Pendências

- **Limiar de silêncio**: confirmar os 3 dias com o grupo.
- **Teste de aceite** com uma pessoa que não construiu a tela: ver o roteiro na
  seção 9 de [05_fluxo_interacao_R01.md](05_fluxo_interacao_R01.md).
