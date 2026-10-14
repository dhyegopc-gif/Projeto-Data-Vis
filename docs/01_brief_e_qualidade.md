# 01 — Brief e qualidade dos dados

> Registro da Aula 01 (método C-D-P-V-D, gates Contexto e Dados, perfil de qualidade).
> **Escrito em 13/10/2026, depois da correção do professor (issue #1)**, que apontou a falta do brief de
> qualidade como documento próprio. O conteúdo já existia espalhado no repositório
> ([Contrato_de_dados.md](../modelagem/Contrato_de_dados.md), [vocabulário](../vocabulario/t02_Vocabulario_do_Projeto.md)
> e [Requisitos.MD](../requisitos/Requisitos.MD)); aqui ele segue o modelo da aula e cada medida foi
> recontada em `sqlite/dados.db` nesta data. Nenhum número novo de requisito foi criado.

Sequência do modelo: público → tarefa → decisão → consequência do erro → tabela/grão → regra → medida
observada → exceções → limitação → perguntas autorizadas → perguntas proibidas.

## 1. Contexto (gate C)

| item | o que vale neste projeto |
| --- | --- |
| **Público** | Vanessa, orientadora pedagógica do processo PBL. Conhece os grupos e o método, não conhece SQL nem o recorte. Tem cerca de 4 minutos antes de cada reunião de acompanhamento. |
| **Tarefa** | Preparar a reunião de acompanhamento com cada grupo: escolher por qual assunto abrir a conversa e o que perguntar. |
| **Decisão** | Que pergunta levar a cada grupo (ritmo de registro, acúmulo no quadro, divisão do trabalho, estimativa de tamanho), e quando pedir antes que o grupo corrija a forma de registrar. |
| **Consequência do erro** | Uma conversa de cobrança com um grupo que trabalhou sem deixar rastro (programação em dupla, estudo, reunião), ou uma conclusão sobre uma pessoa a partir de um campo incompleto. A decisão recai sobre estudantes reais em formação. |
| **Unidade de análise** | O grupo. O integrante aparece só como parte da distribuição interna do grupo, nunca como sujeito de comparação. |

## 2. Dados (gate D): tabela, grão e perfil

Fonte: os 8 CSVs da turma T28 publicados na página do projeto, em [`csvs_originais/`](../csvs_originais/),
preservados sem edição e carregados em `sqlite/dados.db` (a carga converte todo instante para
`America/Sao_Paulo`; [`sqlite/verificar.py`](../sqlite/verificar.py) confere o banco contra os CSVs, valor a valor).

| tabela | um registro é | registros | período coberto |
| --- | --- | ---: | --- |
| `grupos` | um grupo | 3 | criados em 22/04/2026; última atividade até 07/08/2026 (G02) |
| `pessoas` | uma pessoa vinculada a um grupo, com papel | 83 | — |
| `sprints` | uma sprint de um grupo | 15 | datas só no G03 (5 de 15) |
| `quadro_colunas` | uma coluna do Scrum Board de um grupo | 12 | — |
| `commits` | um commit, chave (`grupo`, `commit_id`) | 2.688 | 08/04/2022 a 13/07/2026 (o que vem antes de 22/04/2026 é histórico herdado do template) |
| `merge_requests` | um MR, chave (`grupo`, `mr_numero`) | 540 | criados de 23/04 a 26/06/2026 |
| `cartoes` | um cartão, chave (`grupo`, `cartao_numero`) | 1.238 | criados de 22/04 a 26/06/2026; fechados até 14/07/2026 |
| `kanban_eventos` | a aplicação ou remoção de um rótulo ou coluna num cartão; sem chave natural | 13.194 | 22/04 a 14/07/2026 |

Data de extração: **não registrada** em nenhum arquivo. Os CSVs entraram no repositório em 18/09/2026;
o registro mais recente do conjunto é de 07/08/2026. O recorte é uma fotografia: nada posterior a ela existe.

### Perfil pelas dimensões da aula (recorte da ISO/IEC 25012)

| dimensão | pergunta operacional | evidência no recorte |
| --- | --- | --- |
| Completude | Que valor falta e qual processo explica a ausência? | `peso` vazio em 100% dos cartões; `tempo_gasto_s` sempre 0; `tempo_estimado_s` 0 em 1.221 de 1.238; `prazo_em` em só 24 cartões (1,9%); datas de sprint vazias em 10 de 15 (todas de G01 e G02); `revisores_ids` em 417 de 540 MRs (77,2%) |
| Consistência | As regras concordam entre tabelas? | cartão `closed` ⇔ `fechado_em` preenchido em 1.174 de 1.174; MR `merged` ⇔ `merged_em` em 500 de 500; nenhum cartão fechado antes de criado; nenhum commit com `commitado_em` antes de `autorado_em`; 36 eventos de Kanban triplicados (12 eventos, 24 linhas a mais) |
| Atualidade | O período ainda serve à decisão? | serve para conversar sobre o módulo encerrado (Sprint 05 do G03 termina em 26/06/2026); não serve para "esta semana", porque a extração tem data desconhecida |
| Credibilidade | A fonte é plausível? | 411 cartões fechados em lote (5 ou mais no mesmo minuto), o que pode ser arrumação do quadro e não fim do trabalho; 213 commits herdados do repositório-template, idênticos nos 3 grupos |
| Rastreabilidade | Outra pessoa consegue refazer o número? | toda consulta está em `sqlite/*.sql`; cada gerador de tela reconta em Python e para se divergir |
| Compreensibilidade | Nome, unidade e semântica estão claros? | `kanban_eventos.coluna` mistura coluna do quadro e rótulo (9.052 movimentos, 4.106 rótulos); timestamps em três grafias de fuso; `*_ids` têm nome plural e sempre um valor |
| Confidencialidade | O que não pode sair? | os dados são pseudonimizados (`G01-A13`) e só a turma T28 está no repositório; o recorte completo das 15 turmas (`projeto_pbl_completo.zip`) não foi usado e não entra no repositório |

## 3. Regras testáveis

Cada regra tem escopo, condição, medida, tolerância e ação, como pede a aula. A medida é a observada em 13/10/2026.

| # | regra (linguagem de negócio) | medida observada | tolerância | classificação da violação | ação |
| --- | --- | --- | --- | --- | --- |
| Q1 | Todo commit contado tem autoria que casa com uma pessoa do cadastro | 2.136 de 2.688 (79,5%); 552 `[externo]` ou `[bot]` | 80% | ausência esperada (e-mail de cliente git fora da conta institucional) | sinalizar: faixa de autoria não resolvida no R01 e no R03; nenhuma tela ordena pessoas por commit |
| Q2 | Todo cartão `closed` tem `fechado_em` | 1.174 de 1.174 | 100% | — | aceitar |
| Q3 | Toda sprint tem início e prazo | 5 de 15 | 100% | estado do processo (G01 e G02 não preencheram) | sinalizar: marco de 26/06 do G03 aplicado aos três como premissa declarada |
| Q4 | Evento de Kanban não se repete | 13.170 distintos em 13.194 | 0 repetido | defeito da extração | excluir as 24 linhas repetidas na view `t05_eventos_kanban`, sem tocar no CSV |
| Q5 | Commit autoral é posterior à criação do grupo e não é merge | 1.743 de 2.688 | — | histórico herdado (213) e merges (762) são outra coisa, não defeito | excluir da contagem e declarar na tela (D1 do R01) |
| Q6 | Instante comparável entre arquivos | 2.144 commits em `-03:00` e 544 em `+00:00` | uma grafia | ausência de padrão na exportação | converter tudo para `America/Sao_Paulo` na carga; `verificar.py` confere o instante |
| Q7 | MR tem revisor designado | 417 de 540 (77,2%); 24% no G01 | 80% | estado do processo | sinalizar no R03 e na leitura do R02 (espera em Waiting Review) |
| Q8 | Cartão tem tamanho para comparar com o realizado | 1.159 de 1.238 (93,6%) | 80% | — | aceitar; cartões sem tamanho ficam fora do R04 e declarados |

## 4. Limitações

- Registro não é trabalho: estudo, reunião, programação em dupla e código descartado não aparecem.
- Não há diff nem texto de revisão: nada sobre qualidade do código ou sobre revisão criteriosa.
- Não há nota, feedback ou resultado de aprendizagem.
- Esforço e prazo não são observáveis (`peso` e `tempo_gasto_s` sem informação; 24 cartões com prazo).
- A data de extração é desconhecida.

## 5. Perguntas de negócio

As perguntas com os cinco elementos da aula (métrica, recorte, período, filtro, decisão). As seis primeiras
viraram os requisitos R01 a R06; as quatro últimas o recorte não sustenta, e ficaram registradas como lacuna.

| # | pergunta | métrica | recorte | período | filtro | decisão | respondível? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | Em quais dias o registro de commits do grupo se concentra, e há silêncio prolongado? | commits autorais por dia | grupo | 23/04 a 13/07/2026, por sprint | sem merge e sem histórico herdado | com qual grupo falar de ritmo e sobre qual período | sim → **R01** |
| P2 | Em qual etapa do quadro os cartões se acumulam? | cartões acima de 48 h na etapa | grupo × etapa | por sprint | etapas do Scrum Board | o que perguntar: espera por revisão ou execução | sim, com premissa → **R02** |
| P3 | O registro do grupo sustenta as outras leituras? | % de preenchimento por campo | grupo × campo | módulo inteiro | campos usados pelas telas | levar a leitura à conversa ou pedir correção do registro | sim → **R03** |
| P4 | Os cartões levam o tempo que o tamanho prometia? | realizado ÷ planejado | grupo × tamanho | por sprint | cartões fechados com tamanho | sobre quais cartões ou tamanhos perguntar | sim, com premissa → **R04** |
| P5 | O trabalho registrado está distribuído ou concentrado? | Gini dos dias planejados concluídos | grupo | por sprint | 7 integrantes | abrir ou não a conversa sobre divisão do trabalho | sim, com premissa → **R05** |
| P6 | Os tipos de tarefa passam pelos integrantes ou ficam com poucos? | parte dos 2 integrantes com mais cartões no eixo | grupo × eixo | por sprint | cartões com eixo dos integrantes | propor rodízio ao grupo | sim, com premissa → **R06** |
| P7 | O grupo está aprendendo? | — | — | — | — | — | **não**: não há nota, feedback nem resultado de aprendizagem |
| P8 | Quem se dedicou mais? | — | — | — | — | — | **não**: registro não mede dedicação; `peso` e `tempo_gasto_s` sem informação; a unidade é o grupo |
| P9 | Este cartão está atrasado? | — | — | — | — | — | **não**: só 24 cartões têm prazo e 10 de 15 sprints não têm datas |
| P10 | A revisão de código foi criteriosa? | — | — | — | — | — | **não**: o recorte traz revisor e contagem de comentários, mas não o texto da revisão nem o diff |

**Perguntas autorizadas**: P1 a P6, cada uma com as premissas declaradas na própria tela.
**Perguntas proibidas** (o painel não pode parecer respondê-las): P7 a P10, e qualquer ordenação de pessoas.
