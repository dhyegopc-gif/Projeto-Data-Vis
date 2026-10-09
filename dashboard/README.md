# dashboard/

A visão geral e as telas dos seis requisitos de [Requisitos.MD](../requisitos/Requisitos.MD), para a
orientadora pedagógica. Cada tela é um arquivo HTML só, que abre no navegador sem
internet, com a versão em preto, branco e cinza ao lado (`_pb`).

| ordem de leitura | tela | arquivo | pergunta |
| --- | --- | --- | --- |
| 0 | Visão geral | `visao_geral.html` | com qual grupo começar, e por qual assunto? (R01 a R06 em uma página) |
| 1 | R03 · Cobertura do registro | `r03_cobertura_registro.html` | o registro deste grupo sustenta as leituras das outras telas? |
| 2 | R01 · Ritmo de registro | `r01_ritmo_de_registro.html` | em quais dias o registro se concentra, e há silêncio prolongado? |
| 3 | R02 · Acúmulo por etapa | `r02_acumulo_por_etapa.html` | em qual etapa do quadro os cartões se acumulam? |
| 4 | R04 · Planejado × realizado | `r04_prazo_planejado_realizado.html` | os cartões levam o tempo que o tamanho prometia? |
| 5 | R05 · Concentração (Gini) | `r05_concentracao_gini.html` | o trabalho registrado está distribuído ou concentrado em poucos? |
| 6 | R06 · Eixos de tarefa | `r06_eixos_de_tarefa.html` | cada integrante passou por vários eixos de tarefa ou ficou num só? |

A visão geral abre o painel: a leitura principal de cada requisito nos três grupos,
numa página, com link para cada tela já no grupo. Entre os requisitos, o R03 vem
primeiro porque diz qual leitura fica prejudicada em qual grupo. Todas as telas
têm a mesma faixa de navegação no topo (Início, depois R01 a R06): aberta do
disco, ela leva ao arquivo local; aberta na web, à versão publicada. As telas R01,
R02, R04, R05 e R06 aceitam o grupo no endereço (`r02_acumulo_por_etapa.html#G03`),
que é como a visão geral abre o detalhe.

```
py -3 dashboard/gerar_r01.py
py -3 dashboard/gerar_r02.py
py -3 dashboard/gerar_r03.py
py -3 dashboard/gerar_r04.py
py -3 dashboard/gerar_r05.py
py -3 dashboard/gerar_r06.py
py -3 dashboard/gerar_visao_geral.py   # por último: resume as outras
```

## Como as telas R02 a R06 e a visão geral são geradas

| arquivo | o que é |
| --- | --- |
| `gerar_rNN.py` | roda os `.sql` de `sqlite/`, reconta o essencial em Python e só grava se bater |
| `rNN_modelo.html` | o modelo da página (layout, gráficos e código); o gerador injeta os dados |
| `comum.css`, `comum.js` | estilo e funções comuns, injetados em cada modelo; mesmos tokens do R01 |
| `comum.py` | leitura do banco, conferência, lista das telas (com as URLs publicadas) e tema P&B |

O `gerar_r01.py` é anterior a esse arranjo e continua independente.

**Premissas.** Cada tela, inclusive o R01, tem o bloco "Premissas desta tela" antes do
rodapé, com a mesma lista da linha "Premissas do grupo" do requisito. A lista vive
em `PREMISSAS`, em `comum.py`; `premissas_no_requisito.py` a escreve no
`Requisitos.MD`, e cada gerador para se o requisito não trouxer a premissa com o
mesmo texto. Para mudar uma premissa: editar `comum.py`, rodar
`premissas_no_requisito.py` e depois os geradores.

**Teclado.** Setas e Enter no gráfico do R04; Tab e Enter nas etapas do R02 e nos
grupos do R05. Depois de cada escolha a tela é redesenhada e o foco volta ao mesmo
botão ou elemento (atributo `data-foco`, função `comFoco` em `comum.js`).

**Conferência antes de gravar.** Cada gerador para, sem gravar nada, se o número
que vai para a tela não bater com uma segunda conta:

| tela | o que é recontado |
| --- | --- |
| R02 | o detalhe cartão × etapa, somado, tem de reproduzir `r02_acumulo_por_etapa.sql` em cartões, passagens, horas, acima do limite, sem saída e etapa de maior acúmulo |
| R03 | autoria dos commits, tamanho do cartão e revisor de MR, contados direto das tabelas |
| R04 | o vínculo `#N` refeito com regex em Python tem de dar os mesmos pares do SQL; commits por cartão e medianas por tamanho também |
| R05 | o Gini refeito em Python a partir das contribuições, e 7 integrantes em todo recorte |
| R06 | o eixo de cada cartão refeito dos rótulos crus em Python tem de dar as mesmas partes do SQL, por integrante, sprint e eixo; 7 integrantes por grupo |
| Visão geral | cada leitura por um segundo caminho: t04 contra os commits autorais, o detalhe do R02 contra o resumo, o % do R04 contra o resumo por tamanho, o Gini do R05 refeito, o total do R06 contra a lista de cartões; e os padrões (3 dias, 48 h, 80%, 75%) contra as premissas |

