# 06 — Auditoria heurística e de vieses

> Registro da Aula 06 (dez heurísticas, escala de severidade de 0 a 4, sete vieses do artefato).
> **Escrito em 13/10/2026, depois da correção do professor (issue #1)**, que apontou a falta deste registro.
> Até a entrega de 10/10 os achados existiam, mas espalhados: na crítica da turma e do professor ao
> protótipo na Aula 07, no teste em voz alta (T08, seção 6 do [dossiê](../README.md)) e no fluxo do R01.
> Aqui eles estão na estrutura da aula (evidência → heurística → severidade → consequência → correção →
> reteste), junto com uma passada nova pelas dez heurísticas e pelos sete vieses nas telas atuais.

## Quem auditou, e o limite disso

| fonte | quem avaliou | quando | independente do grupo? |
| --- | --- | --- | --- |
| **A** · crítica ao protótipo | professor e turma, na apresentação da Aula 07 | 26/09/2026 | sim |
| **B** · teste em voz alta T08 | usuária externa simulando a orientadora; anotações da Thamyres | antes de 09/10/2026 | sim (leitora); anotação pelo grupo |
| **C** · correção da entrega | professor, issue #1 do repositório | 10/10/2026 | sim |
| **D** · passada pelas 10 heurísticas e pelos 7 vieses | o próprio grupo, com assistência de IA (Claude Code) | 13/10/2026 | **não** |

A aula diz que a auditoria deve ser feita por quem não construiu o painel, porque quem construiu sofre da
"maldição do conhecimento". Os achados **D** são autoavaliação e valem menos que A, B e C; ficam
registrados para não se perderem, e o reteste deles depende de uma pessoa de fora.

## Escala usada

0 não é problema · 1 cosmético · 2 menor (custa tempo, pede segundo olhar) · 3 grave (o leitor decide com
base numa leitura que o dado não sustenta) · 4 impede a decisão. A justificativa nomeia a decisão que muda.

## Achados

Estado: **corrigido** (com a correção já na tela), **corrigido, reteste pendente**, **aberto** (correção
proposta, não feita), **mantido** (decisão de não mudar, com motivo).

### Graves (3)

| # | fonte | evidência (o que se vê) | heurística | consequência na decisão | correção | reteste | estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AU-01 | C | O R06 abria já com o integrante de maior concentração selecionado, e a decisão escrita no requisito era "perguntar por que um integrante ficou o módulo inteiro num tipo de tarefa". | 1 (adequação à tarefa), 8; viés: erro fundamental de atribuição e ranking implícito | A orientadora leva para a reunião uma pergunta sobre um aluno, e não sobre o grupo; a divisão de papéis combinada pelo grupo vira defeito de uma pessoa. | R06 refeito em 13/10: a leitura principal é a divisão de cada eixo entre os 7 (parte dos 2 que mais têm, contra 29% da divisão igual); integrantes sempre na ordem do identificador; a tela abre sem ninguém selecionado; o limiar de foco virou contagem "n de 7", sem marcar quem; sem cor de alerta. | Uma pessoa de fora abre o R06 e descreve o grupo ("o design do G03 ficou com duas pessoas") sem citar um integrante pelo código. | corrigido, reteste pendente |
| AU-02 | B, C | Na visão geral, a célula com ▲ vinha em laranja com fundo destacado, o título dizia "Comece pelo G01: é o grupo que mais se afasta em N das 6 leituras" e o rodapé do placar somava os ▲ por grupo. Fala da leitora: "o grupo um está em vermelho [...] então eu como orientadora teria que começar pelo grupo um, que é o que está assim, pior". | 6, 8, 9; vieses: afeto (cor semântica) e ancoragem (título) | A orientadora trata a soma de leituras diferentes como nota do grupo e escolhe "o pior", quando cada linha é uma pergunta separada. | Visão geral revista em 13/10: sem soma de marcas; ◆ em tinta neutra com o texto "maior valor da linha"; barras na mesma cor para todos; frase de limite "valor alto não quer dizer grupo pior"; título passa a sugerir um assunto de abertura para cada grupo (a orientadora conversa com os três). | Uma pessoa de fora lê a visão geral e diz por qual assunto começaria com um grupo, sem chamar nenhum de pior. | corrigido, reteste pendente |
| AU-03 | A | No protótipo, o maior silêncio de cada grupo caía depois de 26/06, quando o calendário já tinha acabado (D3 do R01). | 7 (contexto e janela), 8 | Escolher o grupo errado para a conversa sobre ritmo, pelo motivo errado. | Marco "fim da Sprint 05 do G03 (26/06)" no gráfico; silêncios depois dele identificados no resumo, na lista e na visão geral; janela fixa de 23/04 para os três grupos, como o professor pediu. | Leitor descarta o silêncio pós-26/06 e procura silêncios dentro das sprints (roteiro do R01, seção 9 do fluxo). | corrigido; reteste parcial na T08 |
| AU-04 | A | Proposta inicial de somar commits e cartões numa mesma medida de volume. Professor: "posso ter 200 commits com card que é P e eu vou mudando só um caractere em cada commit". | 4 (codificação), 1 | Volume de commits lido como tamanho do trabalho. | R04 liga commits a cartões pelo `#N` e compara tempo com tamanho; R05 pesa pelo tamanho do cartão (dias planejados), não pela contagem. | — | corrigido |

### Menores (2)

| # | fonte | evidência | heurística | consequência | correção | reteste | estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AU-05 | B | No R06, as siglas "Cod", "Des", "Doc", "Neg" nos radares não fazem parte do vocabulário da leitora. | 2, 9 | Segundo olhar para saber que eixo é qual. | Legenda das siglas junto aos radares (Thamyres, 09/10), mantida no R06 refeito. | Leitora identifica o eixo de um vértice sem perguntar. | corrigido, reteste pendente |
| AU-06 | B | Dispersão do R04 pouco familiar; a leitora só entendeu com os textos de apoio. | 4, 5 | Tempo para ler o gráfico principal do R04. | Mantida: os textos de apoio resolveram no teste; tabela por tamanho e visão em tabela de todos os pontos ao lado. | — | mantido |
| AU-07 | B | No R01 a leitora entendeu as barras, mas não ligou sozinha o silêncio de 3+ dias a uma pergunta de acompanhamento. | 10 (acionabilidade) | O silêncio não vira pergunta, ou vira cobrança. | Visão geral passou a trazer, por assunto, o que observar na sprint seguinte e o aviso de que uma sprint só varia por acaso. No R01 a frase de limite continua junto ao gráfico. | Leitora formula uma pergunta ao grupo a partir de um silêncio, sem concluir que o grupo parou. | aberto (reteste do R01 nunca foi feito por inteiro) |
| AU-08 | A | Só o G03 tem datas de sprint; o professor sugeriu sobrepor as datas de sprint aos três grupos. | 7 | Silêncio sem referência de sprint em G01 e G02. | Feito em parte: o fim da Sprint 05 do G03 marca os três grupos. As outras fronteiras de sprint do G03 não são sobrepostas a G01 e G02, porque a premissa de que o calendário é o mesmo ficaria mais forte do que o dado sustenta. | — | aberto (decisão a confirmar com o professor) |
| AU-09 | A | Professor sugeriu dois alertas: uma pessoa com dois cartões em andamento ao mesmo tempo, e cartão que volta de coluna ("Card no Kanban não volta nunca"). | 1, 10 | Sinais de processo que a orientadora não vê. | Não implementados. O R02 soma as passagens de um cartão que volta à etapa, mas não aponta a volta. Ficam como lacuna da entrega, fora dos requisitos elicitados. | — | aberto |
| AU-10 | A | Taxa de conclusão só vale até a Sprint 4: na última, os alunos arrastam tudo para concluído. | 7, 8 | Concluído na Sprint 05 lido como entrega. | O R04 declara os 411 cartões fechados em lote como possível arrumação do quadro; o R05 permite filtrar por sprint. Nenhuma tela usa taxa de conclusão como indicador. | — | mantido |
| AU-11 | D | No R04, o tamanho (PP a GG, uma escala ordinal) vira dias planejados (0,25 a 5) e a razão realizado ÷ planejado mistura tamanhos no resumo do topo. | 4, 7; viés: ordinal tratado como contínuo | A mediana geral parece uma medida exata de quanto o grupo subestima. | Mantido com cuidado: os dias por tamanho são premissa declarada na tela; o gráfico separa uma coluna por tamanho e a tabela traz a mediana de cada tamanho. | — | mantido; premissa a confirmar |
| AU-12 | D | O R06 refeito mostra contagens com meio cartão ("64,5 cartões"), porque cartão de dois eixos conta metade em cada; a lista mostra o cartão inteiro nos dois filtros. | 6, 7; viés: precisão espúria | Leitor estranha a diferença entre o gráfico e a lista. | A legenda da lista explica a diferença; a regra está na premissa "Cartão de dois eixos". | Leitor explica a diferença sem ajuda. | corrigido, reteste pendente |

### Cosméticos ou sem problema (0 e 1)

| # | fonte | evidência | heurística | decisão |
| --- | --- | --- | --- | --- |
| AU-13 | A | Manter sábado e domingo no eixo do R01. Professor: "Não, é o que eles fazem." | 7 | 0: mantido; o fim de semana fica no eixo. |
| AU-14 | A | Normalizar o fuso: commits de sábado "feitos 3 horas antes". | 7 | 0: já feito na carga (`America/Sao_Paulo`). |
| AU-15 | D | Laranja de "passou do limite" no R02 e no R04. | 9 | 1: mantido; o laranja compara com um limite declarado, não com outro grupo, e sempre vem com triângulo (forma) e texto. |

## Os sete vieses do artefato, tela a tela

Passada **D** (autoavaliação), nas telas de 13/10/2026.

| viés | onde poderia aparecer | situação |
| --- | --- | --- |
| 1 · eixo truncado | barras do R02, R05, R06 e da visão geral | barras partem do zero; as escalas logarítmicas do R02 e do R04 estão declaradas no eixo e na nota |
| 2 · coroplético sem normalização | — | não há mapa |
| 3 · top N sem prestar contas | R04 rotula os 3 cartões mais distantes | a lista e a visão em tabela trazem todos os pontos; nenhuma tela corta categorias |
| 4 · ordinal como contínuo | tamanho do cartão no R04 e no R05 | premissa declarada; ver AU-11 |
| 5 · ranking de pessoas | R05 e R06 | integrantes na ordem do identificador; resumos sem nome; R06 refeito (AU-01) |
| 6 · cor semântica no valor bruto | visão geral | corrigido (AU-02) |
| 7 · precisão espúria | R05 (Gini), R06 (meio cartão) | Gini com 2 casas e intervalo quando há registro sem dono; percentuais com 0 ou 1 casa; ver AU-12 |

## Reteste pendente

Os achados AU-01, AU-02, AU-05, AU-07 e AU-12 pedem uma leitura por alguém de fora do grupo, com o mesmo
roteiro da T08: tarefa falada, nenhuma ajuda, frases literais anotadas. Até lá eles ficam como "corrigido,
reteste pendente" na [matriz de rastreabilidade](../README.md#4-matriz-de-rastreabilidade).
