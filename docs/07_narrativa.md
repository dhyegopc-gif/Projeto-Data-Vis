# 07 — Narrativa do painel

> Registro da Aula 07 (storytelling: da exploração à explicação, ideia central, título que afirma,
> sequência do painel, ficha técnica do indicador, narrar sobre pessoas em formação).
> **Escrito em 13/10/2026, depois da correção do professor (issue #1)**, que apontou a falta do registro de
> narrativa. Os números vêm das telas geradas nesta data, que recalculam tudo a partir de `sqlite/`.

## 1. Da exploração à explicação

Na exploração o grupo produziu as consultas de `sqlite/` (14 arquivos `.sql`, entre eles o
detalhamento dos commits, a cadência diária t04 e a view t05 dos eventos de Kanban). Na explicação ficaram
uma página de abertura e seis telas, uma por requisito, cada uma com função declarada. Ficaram fora do
painel as medidas que não sustentam decisão da orientadora: contagem de pessoas "ativas" (o campo
`situacao` é `active` para os 83 do cadastro e não distingue ninguém), volume de commits por pessoa (o
painel não ordena integrantes) e a soma de commits com cartões, que o professor desaconselhou na Aula 07.

## 2. Ideia central

> **Nos três grupos, o quadro trava na espera por revisão, e não na execução.** Em todas as sprints, a
> etapa com mais cartões parados por mais de 48 h é Waiting Review no G01 (82 cartões), no G02 (134) e no
> G03 (95), contra 19, 2 e 2 em Doing. A conversa de acompanhamento pode abrir pelo fluxo de revisão de
> cada grupo, com quem revisa, quando e quanto tempo o cartão espera, antes de falar de ritmo de commits.

- **Sujeito**: os três grupos e a etapa Waiting Review do quadro.
- **Tensão**: o cartão fica pronto e espera; o trabalho parado não está na execução.
- **Janela**: todas as sprints do módulo (23/04 a 26/06/2026 para cartões criados).
- **Quem faz algo diferente**: a orientadora, que leva o fluxo de revisão para a reunião, e o grupo, que
  combina quem revisa e em quanto tempo.
- **O que a derrubaria**: em algum grupo, Doing (execução) ter mais cartões acima de 48 h que Waiting
  Review; ou a espera em Waiting Review cair toda em fins de semana, o que a explicaria pelo calendário e
  não pelo processo. As duas coisas são observáveis nesta base: a primeira está no R02 (filtro por
  grupo e sprint); a segunda pede abrir a lista dos cartões da etapa e olhar as datas.
- **O que ela não afirma**: que a revisão é ruim ou lenta por culpa de alguém. O recorte não tem o texto da
  revisão nem o diff, e no G01 só 24% dos MRs têm revisor designado (R03), o que enfraquece a leitura
  da espera nesse grupo.

## 3. Sequência do painel

O painel não está em abas "Situação / Evidência / Decisão": é uma página de abertura (o one-pager que o
professor sugeriu na Aula 07) e uma tela de aprofundamento por requisito. A sequência da aula aparece assim:

| parte | onde está | o que faz |
| --- | --- | --- |
| **Situação** | visão geral: faixa de contexto (período, grupos, commits, cartões, MRs) e o placar requisito × grupo | estabelece o terreno comum: quem, quando e quanto, com a leitura principal de cada tela |
| **Evidência** | telas R01 a R06, abertas a partir da célula do placar já no grupo | de dois a quatro quadros por tela, com título que afirma ou descreve o processo, lista que abre o número até a origem e visão em tabela |
| **Decisão** | visão geral: "Por onde começar a conversa com cada grupo" | para cada grupo, os assuntos na ordem de prioridade, o que conferir no registro antes e o que observar na sprint seguinte |
| **O que este painel não afirma** | rodapé de cada tela ("O que esta tela não sustenta", "Qualidade do registro") e o bloco "Premissas desta tela" | a fonte, o recorte, a janela, a leitura errada mais provável e o efeito de cada premissa |

A limitação vem antes da recomendação na visão geral: a frase "valor alto não quer dizer grupo pior" fica
no topo do placar, e o roteiro de cada grupo começa pelo que conferir no registro.

## 4. Títulos

| tela | título (exemplo com o padrão) | afirma ou rotula? |
| --- | --- | --- |
| Visão geral | "Um assunto para abrir cada conversa: G01 por ritmo de registro, G02 pelo que o grupo quiser mostrar e G03 por eixos no grupo" | afirma |
| R01 | "Commits registrados por dia, grupo G01, 23/04/2026 a 13/07/2026" | rotula, com unidade e janela |
| R02 | "Onde os cartões se acumulam no quadro" | descreve o processo |
| R03 | "Quanto de cada campo o grupo preencheu, e que leitura isso compromete" | descreve o processo |
| R04 | "Tempo entre criar e fechar cada cartão, comparado ao tamanho planejado" | rotula |
| R05 | "Concentração do trabalho registrado entre os integrantes de cada grupo" | rotula |
| R06 | "No G03, todas as sprints, o eixo mais concentrado é Design: 2 dos 7 integrantes têm 88% dos cartões dele" | afirma |

Pendência: R01 a R05 ainda trazem títulos que descrevem ou rotulam. A aula pede que o título afirme o que
o quadro demonstra, com o número visível no próprio quadro. O resumo de cada uma dessas telas já tem o
número, então a troca é de texto e não de cálculo; fica como próximo passo.

## 5. Ficha técnica do indicador principal de cada tela

| tela | definição | fórmula e consulta | grão | meta ou faixa | dono e frequência | limitação |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | dias seguidos sem commit autoral do grupo | dias com zero na série diária; silêncio = 3 dias ou mais; `t04_cadencia_commits_diaria.sql` | grupo × dia | 3 dias (premissa) | orientadora, a cada sprint | dia sem commit não é dia sem trabalho |
| R02 | cartões que ficaram mais de 48 h numa etapa do quadro | horas somadas por cartão e etapa, pares add/remove; `r02_acumulo_por_etapa.sql` | cartão × etapa | 48 h (premissa; 24 e 72 para comparar) | orientadora, a cada sprint | tempo na etapa não é tempo de trabalho |
| R03 | percentual de preenchimento de cada campo usado pelas telas | preenchidos ÷ registros; `r03_cobertura_registro.sql` | grupo × campo | 80% (premissa) | orientadora, antes das outras telas | vazio não é desleixo; pode ser configuração |
| R04 | cartões que levaram mais que o tamanho previa | dias corridos ÷ dias planejados por tamanho; `r04_prazo_planejado_realizado.sql` | cartão fechado com tamanho | 1× (planejado) e 2× (o dobro) | orientadora, a cada sprint | dias por tamanho são premissa; não é atraso |
| R05 | concentração dos dias planejados concluídos entre os 7 | Gini sobre a soma por responsável; `r05_gini_concentracao.sql` | grupo × integrante | até 0,2 distribuído, até 0,4 moderado (premissa) | orientadora, a cada sprint | registro não é quem trabalhou |
| R06 | parte dos cartões de um eixo com os 2 integrantes que mais têm cartões nele | soma dos 2 maiores pesos ÷ cartões do eixo; `r06_divisao_do_eixo.sql` | grupo × eixo | 29% = divisão igual entre 7 | orientadora, a cada sprint | rótulo é posto pelo grupo; alocação não é competência |
| Visão geral | leitura principal de cada tela nos três grupos | as mesmas consultas, todas as sprints | requisito × grupo | maior valor da linha (◆), sem soma | orientadora, antes de cada rodada de reuniões | não é nota nem ranking |

## 6. Narrar sobre pessoas em formação

- O painel descreve no verbo do dado: "fez 12 commits", "2 integrantes têm 88% dos cartões de Design",
  nunca "se dedicou pouco" ou "não sabe design".
- Silêncio na fonte é ausência de evidência: a frase de limite do R01 fica junto ao gráfico.
- Nenhuma tela ordena integrantes por volume; R05 e R06 usam a ordem do identificador. Depois da correção,
  o R06 também deixou de abrir num integrante e de marcar quem passa do limiar de foco.
- A recomendação começa por uma conversa com o grupo: o roteiro da visão geral sugere o assunto, e a
  pergunta vai ao grupo.
- O teste da aula ("este quadro seria apresentado com o aluno descrito nele na primeira fileira?") foi o
  que derrubou a versão anterior do R06, que abria no integrante mais concentrado.
