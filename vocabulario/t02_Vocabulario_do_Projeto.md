# Vocabulário do Projeto

## Critério de leitura

A entrevista com a professora/orientadora é uma **fonte congelada**: não há nova validação direta disponível. Este documento não cria falas nem atribui à cliente definições que não estejam explicitamente registradas na elicitação. Toda interpretação sem confirmação explícita está identificada como **Premissa do Grupo**.

Cada termo separa:

- **Definição do Dado:** o que as fontes registram, incluindo grão e campos relevantes.
- **Definição da Cliente / Premissa do Grupo:** o significado de negócio usado no projeto. Quando não há confirmação explícita na fonte congelada, é uma **Premissa do Grupo**, não uma declaração atribuída à cliente.
- **Status e Classificação:** identifica explicitamente o que é **Definição do Dado** e o que é **Premissa do Grupo**.

Os arquivos CSV são as fontes descritas abaixo. Nomes de campos são apresentados como aparecem nas fontes; a camada SQLite pode expô-los em tabelas ou colunas derivadas.

## 1. Entrega

**Definição do Dado**  
Há dois sinais observáveis, que não devem ser tratados como equivalentes nem presumidos como vinculados entre si:

- Em `kanban_eventos.csv`, cada registro representa um evento de quadro ou de rótulo; `grupo`, `cartao_numero`, `acao`, `coluna`, `pessoa_id` e `ocorrido_em` descrevem o evento. No conjunto analisado, a coluna final configurada no quadro é `Review`; a fonte permite identificar a chegada a essa coluna, mas não permite afirmar que ela equivale a `Done` ou a uma entrega validada.
- Em `merge_requests.csv`, cada registro representa um Merge Request por grupo e número (`grupo`, `mr_numero`); `situacao` e `merged_em` permitem identificar um MR integrado (`situacao = merged`).

**Definição da Cliente / Premissa do Grupo**  
Para a análise, entrega significa trabalho de conteúdo válido, produzido e validado, com contribuição real de código ou documentação. Alterações periféricas, como formatação de texto, ou movimentação de cartão sem commit associado, não bastam para caracterizar entrega. Esta interpretação é **Premissa do Grupo**; os sinais disponíveis, isoladamente, não comprovam validade ou conteúdo.

**Status e Classificação**  
Os eventos de quadro e o estado de integração do MR são **Definição do Dado**. O critério de trabalho válido e a exclusão de alterações periféricas são **Premissa do Grupo**. No contrato local, a coluna de maior posição está denominada `Review`; portanto, confirmar a equivalência com `Done` exige o mapeamento adotado pelo projeto, não uma suposição sobre o rótulo.

## 2. Atraso

**Definição do Dado**  
Em `cartoes.csv`, cada registro representa um cartão por grupo e número. `prazo_em`, `situacao` e `fechado_em` permitem identificar cartão não concluído cujo prazo é anterior à data de referência da análise. Apenas 24 cartões têm `prazo_em`; sem prazo registrado, o atraso por esse critério não pode ser calculado. Em `sprints.csv`, cada registro representa uma sprint de um grupo, com `sprint`, `inicio_em` e `prazo_em`.

**Definição da Cliente / Premissa do Grupo**  
Para a análise, considera-se atraso uma entrega realizada após o encerramento da Sprint. Como `inicio_em` e `prazo_em` estão vazios para G01 e G02, o grupo assume para esses grupos o calendário quinzenal padrão de cinco sprints do G03, em um projeto de dez semanas. A imputação deve permanecer identificada como **Premissa do Grupo**, e não como data original observada.

**Status e Classificação**  
O estado do cartão, o prazo preenchido e as datas de sprint informadas são **Definição do Dado**. O calendário imputado de G01 e G02 e a interpretação de entrega posterior ao fim da Sprint são **Premissa do Grupo**. Ausência de prazo não equivale a atraso.

## 3. Participação / Colaboração

**Definição do Dado**  
O dado registra rastros versionados em diferentes grãos: um commit por registro em `commits.csv` (`grupo`, `commit_id`, `autor_id`, `autorado_em`); um MR por registro em `merge_requests.csv` (`grupo`, `mr_numero`, `revisores_ids`, `comentarios`); e um evento por registro em `kanban_eventos.csv` (`grupo`, `cartao_numero`, `pessoa_id`, `acao`, `ocorrido_em`). `merge_requests.csv` contém contagem de comentários e identificadores de revisores, mas não identifica a autoria individual de cada comentário.

**Definição da Cliente / Premissa do Grupo**  
Participação ou colaboração é interpretada como engajamento ativo do estudante nas frentes de trabalho. **Lacuna:** os dados medem somente rastros versionados disponíveis no GitLab. Não medem estudo individual, leituras, reuniões presenciais, conversas fora da plataforma nem programação em dupla no mesmo teclado. Assim, ausência de registro não prova ausência de participação.

