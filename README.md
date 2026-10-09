# Dossiê Final — Data Visualization

**Equipe:** Dhyego, Thamyres e Augusto
**Projeto:** painel de apoio ao acompanhamento pedagógico de grupos no processo PBL.

Este dossiê consolida os requisitos, as decisões de tratamento e os limites de interpretação do projeto. Os CSVs originais são mantidos como fonte; regras derivadas e premissas permanecem identificadas para que uma leitura do painel possa ser auditada.

## 1. Visão Geral do Projeto

O projeto reúne uma visão geral e seis telas analíticas para apoiar conversas de acompanhamento pedagógico a partir dos registros disponíveis de quadro Kanban, commits e merge requests. O público principal é a **orientadora pedagógica**, que consulta o painel antes ou durante o planejamento de conversas com os grupos.

**Unidade de análise obrigatória: o grupo.** Os indicadores comparam ou descrevem G01, G02 e G03. Identificadores de pessoas podem aparecer em detalhes para explicar a origem de um registro, mas não transformam o painel em avaliação, ranking ou medida de desempenho individual. Registro em ferramenta não equivale a esforço, participação integral ou aprendizagem.

As telas cobrem ritmo de commits (R01), acúmulo por etapa (R02), cobertura dos registros (R03), tamanho planejado versus tempo decorrido (R04), concentração dos registros (R05) e distribuição por eixo de tarefa (R06). A visão geral resume esses requisitos sem criar uma métrica nova.

**Dashboard final:** [abrir a versão HTML local](dashboard/visao_geral.html).

## 2. Dicionário e Vocabulário

Os termos foram padronizados para separar o que as fontes efetivamente registram da interpretação de negócio adotada para construir as visualizações. A elicitação da cliente é uma fonte congelada: interpretações sem confirmação devem ser apresentadas como **Premissa do Grupo**, nunca atribuídas à cliente.

| Termo                            | Definição do dado                                                                                              | Interpretação e limite                                                                                                                                |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Entrega**                | Um cartão pode chegar à coluna final registrada; um MR pode ter`situacao = merged`. São sinais diferentes.  | Não comprovam, isoladamente, validade ou aceitação pedagógica do conteúdo.                                                                         |
| **Atraso**                 | Pode ser calculado somente onde existem prazo e datas aplicáveis; apenas 24 de 1.238 cartões têm`prazo_em`. | A definição de atraso depende de calendário e regra de negócio. O R04 diz “levou mais que o planejado”, não “atrasou”.                         |
| **Participação**         | Há rastros de commits, eventos Kanban e MRs, em grãos diferentes.                                              | São registros da plataforma; não medem presença, dedicação ou toda a colaboração.                                                                |
| **Revisão**               | O MR registra identificadores de revisores e contagem de comentários.                                           | Não comprova leitura criteriosa, aprovação ou autoria individual dos comentários.                                                                   |
| **Concluído**             | O estado do cartão ou do MR e os eventos registram estados operacionais.                                        | Estado final no sistema não garante que o trabalho foi realizado ou validado como esperado.                                                            |
| **Ativo**                  | `pessoas.situacao` está como `active` para os 83 perfis; pode-se também observar registros em um período. | O campo da origem não distingue engajamento. Ter registro não prova contribuição contínua.                                                         |
| **Automação / Bot**      | A autoria`[bot]` pode aparecer em commits; eventos podem trazer identificadores reconhecíveis.                | A classificação depende da informação disponível. Não se deve inferir que um registro é humano ou automatizado apenas pelo padrão de atividade. |
| **Tamanho vs. prioridade** | Rótulos como`SIZE_P` indicam uma categoria registrada; `P1` a `P8` são tokens de prioridade.             | Tamanho e prioridade são conceitos distintos. A equivalência de tamanho com complexidade ou dias é premissa, não medida observada.                  |

**Regra inegociável:** em todo artefato, tabela ou tela, manter separados **Definição do Dado** (o que a fonte registra) e **Premissa do Grupo** (interpretação, corte ou regra não confirmada). Campo vazio é ausência de valor, não autorização para completar por inferência.

## 3. Tratamento de Dados e Regras de Negócio

