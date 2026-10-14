# Dossiê Final — Data Visualization

**Equipe:** Dhyego, Thamyres e Augusto
**Projeto:** painel de apoio ao acompanhamento pedagógico de grupos no processo PBL.
**Painel:** [abrir a visão geral](dashboard/visao_geral.html) (HTML estático; abre do repositório clonado, sem login nem internet).

Este dossiê consolida os requisitos, as decisões de tratamento e os limites de interpretação do projeto. Os CSVs originais são mantidos como fonte; regras derivadas e premissas permanecem identificadas para que uma leitura do painel possa ser auditada. As seções seguem as nove partes pedidas na Aula 08.

> **Revisão de 13/10/2026, depois da correção do professor** ([issue #1](https://github.com/dhyegopc-gif/Projeto-Data-Vis/issues/1), sobre o commit `adb0393` de 09/10/2026). O que mudou em resposta a cada ponto de melhoria:
>
> | ponto da correção | o que foi feito | onde |
> | --- | --- | --- |
> | O link da entrega abre no branch `main`, vazio | o trabalho do `master` foi integrado ao `main` | branch `main` |
> | Falta a matriz de rastreabilidade completa | matriz com uma linha por requisito (R01 a R06, visão geral e as lacunas), estado, razão e as quatro condições comuns | [seção 4](#4-matriz-de-rastreabilidade) |
> | Decisões de recorte e lacunas estruturais fora do dossiê | `autorado_em` × `commitado_em`, fuso, histórico herdado, merges, autoria resolvida do recorte usado; as três lacunas estruturais em quatro partes | [seção 3](#3-fonte) |
> | O R06 desloca a decisão para o indivíduo | R06 refeito em torno da divisão de cada eixo dentro do grupo; abre sem destacar ninguém | [R06](dashboard/r06_eixos_de_tarefa.html), [requisito](requisitos/Requisitos.MD#r06--divisão-dos-tipos-de-tarefa-no-grupo-prioridade-4) |
> | A visão geral foi lida como veredito ("pior") | sem soma de marcas, sem cor de alerta, título por assunto de abertura de cada grupo | [visão geral](dashboard/visao_geral.html), [seção 6](#6-auditoria-e-teste-com-usuário) |
> | Faltam registros da Aula 04, da auditoria heurística e de vieses e da narrativa (e o brief de qualidade) | registros escritos e versionados | [docs/](docs/README.md) |
> | Priorização só no R01 | prioridade declarada para todos os requisitos, com o motivo | [seção 2](#2-requisitos) |
> | Plataforma sem justificativa; versões publicadas privadas | justificativa da escolha e do que ela custa; a navegação entre telas usa só arquivos do repositório | [seção 7](#7-painel) |
>
> A versão entregue em 10/10 continua no histórico do git (`adb0393`).

## 1. Contexto

O projeto reúne uma visão geral e seis telas analíticas para apoiar conversas de acompanhamento pedagógico a partir dos registros disponíveis de quadro Kanban, commits e merge requests. O público principal é a **orientadora pedagógica** (Vanessa), que consulta o painel antes ou durante o planejamento de conversas com os grupos e tem cerca de 4 minutos antes de cada reunião.

- **Decisão servida:** por qual assunto abrir a conversa com cada grupo e o que perguntar (ritmo de registro, acúmulo no quadro, estimativa de tamanho, divisão do trabalho), e quando pedir antes que o grupo corrija a forma de registrar.
- **Consequência do erro:** uma conversa de cobrança com um grupo que trabalhou sem deixar rastro (programação em dupla, estudo, reunião), ou uma conclusão sobre uma pessoa a partir de um campo incompleto. A decisão recai sobre estudantes reais em formação.

**Unidade de análise obrigatória: o grupo.** Os indicadores comparam ou descrevem G01, G02 e G03. Identificadores de pessoas podem aparecer em detalhes para explicar a origem de um registro ou como parte da distribuição interna do grupo, mas não transformam o painel em avaliação, ranking ou medida de desempenho individual. Registro em ferramenta não equivale a esforço, participação integral ou aprendizagem.

O brief completo, com o perfil de qualidade e as regras testáveis, está em [docs/01_brief_e_qualidade.md](docs/01_brief_e_qualidade.md).

## 2. Requisitos

O catálogo completo, com os cinco campos da elicitação (público, decisão, frequência, critério de aceite, evidência), regra de cálculo, suporte na tela, lacunas e premissas, está em [`requisitos/Requisitos.MD`](requisitos/Requisitos.MD). A prioridade é premissa do grupo, a confirmar com a cliente: a orientação não ordenou os requisitos.

| prioridade | requisito | pergunta de decisão | decisão que apoia | por que esta prioridade |
| :---: | --- | --- | --- | --- |
| abertura | Visão geral | O que cada requisito diz de cada grupo, e por qual assunto começar com cada um? | Por qual assunto abrir a conversa com cada grupo | Tela de abertura; resume as seis |
| 1 | R01 · Ritmo de registro | Em quais dias o registro do grupo se concentra, e há silêncio prolongado que mereça uma pergunta? | Com qual grupo abrir conversa sobre ritmo, e sobre qual período | Requisito atribuído ao grupo desde a elicitação; único com fluxo anotado completo |
| 2 | R03 · Cobertura do registro | O registro deste grupo está completo o suficiente para sustentar as leituras das outras telas? | Levar a leitura à conversa ou pedir antes que o grupo corrija o registro | Condição para ler os outros |
| 3 | R02 · Acúmulo por etapa | Em qual etapa do quadro os cartões deste grupo se acumulam? | Perguntar sobre espera por revisão ou sobre execução | O professor, como orientador, chamou de "importante" na Aula 07 |
| 4 | R06 · Divisão dos tipos de tarefa | Os cartões de cada tipo de tarefa passam pelos 7 integrantes ou ficam com poucos? | Propor ao grupo rodízio entre os eixos | Pergunta levantada pelo professor na Aula 07 |
| 5 | R04 · Planejado × realizado | Os cartões levam o tempo que o tamanho prometia? | Sobre quais cartões ou tamanhos perguntar | Recomendação do professor, apoiada numa premissa forte (dias por tamanho) |
| 6 | R05 · Concentração (Gini) | O trabalho registrado está distribuído ou concentrado em poucos integrantes? | Abrir ou não a conversa sobre divisão do trabalho | Pedido do próprio grupo; depende de duas premissas |

Exemplo preenchido, R01:

| Campo | Especificação |
| --- | --- |
| **Público** | Orientadora pedagógica. |
| **Decisão** | Escolher com qual grupo abrir uma conversa sobre ritmo de trabalho e qual período investigar, sem tratar ausência de commit como ausência de trabalho. |
| **Frequência** | A cada sprint e antes de uma reunião de acompanhamento. |
| **Critério de Aceite** | 1. Selecionar um grupo e um período. 2. Ler a quantidade de commits autorais por dia, incluindo dias sem registro como zero. 3. Abrir um dia e conferir os commits que compõem o total. 4. Explicar, sem ajuda, que a tela mostra registros no Git e não mede todo o trabalho do grupo. |
| **Evidência** | `commits.csv`: `grupo`, `commit_id`, `autor_id`, `autorado_em`, `commitado_em` e `e_merge`; `grupos.csv`: `grupo` e `criado_em`, usados para excluir histórico anterior à criação do grupo. A chave analítica do commit é (`grupo`, `commit_id`). |
| **Lacunas** | Não mede esforço ou horas trabalhadas fora do Git, estudo, reuniões ou programação em dupla sem commit. Um dia sem commit não é um dia sem trabalho. Autoria não resolvida também limita leituras por pessoa. |

**Anotações do atendimento da Aula 08:** não há registro escrito do atendimento de 03/10/2026 no repositório. Nenhum campo de requisito foi fechado com base nele.

## 3. Fonte

### Recorte usado

Os 8 CSVs da **turma T28** (grupos G01, G02 e G03) publicados na página do projeto, em [`csvs_originais/`](csvs_originais/), preservados sem edição e carregados em `sqlite/dados.db`. O recorte completo das 15 turmas (`projeto_pbl_completo.zip`) **não foi usado** e não está no repositório.

| arquivo | um registro é | registros |
| --- | --- | ---: |
| `grupos.csv` | um grupo | 3 |
| `pessoas.csv` | uma pessoa vinculada a um grupo | 83 |
| `sprints.csv` | uma sprint de um grupo | 15 |
| `quadro_colunas.csv` | uma coluna do Scrum Board | 12 |
| `commits.csv` | um commit, chave (`grupo`, `commit_id`) | 2.688 |
| `merge_requests.csv` | um MR, chave (`grupo`, `mr_numero`) | 540 |
| `cartoes.csv` | um cartão, chave (`grupo`, `cartao_numero`) | 1.238 |
| `kanban_eventos.csv` | aplicação ou remoção de rótulo ou coluna num cartão; sem chave natural | 13.194 |

Grão, tipos, chaves e junções: [`modelagem/Contrato_de_dados.md`](modelagem/Contrato_de_dados.md).

### Tratamento de dados e regras de negócio

Os arquivos de `csvs_originais/` são preservados sem alteração. O banco SQLite reproduz as tabelas de origem; o tratamento analítico do Kanban é feito na view `t05_eventos_kanban`.

- **Duplicatas:** a view remove as 24 linhas integralmente duplicadas de `kanban_eventos.csv` para análise, reduzindo 13.194 registros a 13.170 eventos distintos. As linhas originais continuam preservadas na fonte e na tabela bruta do banco.
- **Campos vazios:** a carga converte campos vazios em `NULL`. Na classificação dos eventos, `coluna` vazia ou em branco é marcada como `DESCONHECIDO`; não é tratada como etapa nem rótulo.
- **Mudança de coluna versus marcação de rótulo:** quando `coluna` corresponde a uma coluna do `Scrum Board` do mesmo grupo, o evento é `MUDANCA_COLUNA`; quando não corresponde, é `MARCACAO_ROTULO`. Valores ausentes ficam separados como desconhecidos. Rótulos são normalizados e categorizados, distinguindo, por exemplo, tamanho de prioridade.
- **Flag `is_bot`:** a view deriva uma flag a partir de identificadores de evento que contêm marcadores reconhecíveis como `bot`, `automat`, `automation`, `pipeline` ou `runner`. É uma classificação operacional baseada no texto disponível, não uma prova universal de automação.
- **Duração:** eventos deduplicados de cada cartão são ordenados por instante e recebem uma sequência. `horas_ate_proximo_evento` calcula as horas entre o evento atual e o próximo evento do mesmo cartão; no último evento, sem próximo registro, o valor fica nulo. É tempo decorrido entre registros, não horas de trabalho.
- **Calendário de sprints:** as datas de G01 e G02 estão vazias na origem. Como **Premissa do Grupo**, o calendário preenchido de G03 é usado para classificar eventos dos três grupos. A origem do calendário aplicado é identificada na view; as datas atribuídas a G01 e G02 não são apresentadas como observações originais.

O detalhamento técnico está em [`sqlite/t05_eventos_kanban.sql`](sqlite/t05_eventos_kanban.sql) e [`sqlite/README.md`](sqlite/README.md).

### Decisões de recorte

Cada uma muda o que o painel pode afirmar, e cada uma aparece na tela onde o número é lido.

| decisão | escolha | o que o dado mostra | onde aparece |
| --- | --- | --- | --- |
| **Data do commit** | `autorado_em` (data de autoria), não `commitado_em` (data do commit) | A autoria é quando a pessoa fez a alteração, gravada pelo cliente git dela; a data do commit muda quando alguém faz rebase, cherry-pick ou aplica o commit de outra pessoa. Nos 1.743 commits contados no R01, **98 têm as duas datas diferentes, e em 10 o dia muda**. Nenhum commit tem `commitado_em` anterior a `autorado_em`. | premissa "Dia do commit" do R01; nota de origem |
| **Fuso** | todo instante convertido para `America/Sao_Paulo` na carga | Três grafias convivem: `Z` (UTC) em grupos, cartões, MRs e Kanban; em `commits`, `-03:00` em 2.144 registros e `+00:00` em 544. Tratar `+00:00` como hora local erraria o dia de 544 commits (o professor apontou commits "de sábado" feitos 3 horas antes). `sqlite/verificar.py` confere o instante valor a valor. | nota de origem de cada tela |
| **Histórico herdado** | excluído: commits com `commitado_em` anterior à criação do grupo | 213 commits (71 hashes repetidos nos três grupos), de 2022 a 2025, vieram do repositório-template. Sem o corte, o autor do template contaria como trabalho dos três grupos. | linha de recorte do R01 (D1) |
| **Commits de merge** | excluídos da contagem autoral | 762 de 2.688 (28,3%); só 31 são do `[bot]`, o resto é "Merge branch" feito pelos alunos. | linha de recorte do R01 |
| **Janela** | fixa e igual para os três grupos: 23/04/2026 a 13/07/2026 | Primeiro e último commit autoral do conjunto, 82 dias, com dia sem commit como zero. O professor pediu janela fixa para todos. | título do R01; faixa de contexto da visão geral |
| **Sprints sem data** | marco de 26/06/2026 (fim da Sprint 05 do G03) aplicado aos três | 10 das 15 sprints, todas de G01 e G02, não têm datas; não dá para atribuir commit a sprint por data. Cartões e MRs trazem a sprint pelo nome. | marco no R01; premissa "Marco de fim de sprint" |
| **Autoria resolvida** | `[externo]` e `[bot]` contam como não atribuídos | No recorte da T28, **2.136 dos 2.688 commits (79,5%)** resolvem para uma pessoa do cadastro; 552 (20,5%) não: 29,9% no G01, 12,9% no G02 e 22,5% no G03. Na base do R01, 305 de 1.743 (17,5%). O número 88,5% da Aula 08 é do recorte completo, que não foi usado. | junto ao gráfico do R01 ("Não atribuídos: N de M"); tile "Sem dono identificado" e faixa possível no R05; R03 |

### Lacunas estruturais

As três lacunas que a Aula 08 manda declarar em qualquer dossiê, no formato de quatro partes.

| lacuna | o que foi pedido | por que a fonte não alcança | o que o painel afirma no lugar | o que a resolveria |
| --- | --- | --- | --- | --- |
| **Fotografia com data** | Ler a situação atual de cada grupo | A data de extração não está registrada em nenhum arquivo (estação de extração). Os CSVs entraram no repositório em 18/09/2026; o registro mais recente é de 07/08/2026. Nada posterior à extração existe na base. | Cada tela diz "data de extração não registrada", a data de entrada no repositório e o registro mais recente. "Últimos 14 dias" é relativo ao último commit (13/07/2026), não a hoje. | Registrar a data e o método da extração junto aos CSVs, ou ler direto do GitLab com data de consulta. |
| **Sem diff nem texto de revisão** | Saber se o código é bom e se a revisão foi criteriosa | O recorte traz linhas alteradas, revisor designado (417 de 540 MRs) e contagem de comentários do MR, mas não o diff nem o texto dos comentários (perda na extração). | Nenhuma tela fala de qualidade de código nem de revisão criteriosa. O R02 mede quanto tempo o cartão espera em Waiting Review, não como foi a revisão. | Exportar o texto das revisões e o diff de cada MR, com o custo de expor a escrita dos alunos e de exigir leitura humana. |
| **Ausência de rastro não prova ausência de trabalho** | Saber quem trabalhou e quanto | Conversa fora da plataforma, programação em par no mesmo teclado, estudo e código descartado antes do commit não viram registro (passagem do evento para a captura). Um integrante pouco visível nos dados é alguém sobre quem esta fonte não tem evidência. | "Um dia sem commit não é um dia sem trabalho" junto ao gráfico do R01; "registro não é trabalho" no R05, no R06 e na visão geral. | Registro de pareamento, diário de bordo do grupo ou observação da orientadora, todos com custo para quem é observado. |

### Dicionário e vocabulário

Os termos foram padronizados para separar o que as fontes efetivamente registram da interpretação de negócio adotada para construir as visualizações. A elicitação da cliente é uma fonte congelada: interpretações sem confirmação devem ser apresentadas como **Premissa do Grupo**, nunca atribuídas à cliente. O vocabulário completo está em [`vocabulario/t02_Vocabulario_do_Projeto.md`](vocabulario/t02_Vocabulario_do_Projeto.md).

| Termo | Definição do dado | Interpretação e limite |
| --- | --- | --- |
| **Entrega** | Um cartão pode chegar à coluna final registrada; um MR pode ter `situacao = merged`. São sinais diferentes. | Não comprovam, isoladamente, validade ou aceitação pedagógica do conteúdo. |
| **Atraso** | Pode ser calculado somente onde existem prazo e datas aplicáveis; apenas 24 de 1.238 cartões têm `prazo_em`. | A definição de atraso depende de calendário e regra de negócio. O R04 diz "levou mais que o planejado", não "atrasou". |
| **Participação** | Há rastros de commits, eventos Kanban e MRs, em grãos diferentes. | São registros da plataforma; não medem presença, dedicação ou toda a colaboração. |
| **Revisão** | O MR registra identificadores de revisores e contagem de comentários. | Não comprova leitura criteriosa, aprovação ou autoria individual dos comentários. |
| **Concluído** | O estado do cartão ou do MR e os eventos registram estados operacionais. | Estado final no sistema não garante que o trabalho foi realizado ou validado como esperado. |
| **Ativo** | `pessoas.situacao` está como `active` para os 83 perfis; pode-se também observar registros em um período. | O campo da origem não distingue engajamento. Ter registro não prova contribuição contínua. |
| **Automação / Bot** | A autoria `[bot]` pode aparecer em commits; eventos podem trazer identificadores reconhecíveis. | A classificação depende da informação disponível. Não se deve inferir que um registro é humano ou automatizado apenas pelo padrão de atividade. |
| **Tamanho vs. prioridade** | Rótulos como `SIZE_P` indicam uma categoria registrada; `P1` a `P8` são tokens de prioridade. | Tamanho e prioridade são conceitos distintos. A equivalência de tamanho com complexidade ou dias é premissa, não medida observada. |

**Regra inegociável:** em todo artefato, tabela ou tela, manter separados **Definição do Dado** (o que a fonte registra) e **Premissa do Grupo** (interpretação, corte ou regra não confirmada). Campo vazio é ausência de valor, não autorização para completar por inferência.

## 4. Matriz de rastreabilidade

Uma linha por requisito da [lista elicitada](requisitos/Requisitos.MD), inclusive as perguntas que o painel não atende. "Onde é atendido" dá a tela e o nome exato do quadro. Estados: **atendido**, **atendido com ressalva** (o painel responde, mas a resposta é mais fraca que o enunciado; a razão diz onde a afirmação para) e **lacuna declarada** (a fonte não alcança).

| id | enunciado (pergunta de decisão) | decisão servida | critério de aceite | onde é atendido | evidência no dado | estado | razão |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VG | O que cada requisito diz de cada grupo, e por qual assunto começar com cada um? | Assunto de abertura da conversa com cada grupo | Em menos de um minuto, diz por qual assunto começaria com um grupo, abre a tela do requisito nesse grupo e diz que o ◆ marca o maior valor de uma linha, não um grupo pior | [visão geral](dashboard/visao_geral.html) · "Leitura principal de cada requisito, nos três grupos" e "Por onde começar a conversa com cada grupo" | as consultas das seis telas, todas as sprints; grão requisito × grupo; cada célula abre a tela no grupo | atendido com ressalva | Reformulada em 13/10 depois que a leitora da T08 leu a cor como "pior"; a versão nova ainda não foi relida por alguém de fora. Herda as ressalvas de cada linha. |
| R01 | Em quais dias o registro de trabalho do grupo se concentra, e existe algum silêncio prolongado que mereça uma pergunta? | Com qual grupo abrir conversa sobre ritmo, e sobre qual período | Seleciona grupo e período, lê commits por dia, acha um dia zerado, abre a lista de um dia e diz sem ajuda o que o gráfico não prova | [R01](dashboard/r01_ritmo_de_registro.html) · "Commits por dia" e "Commits do dia" | `commits` (`grupo`, `commit_id`, `autorado_em`, `e_merge`) e `grupos.criado_em`; [`t04_cadencia_commits_diaria.sql`](sqlite/t04_cadencia_commits_diaria.sql); grão grupo × dia | atendido com ressalva | Mede registro de alteração no Git, não esforço; 27,5% dos commits contados no G01 não têm autor. O aceite formal na T08 ficou parcial: a leitora não ligou sozinha o silêncio a uma pergunta. |
| R02 | Em qual etapa do quadro os cartões deste grupo se acumulam ao longo da sprint? | O que perguntar: espera por revisão ou execução | Seleciona grupo e sprint, vê cartões e tempo por etapa e abre os cartões da etapa de maior acúmulo; casos sem saída aparecem | [R02](dashboard/r02_acumulo_por_etapa.html) · "Quantos cartões passaram por cada etapa, e quanto tempo cada um ficou nela" e "Cartões da etapa" | `kanban_eventos` pela view `t05_eventos_kanban`; [`r02_acumulo_por_etapa.sql`](sqlite/r02_acumulo_por_etapa.sql), [`r02_cartoes_da_etapa.sql`](sqlite/r02_cartoes_da_etapa.sql); grão cartão × etapa | atendido com ressalva | Tempo na etapa é tempo corrido, não trabalho; o limite de 48 h é premissa nossa. No G01 só 24% dos MRs têm revisor, o que enfraquece a leitura da espera em Waiting Review. |
| R03 | O registro deste grupo está completo o suficiente para sustentar as leituras das outras telas? | Levar a leitura à conversa ou pedir antes a correção do registro | Abre antes das outras, lê a cobertura de cada campo por grupo e diz qual leitura fica prejudicada em qual grupo | [R03](dashboard/r03_cobertura_registro.html) · "Cobertura de cada campo, por grupo" e "Leituras prejudicadas, tela por tela" | `commits`, `cartoes`, `merge_requests`, `sprints`; [`r03_cobertura_registro.sql`](sqlite/r03_cobertura_registro.sql); grão grupo × campo | atendido com ressalva | A tela mostra onde o registro falta, não por quê (configuração, conta não vinculada ou combinado com a orientação). Não foi lida por ninguém de fora: a acionabilidade não foi verificada. |
| R04 | Os cartões deste grupo levam o tempo que o tamanho prometia, e quais fogem tanto do previsto que merecem uma pergunta? | Sobre quais cartões ou tamanhos perguntar | Escolhe grupo e sprint, aponta um cartão acima da linha, abre os commits ligados e diz que o gráfico mede tempo decorrido | [R04](dashboard/r04_prazo_planejado_realizado.html) · "Cada ponto é um cartão fechado…" e "Cartão aberto" | `cartoes` (`criado_em`, `fechado_em`, `rotulos`) e `commits` (`titulo`, `mensagem`); [`r04_prazo_planejado_realizado.sql`](sqlite/r04_prazo_planejado_realizado.sql), [`r04_commits_por_cartao.sql`](sqlite/r04_commits_por_cartao.sql); grão cartão fechado com tamanho | atendido com ressalva | Os dias por tamanho são premissa; tempo corrido inclui noite, fim de semana e espera no Backlog; 411 cartões foram fechados em lote. A tela diz "levou mais que o planejado", nunca "atrasou". |
| R05 | O trabalho registrado do grupo está distribuído entre os integrantes ou concentrado em poucas pessoas? | Abrir ou não a conversa sobre divisão do trabalho, e com base em qual registro | Compara os três grupos numa medida, lê na curva de Lorenz quanto somam os de menos registro, troca a medida e diz que o índice mede concentração do registro | [R05](dashboard/r05_concentracao_gini.html) · "Índice de Gini por grupo", "Parte de cada integrante" e "Curva de Lorenz" | `cartoes`, `commits`, `merge_requests`, `kanban_eventos`, `pessoas`; [`r05_contribuicao_por_integrante.sql`](sqlite/r05_contribuicao_por_integrante.sql), [`r05_gini_concentracao.sql`](sqlite/r05_gini_concentracao.sql); grão grupo × integrante | atendido com ressalva | Mede concentração do registro, não quem trabalhou; o responsável no quadro nem sempre é quem executou; registro sem dono vira faixa possível. Não foi lida por ninguém de fora. |
| R06 | Os cartões de cada tipo de tarefa do grupo passam pelos 7 integrantes ou ficam com poucos? | Propor ao grupo rodízio entre os eixos | Diz qual eixo está mais concentrado e em quantos integrantes passou, abre os cartões do eixo e diz que a tela mede alocação, não competência, e que a pergunta vai ao grupo | [R06](dashboard/r06_eixos_de_tarefa.html) · "Como os cartões de cada eixo se dividem entre os 7 integrantes" e "Cartões do grupo" | `cartoes` (`rotulos`, `responsaveis_ids`, `sprint`), `kanban_eventos`, `pessoas`; [`r06_divisao_do_eixo.sql`](sqlite/r06_divisao_do_eixo.sql); grão grupo × eixo | atendido com ressalva | O rótulo é posto pelo próprio grupo e o eixo Negócio não compara grupos (G03 não usa). Reformulado em 13/10; a versão nova ainda não foi relida por alguém de fora. |
| L1 | O grupo está aprendendo? | — | — | [Requisitos.MD · Lacunas do recorte](requisitos/Requisitos.MD#lacunas-do-recorte); rodapé "O que esta tela não sustenta" | — | lacuna declarada | Não há nota, feedback nem resultado de aprendizagem no recorte; uma medida aproximada por volume seria veredito. |
| L2 | Quem se dedicou mais? | — | — | idem; R05 e R06 explicam que não respondem | — | lacuna declarada | Registro não mede dedicação; `peso` vazio em 100% e `tempo_gasto_s` sempre 0; a unidade é o grupo. |
| L3 | Este cartão está atrasado? | — | — | idem; R04 diz "levou mais que o planejado" | — | lacuna declarada | Só 24 de 1.238 cartões têm prazo, e 10 de 15 sprints não têm datas. |

### Condições comuns a todos os requisitos

| id | localização | rastreabilidade (do número à linha) | declaração (grão, unidade, período, filtro, fonte na tela) | acionabilidade (a leitora diz o que faria) |
| --- | --- | --- | --- | --- |
| VG | ✓ quadros nomeados | ✓ cada célula abre a tela do requisito no grupo | ✓ faixa de contexto e "Como ler" | verbalizada na T08, na versão anterior ("teria que começar pelo grupo um"), com a leitura de veredito que levou à revisão; versão nova sem reteste |
| R01 | ✓ | ✓ lista "Commits do dia"; gerador confere dia a dia contra o t04 | ✓ título com grupo e janela; linha de recorte com merges e não atribuídos | parcial na T08 |
| R02 | ✓ | ✓ lista "Cartões da etapa"; gerador confere contra `r02_acumulo_por_etapa.sql` | ✓ | verbalizada na T08 (escolha pelo limite de 48 h) |
| R03 | ✓ | ✓ cada percentual com a contagem; gerador reconta direto das tabelas | ✓ | não verificada |
| R04 | ✓ | ✓ "Cartão aberto" com os commits ligados; vínculo `#N` refeito em Python | ✓ | parcial na T08 (entendeu com os textos de apoio) |
| R05 | ✓ | ✓ tabela "O mesmo grupo, outras medidas"; Gini refeito em Python | ✓ | não verificada |
| R06 | ✓ | ✓ "Cartões do grupo" filtrável por eixo e integrante; divisão refeita dos rótulos crus | ✓ | não verificada (versão nova) |

## 5. Decisões

O dashboard deve tornar visível a distância entre uma leitura intuitiva e o que os dados autorizam afirmar. Cada visualização explicita período, unidade, fonte, regra de cálculo, premissas e lacunas junto ao indicador relevante. Números incompletos ou derivados não devem parecer fatos confirmados.

**Afirmação máxima do R01:** "Exibe apenas commits autorais registrados no Git para o grupo e período selecionados; não mede esforço fora do Git. Um dia sem commit não significa um dia sem trabalho."

| divergência | leitura do usuário | o que o dado autoriza | suporte na tela |
| --- | --- | --- | --- |
| D1 · grão | "O G01 fez 662 commits." | 404 commits autorais; 197 são merges e 71 são histórico herdado | linha de recorte abaixo do título do R01 |
| D2 · causalidade | "O G03 parou de trabalhar de 14 a 21/06." | não houve commit autoral nesses 8 dias, e nada além disso | frase de limite junto ao gráfico |
| D3 · janela | "O maior silêncio do G01 é de 16 dias." | depois de 26/06 o calendário acabou para os três | marco de 26/06; silêncios posteriores identificados |
| D4 · atribuição | "O G01-A17 fez 37 dos 49 commits do dia." | 27,5% dos commits do G01 não têm autor resolvido | selo "autoria não resolvida"; percentual junto ao gráfico |
| D5 · veredito (T08) | "o grupo um [...] é o que está assim, pior" | cada linha da visão geral é uma pergunta separada; a soma não tem sentido | visão geral revista: sem soma, sem cor de alerta, ◆ "maior valor da linha" |
| D6 · atribuição a pessoa (correção) | o R06 abria no integrante mais concentrado | a divisão de papéis é do grupo; o rótulo registra alocação | R06 refeito em torno da divisão de cada eixo no grupo |

O fluxo completo do R01, com as oito estações do ciclo da métrica, está em [`dashboard/05_fluxo_interacao_R01.md`](dashboard/05_fluxo_interacao_R01.md). As premissas de cada tela (limites, faixas, dias por tamanho, critério de integrante, eixos) estão no bloco "Premissas desta tela" e na linha "Premissas do grupo" de cada requisito; todas aguardam confirmação.

## 6. Auditoria e teste com usuário

O registro completo da auditoria, com os achados da crítica da Aula 07, do teste T08, da correção do professor e de uma passada pelas dez heurísticas e pelos sete vieses, com severidade, correção e reteste, está em [docs/06_auditoria_heuristica_e_vieses.md](docs/06_auditoria_heuristica_e_vieses.md). Resumo dos graves:

| achado | severidade | correção | estado |
| --- | :---: | --- | --- |
| R06 abria no integrante mais concentrado e decidia sobre a pessoa | 3 | R06 refeito em torno do grupo | corrigido, reteste pendente |
| Visão geral lida como veredito (cor, ▲, soma de marcas) | 3 | sem soma, sem cor de alerta, título por assunto | corrigido, reteste pendente |
| Maior silêncio caía depois do fim do calendário | 3 | marco de 26/06 e janela fixa | corrigido; reteste parcial |
| Somar commits com cartões | 3 | vínculo por `#N` e peso pelo tamanho | corrigido |

### Teste de leitura em voz alta (T08)

Foi realizado um teste de leitura em voz alta com um usuário externo, simulando o papel da orientadora pedagógica, sobre a versão entregue em 10/10. As observações abaixo consolidam as falas e dificuldades registradas durante a navegação. As citações foram mantidas conforme as anotações da entrevista.

#### Falas reais

- **Identificação dos grupos:** "Aqui o G01, G02, G03. Sim, está claro." O usuário localizou os três grupos sem dificuldade.
- **Escolha de onde intervir:** "O grupo um está em vermelho [...] Cartões que passaram de 48 horas em alguma etapa do quadro [...] então eu como orientadora teria que começar pelo grupo um que é o que está assim, pior." A escolha foi imediata e orientada pelo destaque visual e pela descrição do limite de 48 horas.
- **Cores e indicadores visuais:** "Ajuda porque o vermelho eu vejo que está fora e o azul dentro. [...] as setinhas para cima e para baixo, isso te ajuda também." As cores e setas facilitaram a comparação dos resultados.
- **Gráfico de barras por etapa:** o usuário entendeu rapidamente a distribuição do tempo nas etapas e identificou que a maioria dos cartões permanece até 48 horas.
- **Gráfico de dispersão:** o usuário inicialmente achou a visualização pouco familiar, mas relatou que as descrições de apoio foram fundamentais para compreender seu sentido e interpretá-la na prática.
- **Gráfico de commits:** compreendeu a evolução temporal representada pelas barras, mas não inferiu sozinho o significado pedagógico dos intervalos de silêncio superiores a três dias.

#### Divergências encontradas

- **Cor como atalho para decisão:** o vermelho ajudou a localizar rapidamente o grupo destacado, mas a fala "o que está assim, pior" mostra que a codificação visual pode ser entendida como uma avaliação global. O destaque se refere ao critério exibido, não a uma conclusão geral sobre o grupo.
- **Dispersão pouco familiar:** sem as descrições de apoio, o usuário teve dificuldade inicial para interpretar o gráfico. A visualização não se explica sozinha para este perfil de leitor.
- **Silêncio em commits sem significado pedagógico evidente:** as barras mostram a evolução temporal, mas o usuário não conectou espontaneamente um intervalo acima de três dias à pergunta de acompanhamento adequada. O gráfico não deve sugerir que o grupo deixou de trabalhar.
- **Siglas nos gráficos de perfil:** "cod", "des", "doc" e "neg" não fazem parte do vocabulário cotidiano da pessoa entrevistada e dificultaram a leitura prática.

#### Ajustes aplicados depois da entrevista

- 09/10: a tela R06 passou a exibir, junto aos radares, a tradução das siglas: **Cód = Código**, **Des = Design**, **Doc = Documentação** e **Neg = Negócio**.
- 13/10, depois da correção: a visão geral deixou de somar marcas e de usar cor de alerta, e o título passou a sugerir um assunto para cada grupo (divergência "cor como atalho para decisão"); o roteiro de cada grupo traz o que observar na sprint seguinte (divergência do silêncio sem significado pedagógico).

**Resultado positivo registrado:** embora o gráfico de dispersão tenha sido inicialmente pouco familiar, a usuária informou que as descrições de apoio foram fundamentais.

## 7. Painel

### Plataforma e motivo

O painel é **HTML estático gerado em Python a partir do SQLite** (`dashboard/gerar_*.py` sobre `sqlite/dados.db`), e não uma coleção no Metabase nem um protótipo HTML ligado ao Supabase, que eram as duas plataformas pedidas. A escolha foi do grupo e tem custo; os motivos:

- **O professor consegue abrir com o que foi entregue.** Cada tela é um arquivo só, sem servidor, login nem internet; abre do repositório clonado. Não depende de uma instância do Metabase que não sobrevive ao semestre nem de credenciais de um projeto Supabase.
- **Cada número volta à origem dentro do repositório.** Toda tela é recalculada pelas consultas de `sqlite/`, e o gerador reconta em Python e para sem gravar se divergir (tabela "Conferência antes de gravar" em [`dashboard/README.md`](dashboard/README.md)). Quem quiser conferir roda o mesmo `.sql` em `sqlite/dados.db`.
- **O protótipo já respondia às perguntas de decisão** (a Aula 07 previa mantê-lo como painel final), e as exigências de leitura (versão em preto e branco, visão em tabela, lista que abre cada número, premissas na tela) foram feitas nele.

O que a escolha custa, e que o grupo assume: os dados são os CSVs da T28 (3 grupos), e não o recorte completo das 15 turmas; não há login nem controle de acesso por RLS; o painel não se atualiza sozinho, é preciso rodar os geradores. Os CSVs da T28 vêm da página pública do projeto, e nenhum arquivo do recorte completo entrou no repositório.

### Telas e ideia central

Uma página de abertura (a visão geral, o one-pager sugerido na Aula 07) e uma tela por requisito; cada tela tem versão em preto, branco e cinza (`_pb.html`), visão em tabela e o bloco "O que esta tela não sustenta". A sequência situação → evidência → decisão → limites e a ficha técnica do indicador de cada tela estão em [docs/07_narrativa.md](docs/07_narrativa.md).

> **Ideia central:** nos três grupos, o quadro trava na espera por revisão, e não na execução. Em todas as sprints, a etapa com mais cartões parados por mais de 48 h é Waiting Review no G01 (82 cartões), no G02 (134) e no G03 (95), contra 19, 2 e 2 em Doing.

### Como abrir cada número até a origem

1. Na visão geral, clique na célula: a tela do requisito abre já no grupo.
2. Na tela, clique na barra, no dia, na etapa ou no ponto: a lista abaixo mostra os registros que formam o número (commits do dia, cartões da etapa, commits ligados ao cartão, cartões do eixo).
3. O nome do `.sql` está na nota de origem de cada tela; rodar `py -3 sqlite/rodar_sql.py <arquivo>.sql` devolve o mesmo número em CSV.

### Como abrir o painel

Abra [`dashboard/visao_geral.html`](dashboard/visao_geral.html) no navegador; a faixa do topo leva às outras telas, sempre por endereço relativo. Para regenerar: `py -3 sqlite/csv_para_sqlite.py`, `py -3 sqlite/verificar.py` e os geradores na ordem de [`dashboard/README.md`](dashboard/README.md) (a visão geral por último).

## 8. Limitações

### Objeto de estudo

O painel observa rastros de processo registrados nas ferramentas pelos grupos G01, G02 e G03 para apoiar conversas da orientadora pedagógica. A unidade de análise é o **grupo**. O painel não avalia alunos, aprendizagem, competência, dedicação ou desempenho individual; identificadores pessoais são detalhes de rastreabilidade, não uma escala de avaliação.

### Limitações da base

- **Cobertura do trabalho:** a base contém commits, eventos Kanban, cartões, merge requests e cadastros. Estudo, reuniões, leitura, trabalho presencial, programação em dupla e alterações que não chegam ao Git não são observados. Ausência de registro não prova ausência de trabalho.
- **Prazos e calendário:** apenas 24 dos 1.238 cartões têm `prazo_em`; 10 das 15 sprints não têm datas, todas de G01 e G02. O calendário de G03 aplicado a esses grupos é premissa, não dado original. Portanto, a base não sustenta uma afirmação geral de atraso.
- **Esforço e duração:** `peso` está vazio em todos os cartões e `tempo_gasto_s` é zero em todos. Tempo entre criação/fechamento ou entre eventos mede tempo corrido, não horas trabalhadas.
- **Atribuição:** 552 dos 2.688 commits (20,5%) têm autoria sentinela `[externo]` ou `[bot]`. Responsável no cartão ou autoria registrada não prova quem executou o trabalho, especialmente em atividades colaborativas.
- **Rótulos e semântica:** os rótulos são definidos pelos grupos e variam entre eles; os eixos de tarefa são um mapeamento do projeto. Não há rótulo UX na base, e `DESIGN` é apenas o rótulo mais próximo. A coluna final observada do quadro é `Review`; não se presume que signifique `Done` ou trabalho validado.
- **Resultados pedagógicos:** não há notas, avaliações, feedback ou medidas diretas de aprendizagem. Nenhum indicador do painel deve ser apresentado como evidência de que um grupo aprendeu mais ou menos.
- **Extração:** método e data de extração dos CSVs não estão registrados. A data mais recente encontrada nos registros não equivale à data de extração.

### Lacunas de validação

A entrevista foi uma leitura qualitativa com um usuário externo simulando a orientadora, não uma amostra representativa. O roteiro formal do R01 não foi comprovado como concluído; as anotações não cobrem R03 e R05, casos sem dados ou auditoria da origem dos números. A legenda do R06, o R06 reformulado e a visão geral revista precisam de reteste. As premissas de negócio continuam sujeitas à confirmação do professor, conforme o catálogo em [`requisitos/Requisitos.MD`](requisitos/Requisitos.MD).

## 9. Recomendação

**Na próxima rodada de reuniões, a orientadora abre a conversa com cada grupo pelo fluxo de revisão do quadro (quem revisa e quanto tempo o cartão espera em Waiting Review), e, na sprint seguinte, acompanha no R02 a parte dos cartões que passa de 48 h nessa etapa.** Uma sprint só varia por acaso: se o número cair depois da conversa, isso é sinal para acompanhar, não prova de que foi a conversa.

## Anexos

### Registros das aulas

O índice dos registros das Aulas 01 a 07 e onde cada um está fica em [docs/README.md](docs/README.md).

### Organização do repositório

| Pasta | Conteúdo |
| --- | --- |
| [`docs/`](docs/README.md) | Registros das aulas: brief e qualidade, pipeline Excel → OLAP, auditoria heurística e de vieses, narrativa. |
| [`requisitos/`](requisitos/Requisitos.MD) | Requisitos R01–R06, visão geral, prioridade e lacunas do recorte. |
| [`vocabulario/`](vocabulario/t02_Vocabulario_do_Projeto.md) | Vocabulário T02 e distinção entre definições e premissas. |
| [`modelagem/`](modelagem/Contrato_de_dados.md) | Contrato dos CSVs, grãos, chaves, tipos e regras de junção. |
| [`csvs_originais/`](csvs_originais/) | Fontes originais da turma T28, preservadas sem edição. |
| [`sqlite/`](sqlite/README.md) | Carga SQLite, consultas SQL, view de tratamento T05 e resultados exportados. |
| [`dashboard/`](dashboard/README.md) | Geradores, modelos HTML, painéis e documentação de interação. |
| [`aula04_excel_olap/`](aula04_excel_olap/README.md) | Laboratório da Aula 04 (Olist): scripts do pipeline Excel → SQLite → DuckDB e os relatórios gerados. |
| [`amostra_10linhas/`](amostra_10linhas/README.md) | Amostras pequenas para inspecionar o formato dos CSVs. |