**Status e Classificação**  
Autoria de commits e eventos e os campos de revisores/contagem de comentários são **Definição do Dado**. Engajamento ativo é **Premissa do Grupo**. Atribuição de comentários individuais não pode ser concluída a partir da estrutura descrita de `merge_requests.csv`.

## 4. Revisão de Código

**Definição do Dado**  
Em `merge_requests.csv`, cada registro representa um MR por grupo e número. `revisores_ids`, `comentarios`, `situacao` e `merged_em` registram revisores associados, quantidade de comentários e desfecho de integração. A fonte descrita não contém o conteúdo nem a autoria individual dos comentários, tampouco um campo específico de aprovação.

**Definição da Cliente / Premissa do Grupo**  
Revisão de código é interpretada como leitura, discussão do conteúdo e validação criteriosa do código por um colega da equipe antes do merge. Essa interpretação é **Premissa do Grupo**: a presença de revisor ou de comentários não comprova, por si só, que a revisão foi criteriosa.

**Status e Classificação**  
Os identificadores de revisores, a contagem de comentários e o estado do MR são **Definição do Dado**. O processo de leitura, discussão e validação criteriosa é **Premissa do Grupo**. Não inferir aprovação individual ou qualidade da revisão a partir de campos que não a registram.

## 5. Concluído

**Definição do Dado**  
`quadro_colunas.csv` tem um registro por coluna de quadro e grupo, com `grupo`, `quadro`, `coluna` e `posicao`. `kanban_eventos.csv` registra eventos por cartão, ação, coluna e instante. No conjunto analisado, a coluna de maior posição é `Review`; é possível identificar essa posição final configurada, mas não renomeá-la como `Done` nem concluir que houve validação do trabalho.

**Definição da Cliente / Premissa do Grupo**  
Concluído é interpretado como atividade finalizada pelo aluno. Mover um cartão para a coluna final não garante que o trabalho foi realizado. Ausência de commits ou de outras evidências vinculadas ao cartão no período é um indicativo de tarefa sem evidência, não prova definitiva de que nada foi feito. Esta leitura é **Premissa do Grupo**.

**Status e Classificação**  
A coluna e a posição configuradas, bem como os eventos registrados, são **Definição do Dado**. Considerar a tarefa finalizada e interpretar falta de evidência como alerta pedagógico são **Premissa do Grupo**. No contrato local, as colunas são `Backlog`, `Doing`, `Waiting Review` e `Review`; `Review` é a coluna de maior posição documentada e não deve ser renomeada implicitamente para `Done`.

## 6. Ativo

**Definição do Dado**  
No período selecionado, considera-se ativo o estudante com pelo menos um registro e autoria resolvida em `commits.csv` ou `kanban_eventos.csv`. Em commits, os campos relevantes incluem `autor_id` e `autorado_em`; em eventos Kanban, `pessoa_id` e `ocorrido_em`. Os registros têm, respectivamente, grão de commit e grão de evento.

**Definição da Cliente / Premissa do Grupo**  
Ativo é interpretado como integrante contribuindo ativa e continuadamente com a equipe. A existência de ao menos um registro no período não demonstra, por si só, continuidade. Essa leitura mais ampla é **Premissa do Grupo**.

**Status e Classificação**  
A existência de registro, sua autoria resolvida e sua data são **Definição do Dado**. Continuidade e contribuição ativa são **Premissa do Grupo**; o indicador operacional mínimo é presença de pelo menos um registro no período.

## 7. Automação / Bot

**Definição do Dado**  
Em `commits.csv`, cada registro representa um commit e `autor_id` pode identificar a autoria sentinela `[bot]`. Em `kanban_eventos.csv`, cada registro representa um evento e `pessoa_id` identifica a pessoa registrada. Classificar um evento ou commit como automatizado depende de a identidade ou o tipo de ação automática estar explicitamente identificável na fonte; não se deve inferir bot apenas pelo padrão da atividade.

**Definição da Cliente / Premissa do Grupo**  
Bot/automação significa ação gerada por script ou robô, sem esforço humano direto. O filtro **Com Bot / Sem Bot** foi considerado inicialmente, mas fica fora do escopo da versão atual: a classificação não é uniforme entre as fontes nem constitui um dos seis requisitos de tela. Esta decisão de escopo é do grupo, não uma definição confirmada pela cliente. Se o professor estabelecer o filtro como obrigatório, o escopo deverá ser reaberto e a regra definida por fonte antes da implementação.

**Status e Classificação**  
O identificador `[bot]` em autoria de commit é **Definição do Dado**. A flag `is_bot` da T05 é derivada de marcadores reconhecíveis no identificador de pessoa de evento Kanban; não classifica todos os fatos do projeto. O filtro não está implementado nos dashboards e está fora do escopo desta versão por decisão do grupo. Identidade ausente ou não reconhecida permanece não classificada, nunca presumida humana.

## 8. Tamanho do Cartão (Size) e Prioridade

**Definição do Dado**  
Os rótulos aparecem em listas associadas a cartões e MRs (`cartoes.csv.rotulos`, `merge_requests.csv.rotulos`) e como eventos de adição/remoção em `kanban_eventos.csv`. O evento registra uma ação e um rótulo/coluna, não uma medida direta do trabalho realizado. Rótulos documentados incluem `SIZE_P`, `SIZE_M` e `P1` a `P8`.