Os arquivos de `csvs_originais/` são preservados sem alteração. O banco SQLite reproduz as tabelas de origem; o tratamento analítico do Kanban é feito na view `t05_eventos_kanban`.

- **Duplicatas:** a view remove as 24 linhas integralmente duplicadas de `kanban_eventos.csv` para análise, reduzindo 13.194 registros a 13.170 eventos distintos. As linhas originais continuam preservadas na fonte e na tabela bruta do banco.
- **Campos vazios:** a carga converte campos vazios em `NULL`. Na classificação dos eventos, `coluna` vazia ou em branco é marcada como `DESCONHECIDO`; não é tratada como etapa nem rótulo.
- **Mudança de coluna versus marcação de rótulo:** quando `coluna` corresponde a uma coluna do `Scrum Board` do mesmo grupo, o evento é `MUDANCA_COLUNA`; quando não corresponde, é `MARCACAO_ROTULO`. Valores ausentes ficam separados como desconhecidos. Rótulos são normalizados e categorizados, distinguindo, por exemplo, tamanho de prioridade.
- **Flag `is_bot`:** a view deriva uma flag a partir de identificadores de evento que contêm marcadores reconhecíveis como `bot`, `automat`, `automation`, `pipeline` ou `runner`. É uma classificação operacional baseada no texto disponível, não uma prova universal de automação.
- **Duração:** eventos deduplicados de cada cartão são ordenados por instante e recebem uma sequência. `horas_ate_proximo_evento` calcula as horas entre o evento atual e o próximo evento do mesmo cartão; no último evento, sem próximo registro, o valor fica nulo. É tempo decorrido entre registros, não horas de trabalho.
- **Calendário de sprints:** as datas de G01 e G02 estão vazias na origem. Como **Premissa do Grupo**, o calendário preenchido de G03 é usado para classificar eventos dos três grupos. A origem do calendário aplicado é identificada na view; as datas atribuídas a G01 e G02 não são apresentadas como observações originais.
- **Datas:** timestamps são convertidos para `America/Sao_Paulo` na carga para permitir ordenação e agregação temporal consistentes.

O detalhamento técnico está em [`sqlite/t05_eventos_kanban.sql`](sqlite/t05_eventos_kanban.sql), [`sqlite/README.md`](sqlite/README.md) e [`modelagem/Contrato_de_dados.md`](modelagem/Contrato_de_dados.md).

## 4. Lista de Requisitos

O catálogo completo está em [`requisitos/Requisitos.MD`](requisitos/Requisitos.MD). Abaixo, um modelo preenchido para R01, com os seis campos exigidos:

### Exemplo — R01: Ritmo de registro ao longo dos dias

| Campo                         | Especificação                                                                                                                                                                                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Público**            | Orientadora pedagógica.                                                                                                                                                                                                                                                                   |
| **Decisão**            | Escolher com qual grupo abrir uma conversa sobre ritmo de trabalho e qual período investigar, sem tratar ausência de commit como ausência de trabalho.                                                                                                                                  |
| **Frequência**         | A cada sprint e antes de uma reunião de acompanhamento.                                                                                                                                                                                                                                   |
| **Critério de Aceite** | 1. Selecionar um grupo e um período. 2. Ler a quantidade de commits autorais por dia, incluindo dias sem registro como zero. 3. Abrir um dia e conferir os commits que compõem o total. 4. Explicar, sem ajuda, que a tela mostra registros no Git e não mede todo o trabalho do grupo. |
| **Evidência**          | `commits.csv`: `grupo`, `commit_id`, `autor_id`, `autorado_em`, `commitado_em` e `e_merge`; `grupos.csv`: `grupo` e `criado_em`, usados para excluir histórico anterior à criação do grupo. A chave analítica do commit é (`grupo`, `commit_id`).            |
| **Lacunas**             | Não mede esforço ou horas trabalhadas fora do Git, estudo, reuniões ou programação em dupla sem commit. Um dia sem commit não é um dia sem trabalho. Autoria não resolvida também limita leituras por pessoa.                                                                     |

## 5. Divergências e Suportes

O dashboard deve tornar visível a distância entre uma leitura intuitiva e o que os dados autorizam afirmar. Cada visualização precisa explicitar período, unidade, fonte, regra de cálculo, premissas e lacunas junto ao indicador relevante. Números incompletos ou derivados não devem parecer fatos confirmados.