**Cor.** Azul é "dentro do limite ou do planejado"; laranja é "passou". O par
passa no validador de daltonismo nos temas claro e escuro. A cor nunca é o único
canal: o laranja vem com triângulo (R02, R04), marca ▲ (R03) ou rótulo. Na
versão P&B as duas cores viram cinza e quase preto, e a forma segue separando.

## R02 · Acúmulo por etapa

- **Filtros**: grupo, sprint (todas, cada sprint, sem sprint) e limite de acúmulo
  (24, 48 ou 72 h; 48 é o padrão e é premissa nossa).
- **Resumo**: cartões no recorte, etapa de maior acúmulo, cartões acima do limite
  em alguma etapa e passagens sem saída registrada.
- **Gráfico**: as mesmas quatro linhas (etapas, na ordem do quadro) em dois
  painéis. À esquerda, quantos cartões passaram pela etapa, com os acima do limite
  em laranja; à direita, as horas de cada cartão na etapa, em escala logarítmica,
  com a linha do limite e a mediana. Em tela estreita os painéis empilham.
- **Lista da etapa**: clicar numa etapa (ou Tab + Enter) lista os cartões dela, do
  que ficou mais ao que ficou menos, com marca para passagens sem saída.
- Fonte: `r02_cartoes_da_etapa.sql` rodado com os parâmetros abertos (`'*'`).

## R03 · Cobertura do registro

- **Destaque**: a autoria dos commits do G01 contra a do G02, o exemplo que o
  requisito pede, montado a partir do dado.
- **Resumo por grupo**: quantos campos usados pelas telas ficam abaixo do mínimo.
- **Matriz**: campo × grupo, com percentual, medidor e a marca ▲ quando abaixo do
  mínimo; ao lado, o que o vazio impede e o link para a tela afetada. Autoria e
  responsável contam [externo] e [bot] como vazio. Campos em
  ordem da pior cobertura; o prazo do cartão, que nenhuma tela usa, vai no fim.
- **Leituras prejudicadas**: tela por tela, em quais grupos ela perde apoio.
- **Mínimo**: 70, 80 (padrão) ou 90%, premissa nossa.

## R04 · Planejado × realizado

- **Filtros**: grupo, sprint e tamanhos no gráfico.
- **Resumo**: cartões no gráfico, % que levou mais que o planejado, mediana de
  realizado ÷ planejado e % dos commits autorais ligados a cartão.
- **Dispersão**: uma coluna por tamanho (PP a GG), tempo entre criar e fechar em
  escala logarítmica com rótulos em linguagem comum. Em cada coluna, a linha
  "realizado = planejado" (faz o papel da diagonal da imagem de referência), a
  linha tracejada do dobro, a região "levou mais" sombreada e a mediana. Quem
  passou do planejado é triângulo laranja; os três cartões mais distantes ganham
  um número no ponto e aparecem, clicáveis, numa linha abaixo do gráfico.
- **Cartão aberto**: clicar num ponto (ou setas + Enter) abre o cartão e os
  commits que citam `#N` no título (ou na mensagem, quando o título não cita número). Abre com o cartão mais distante do planejado.
- **Por tamanho**: mediana do tempo, % acima do planejado e commits por cartão.
- Por que colunas e não eixo contínuo: o tamanho é uma categoria ordenada com
  cinco valores; colunas de mesma largura dão espaço igual para os pontos de cada
  tamanho, e o segmento "planejado" em cada coluna evita comparar o ponto
  afastado para o lado com uma diagonal inclinada.

## R05 · Concentração (Gini)

- **Filtros**: medida (dias planejados concluídos, a principal; cartões concluídos;
  commits autorais; merge requests), sprint (desligado para commits, que não têm
  sprint) e grupo em detalhe.
- **Gini por grupo**: barra de 0 a 1 com faixas de leitura (premissa), marca do
  máximo com 7 integrantes (0,857) e o intervalo possível quando há registro sem
  dono. Aqui os grupos aparecem juntos: o índice não depende da escala e os três
  têm 7 integrantes. Com poucos registros, porém, ele sobe por construção (4 MRs
  entre 7 pessoas não dão menos de 0,43); nas medidas de contagem, a tela avisa
  quando o recorte tem menos de 14 registros e desenha o ponto vazado.
- **Parte de cada integrante** vem na ordem do identificador, não do volume, e os
  resumos no topo não citam nomes: a tela não ordena alunos.
- Também: a linha de divisão igual (14,3%), a **curva de Lorenz**, o **Gini por
  sprint** e o mesmo grupo nas quatro medidas.

## R06 · Eixos de tarefa

- **Eixos**: os rótulos de tipo de tarefa do cartão em quatro grupos (premissa):
  Código (CODE, BUG, Fix, TEST, DEPLOY, CODE_REVIEW), Design (DESIGN),
  Documentação (DOCUMENTATION, REQUIREMENTS, user-story) e Negócio (NEGÓCIOS,
  Presentation). Não existe rótulo UX no conjunto; DESIGN é o mais próximo.