**Definição da Cliente / Premissa do Grupo**  
Size é interpretado como complexidade da tarefa e relacionado ao volume esperado de commits; prioridade é uma classificação distinta. Essa relação com complexidade e volume esperado é **Premissa do Grupo**, não medida observada diretamente.

**Status e Classificação**  
O rótulo registrado é **Definição do Dado**. Sua interpretação como tamanho ou prioridade é **Premissa do Grupo**. Regra obrigatória de tratamento: `P` isolado ou `SIZE_P` significa tamanho pequeno; `P1` a `P8` significam prioridade. Não agrupar `P1`–`P8` como tamanho por Regex. A normalização deve distinguir o token `P` isolado dos rótulos com sufixo numérico.

## 9. Eixos de Aprendizagem / Perfil do Aluno

**Definição do Dado**  
As fontes registram rótulos ligados a cartões e MRs. É possível contar e distribuir os rótulos identificados como eixos (por exemplo, UX, Negócio e Liderança) por grupo ou Sprint, desde que o rótulo e o período possam ser associados. O grão original permanece o cartão, o MR ou o evento de rótulo; uma contagem deve respeitar esse grão e evitar duplicações.

**Definição da Cliente / Premissa do Grupo**  
Os eixos são interpretados como um mapeamento de como competências do curso de Engenharia de Software estão sendo desenvolvidas no grupo ao longo das Sprints. A distribuição de rótulos é um indicador indireto e não comprova, isoladamente, domínio ou desenvolvimento individual do aluno. Esta interpretação é **Premissa do Grupo**.

**Status e Classificação**  
A presença e a distribuição dos rótulos nas fontes são **Definição do Dado**. A correspondência dos rótulos a eixos do curso e sua leitura como perfil ou desenvolvimento de aprendizagem são **Premissa do Grupo**.

## 10. Tempo Realizado do Cartão (Planejado × Realizado)

**Definição do Dado**  
`cartoes.csv` registra `criado_em` e `fechado_em` de cada cartão, e o tamanho aparece como rótulo (seção 8). A diferença entre as duas datas é tempo corrido: inclui noites, fins de semana e a espera no Backlog antes de alguém pegar o cartão. O commit se liga ao cartão quando cita `#N` no título (ou na mensagem, se o título não cita número), com N igual a um cartão do mesmo grupo; 83,2% dos commits autorais fazem isso.

**Definição da Cliente / Premissa do Grupo**  
Cada tamanho equivale a um número de dias planejados: PP 0,25, P 0,5, M 1, G 3 e GG 5. O cartão "levou mais que o planejado" quando o tempo realizado passa desses dias. A tabela vem do exemplo do professor e é **Premissa do Grupo**; a cliente não a definiu.

**Status e Classificação**  
As datas, o rótulo de tamanho e a citação `#N` são **Definição do Dado**. A equivalência tamanho → dias e a leitura "levou mais que o planejado" são **Premissa do Grupo**. Não usar "atraso": não há prazo combinado (seção 2), e o tempo corrido não é tempo de trabalho. Tela: R04.

## 11. Concentração do Trabalho Registrado (Índice de Gini)

**Definição do Dado**  
Cada registro com dono identificado (responsável por cartão fechado, autor de commit ou de MR) pode ser somado por pessoa. O índice de Gini resume a distribuição dessas somas entre os integrantes: 0 quando todos têm a mesma parte, (n − 1)/n quando uma pessoa tem tudo (0,857 com 7 integrantes). Registros de `[externo]`, `[bot]`, sem responsável ou de pessoa que não é integrante do grupo (de outro grupo, ou do cadastro sem movimento no quadro) não têm dono no índice e ficam fora dele.

**Definição da Cliente / Premissa do Grupo**  
Integrante é a pessoa do cadastro do grupo com pelo menos um evento no quadro do próprio grupo (7 em cada grupo). A medida principal pesa o cartão concluído pelos dias planejados do tamanho (seção 10). As faixas de leitura (até 0,2 distribuído, até 0,4 moderado, acima disso concentrado) orientam a conversa e não são régua oficial. Tudo isso é **Premissa do Grupo**.

**Status e Classificação**  
As somas por pessoa são **Definição do Dado**. O critério de integrante, o peso por tamanho e as faixas de leitura são **Premissa do Grupo**. O índice mede concentração do registro, não dedicação nem desempenho individual, e não serve para ordenar alunos. Tela: R05.

## Limites de interpretação

- Um registro representa evidência na plataforma, não uma avaliação completa do esforço ou da aprendizagem.
- Datas ausentes, identidades não resolvidas e rótulos ambíguos devem permanecer explícitos; não devem ser preenchidos silenciosamente como fatos.
- Indicadores derivados devem preservar o grão da fonte e distinguir valores observados de valores imputados ou interpretações do grupo.