**Afirmação Máxima do R01:** “Exibe apenas commits autorais registrados no Git para o grupo e período selecionados; não mede esforço fora do Git. Um dia sem commit não significa um dia sem trabalho.”

Suportes documentados incluem: excluir commits de merge e histórico herdado do template da contagem autoral; manter dias sem commit no eixo como zero; mostrar o marco de fim da Sprint 05 do G03 (26/06/2026) para contextualizar silêncios posteriores; sinalizar autoria não resolvida; e permitir abrir os registros que formam cada total. A visão geral marca leituras afetadas por baixa cobertura, e cada tela exibe suas premissas.

O fluxo, as divergências D1–D4 e os suportes do R01 estão em [`dashboard/05_fluxo_interacao_R01.md`](dashboard/05_fluxo_interacao_R01.md). A afirmação máxima deve ser adaptada para cada requisito, sem extrapolar o que sua fonte sustenta.

## 6. Testes de Leitura com Usuário Externo

Foi realizado um teste de leitura em voz alta com um usuário externo, simulando o papel da orientadora pedagógica. As observações abaixo consolidam as falas e dificuldades registradas durante a navegação. As citações foram mantidas conforme as anotações da entrevista.

### Falas Reais

- **Identificação dos grupos:** “Aqui o G01, G02, G03. Sim, está claro.” O usuário localizou os três grupos sem dificuldade.
- **Escolha de onde intervir:** “O grupo um está em vermelho [...] Cartões que passaram de 48 horas em alguma etapa do quadro [...] então eu como orientadora teria que começar pelo grupo um que é o que está assim, pior.” A escolha foi imediata e orientada pelo destaque visual e pela descrição do limite de 48 horas.
- **Cores e indicadores visuais:** “Ajuda porque o vermelho eu vejo que está fora e o azul dentro. [...] as setinhas para cima e para baixo, isso te ajuda também.” As cores e setas facilitaram a comparação dos resultados.
- **Gráfico de barras por etapa:** o usuário entendeu rapidamente a distribuição do tempo nas etapas e identificou que a maioria dos cartões permanece até 48 horas.
- **Gráfico de dispersão:** o usuário inicialmente achou a visualização pouco familiar, mas relatou que as descrições de apoio foram fundamentais para compreender seu sentido e interpretá-la na prática.
- **Gráfico de commits:** compreendeu a evolução temporal representada pelas barras, mas não inferiu sozinho o significado pedagógico dos intervalos de silêncio superiores a três dias.

### Divergências Encontradas

- **Cor como atalho para decisão:** o vermelho ajudou a localizar rapidamente o grupo destacado, mas a fala “o que está assim, pior” mostra que a codificação visual pode ser entendida como uma avaliação global. O destaque se refere ao critério exibido, não a uma conclusão geral sobre o grupo.
- **Dispersão pouco familiar:** sem as descrições de apoio, o usuário teve dificuldade inicial para interpretar o gráfico. A visualização não se explica sozinha para este perfil de leitor.
- **Silêncio em commits sem significado pedagógico evidente:** as barras mostram a evolução temporal, mas o usuário não conectou espontaneamente um intervalo acima de três dias à pergunta de acompanhamento adequada. O gráfico não deve sugerir que o grupo deixou de trabalhar.
- **Siglas nos gráficos de perfil:** “cod”, “des”, “doc” e “neg” não fazem parte do vocabulário cotidiano da pessoa entrevistada e dificultaram a leitura prática.

**Ajuste aplicado após a entrevista:** a tela R06 agora exibe, junto à legenda dos radares e antes dos gráficos de perfil, a tradução das siglas: **Cod = Código**, **Des = Design**, **Doc = Documentação** e **Neg = Negócio**. A alteração foi feita no modelo [`dashboard/r06_modelo.html`](dashboard/r06_modelo.html) e incorporada ao HTML gerado [`dashboard/r06_eixos_de_tarefa.html`](dashboard/r06_eixos_de_tarefa.html).