- **Filtros**: grupo, sprint e o limiar de foco (60, 75 ou 90%; 75 é o padrão).
- **Pequenos múltiplos**: um radar por integrante, na ordem do identificador,
  todos na mesma escala (0 a 100%), com o perfil do grupo tracejado por baixo e o
  anel do limiar. Vértice além do limiar vira triângulo laranja; com menos de 10
  cartões o contorno fica tracejado.
- **Radar do integrante**: o escolhido em tamanho grande, com o percentual dele e
  o do grupo no rótulo de cada eixo. Clicar num vértice filtra a lista.
- **Cartões do integrante**: os cartões em que ele é o responsável, filtráveis
  por eixo.
- **Parte de cada eixo**: matriz integrante × eixo em tom único (mais escuro, maior
  a parte), com os números escritos; é também a visão em tabela dos radares.
- Por que radar com cuidados: com 4 eixos fixos e escala igual, a forma mostra
  de relance para onde a pessoa pende. O radar exagera área, então a tela manda
  ler os vértices, sempre põe o grupo como referência e traz a matriz exata.

## Visão geral

- **Título que afirma** a conclusão (o grupo que mais se afasta e em quantas leituras).
- **Placar requisito × grupo**: a leitura principal de cada tela com os padrões
  dela, todas as sprints, com barra na escala natural da medida. O ▲ laranja marca,
  em cada linha, o grupo que mais se afasta dos outros dois (comparação relativa;
  os três têm 7 integrantes). O ◇ traz, da matriz do R03, o campo abaixo de 80%
  que aquela leitura usa naquele grupo. A célula abre a tela já no grupo.
- **Por onde começar**: para cada grupo, os assuntos com ▲ e o que conferir no
  registro antes.
- **O que cada requisito mostra**: uma frase por tela, montada a partir dos números.
- **Premissas** que mudam a página, com link para a lista completa de cada tela.

## Publicação

Versões coloridas publicadas (privadas; compartilhar pelo menu Share). As URLs
ficam também em `TELAS`, em `comum.py`, para a navegação entre telas.

| tela | URL |
| --- | --- |
| R01 | <https://claude.ai/artifact/J8vMTWGFyRVzfqxYK9nNXo> (P&B: <https://claude.ai/artifact/McKykihF3fN4L9pgwgynS2>) |
| R02 | <https://claude.ai/artifact/HTDPZKzttfVncZUGBU4kvv> |
| R03 | <https://claude.ai/artifact/6UznL9ZeRJR2973pazcdCG> |
| R04 | <https://claude.ai/artifact/X6Z8ZAoEurjtGkGagFE8my> |
| R05 | <https://claude.ai/artifact/UFJ17FrDcetbwMGXCuqNRj> |
| R06 | <https://claude.ai/artifact/4tvQRwKfVW5JZs6p2cYRqv> |
| Visão geral | <https://claude.ai/artifact/Jh4vnFxrMXM2oP9gE2jjsD> |

## Pendências

- **Premissas a confirmar**: dias por tamanho (R04), limite de 48 h (R02), mínimo
  de 80% (R03), critério de integrante e faixas de leitura do Gini (R05),
  agrupamento dos rótulos em eixos e limiar de foco de 75% (R06).
- **Validação externa:** a sessão de leitura T08 foi realizada e registrou impressões sobre a visão geral, R01, R02, R04 e R06. Ela não documenta o critério de aceite completo de cada tela; faltam evidências específicas de R03 e R05, além do reteste dos ajustes. Os resultados estão no [dossiê final](../README.md).

## R01 · Ritmo de registro

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

### De onde vêm os números

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

### O que a tela mostra

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

### Decisões de projeto

| decisão                                           | por quê                                                                                                           |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Um grupo por vez, cada um na sua escala            | O requisito veta comparar grupos de tamanhos diferentes sem normalizar                                             |
| Silêncio = 3 dias seguidos sem commit, ajustável | Premissa nossa: um a mais que um fim de semana. Não vem da cliente                                                |
| Marco em 26/06 para todos os grupos                | É a última sprint com data do conjunto (G03). G01 e G02 não têm datas de sprint; a tela diz de quem é o marco |
| Dia pela data de autoria, não de commit           | Segue o t04 e o requisito. 98 commits contados têm as duas datas diferentes; em 10 o dia muda                     |
| Dia de pico aberto na lista ao carregar            | A tela abre mostrando o que faz, sem esperar um clique                                                             |
| Sem rede                                           | Fontes do sistema, dados e código dentro do HTML; abre offline e não avisa terceiros                             |

### Pendências

- **Limiar de silêncio**: confirmar os 3 dias com o grupo.
- **Aceite formal do R01**: houve leitura externa do gráfico de commits na T08, mas as anotações não confirmam execução de todos os passos do roteiro da seção 9 de [05_fluxo_interacao_R01.md](05_fluxo_interacao_R01.md), especialmente localizar um dia zerado, abrir sua lista e explicar sem ajuda o que o gráfico não prova. O resultado permanece parcial, sem aprovação formal.