**Resultado positivo registrado:** embora o gráfico de dispersão tenha sido inicialmente pouco familiar, a usuária informou que as descrições de apoio foram fundamentais..

## 7. Organização do Repositório

O `README.md` está na raiz do projeto, ao lado das pastas abaixo. A estrutura atual não contém uma pasta `/docs`; os documentos de especificação estão organizados por assunto:

| Pasta                                                        | Conteúdo                                                                         |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| [`requisitos/`](requisitos/Requisitos.MD)                   | Requisitos R01–R06, visão geral e lacunas do recorte.                           |
| [`vocabulario/`](vocabulario/t02_Vocabulario_do_Projeto.md) | Vocabulário T02 e distinção entre definições e premissas.                    |
| [`modelagem/`](modelagem/Contrato_de_dados.md)              | Contrato dos CSVs, grãos, chaves, tipos e regras de junção.                    |
| [`csvs_originais/`](csvs_originais/)                        | Fontes originais, preservadas sem edição.                                       |
| [`sqlite/`](sqlite/README.md)                               | Carga SQLite, consultas SQL, view de tratamento T05 e resultados exportados.      |
| [`dashboard/`](dashboard/README.md)                         | Geradores, modelos HTML, painéis e documentação de interação e publicação. |
| [`amostra_10linhas/`](amostra_10linhas/README.md)           | Amostras pequenas para inspecionar o formato dos CSVs.                            |

No VS Code, abra esta pasta de projeto para navegar pelos documentos e scripts. No GitHub, a mesma organização relativa permite seguir os links deste dossiê e revisar as evidências junto ao código.

## Limitações e Lacunas do Projeto

### Objeto de Estudo

O painel observa rastros de processo registrados nas ferramentas pelos grupos G01, G02 e G03 para apoiar conversas da orientadora pedagógica. A unidade de análise é o **grupo**. O painel não avalia alunos, aprendizagem, competência, dedicação ou desempenho individual; identificadores pessoais são detalhes de rastreabilidade, não uma escala de avaliação.

### Limitações da Base

- **Cobertura do trabalho:** a base contém commits, eventos Kanban, cartões, merge requests e cadastros. Estudo, reuniões, leitura, trabalho presencial, programação em dupla e alterações que não chegam ao Git não são observados. Ausência de registro não prova ausência de trabalho.
- **Prazos e calendário:** apenas 24 dos 1.238 cartões têm `prazo_em`; 10 das 15 sprints não têm datas, todas de G01 e G02. O calendário de G03 aplicado a esses grupos é premissa, não dado original. Portanto, a base não sustenta uma afirmação geral de atraso.
- **Esforço e duração:** `peso` está vazio em todos os cartões e `tempo_gasto_s` é zero em todos. Tempo entre criação/fechamento ou entre eventos mede tempo corrido, não horas trabalhadas.
- **Atribuição:** 552 dos 2.688 commits (20,5%) têm autoria sentinela `[externo]` ou `[bot]`. Responsável no cartão ou autoria registrada não prova quem executou o trabalho, especialmente em atividades colaborativas.
- **Rótulos e semântica:** os rótulos são definidos pelos grupos e variam entre eles; os eixos de tarefa são um mapeamento do projeto. Não há rótulo UX na base, e `DESIGN` é apenas o rótulo mais próximo. A coluna final observada do quadro é `Review`; não se presume que signifique `Done` ou trabalho validado.
- **Resultados pedagógicos:** não há notas, avaliações, feedback ou medidas diretas de aprendizagem. Nenhum indicador do painel deve ser apresentado como evidência de que um grupo aprendeu mais ou menos.
- **Extração:** método e data de extração dos CSVs não estão registrados. A data mais recente encontrada nos registros não equivale à data de extração.

### Lacunas de Validação

A entrevista foi uma leitura qualitativa com um usuário externo simulando a orientadora, não uma amostra representativa. O roteiro formal do R01 não foi comprovado como concluído; as anotações não cobrem R03 e R05, casos sem dados ou auditoria da origem dos números. A legenda do R06 e os ajustes de linguagem/ênfase precisam de reteste. As premissas de negócio continuam sujeitas à confirmação do professor, conforme o catálogo em [`requisitos/Requisitos.MD`](requisitos/Requisitos.MD).
