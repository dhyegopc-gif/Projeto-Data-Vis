# 05 — Fluxo de Interação Anotado (Requisito R01)

> **Link do Frame**: `[Cole aqui o link do frame do grupo no Miro]`
>
> **Painel**: [r01_ritmo_de_registro.html](r01_ritmo_de_registro.html) ·
> gerado por [gerar_r01.py](gerar_r01.py) · decisões técnicas em [README.md](README.md)

Todo número deste documento foi conferido em `sqlite/dados.db`, que reproduz
`csvs_originais/` linha a linha (ver [sqlite/README.md](../sqlite/README.md)).

---

## 1. Tarefa de Decisão da Orientadora

- **Usuária**: Vanessa Nunes, orientadora pedagógica do processo PBL. É ela
  quem lê a tela; não é material para o grupo de alunos.
- **Tarefa**: escolher com qual grupo abrir conversa sobre ritmo de trabalho na
  próxima reunião de acompanhamento, e sobre qual período dessa conversa tratar.
- **Frequência**: a cada sprint (as do G03, únicas com datas, duram de 10 a 13
  dias) e sob demanda antes de uma reunião com um grupo específico.
- **Prazo e consequência**: a decisão vale para a reunião seguinte. Uma leitura
  distorcida leva a uma conversa de cobrança com um grupo que trabalhou sem
  gerar commit (programação em dupla, reunião, estudo, documentação) ou que
  simplesmente já tinha terminado o calendário.

---

## 2. Ciclo de Vida da Métrica (8 Estações)

Métrica: **commits autorais registrados por dia, por grupo**.

1. **Evento**: o aluno programa, estuda, lê, participa de reunião, faz
   programação em dupla, escreve documentação.
   - *Descarte*: todo trabalho que não vira alteração versionada.
2. **Captura**: `git commit` e envio ao repositório do grupo. O Git grava nome
   e e-mail do autor e duas datas: de autoria e de commit.
   - *Descarte*: alterações não commitadas ou feitas fora do repositório; em
     programação em dupla, o colega que não está no teclado.
3. **Extração**: exportação para `commits.csv`. Os papéis de `pessoas.csv`
   (owner, maintainer, reporter, guest) e os merge requests indicam o GitLab
   como origem, mas o método e a data da extração não estão documentados.
   - *Descarte*: a identidade real, trocada por identificador pseudônimo
     (`G01-A13`). Autores que não casaram com uma pessoa do cadastro viraram
     `[externo]` (391 commits) ou `[bot]` (161): 552 de 2.688, **20,5%**.
4. **Staging**: cópia intacta em `csvs_originais/commits.csv`, aberta só para
   leitura.
   - *Descarte*: nenhum. As duas grafias de fuso (`-03:00` em 2.144 registros e
     `+00:00` em 544) são preservadas como vieram.
5. **Carga**: `sqlite/dados.db`, com todo timestamp convertido para
   America/Sao_Paulo.
   - *Descarte*: só o offset original. O instante é o mesmo, e `verificar.py`
     confere valor a valor. Nenhuma linha é filtrada.
6. **Modelagem**: contagem por `grupo` e `date(autorado_em)`, com calendário
   contínuo que devolve zero no dia sem commit.
   - *Descarte*: 762 commits de merge (`e_merge = 1`) e 213 commits herdados do
     repositório-template, anteriores à criação dos grupos (30 commits caem nos
     dois cortes). Sobram 1.743. Também saem a hora do dia e o tamanho do
     commit: um commit sem linha alterada conta o mesmo que um de 19.253.
7. **Codificação**: colunas por dia no painel HTML, um grupo por vez, com dias
   zerados no eixo, faixas de silêncio e o marco do fim da Sprint 05 do G03.
   - *Descarte*: a mensagem completa do commit (a lista mostra só o título) e
     a comparação lado a lado entre grupos.
8. **Leitura**: a orientadora olha o gráfico, abre dias na lista e decide com
   qual grupo conversar.
   - *Descarte*: o que ela não lê. A frase de limite fica junto ao gráfico
     justamente porque o rodapé pode ficar sem leitura.

> **Estação de maior perda**: **passagem 1 → 2 (Evento → Captura)**. O rastro
> de versão só enxerga a alteração salva no Git. Horas de estudo, reuniões de
> arquitetura e programação em dupla no mesmo computador não deixam registro,
> e nenhuma estação seguinte consegue recuperá-las.

---

## 3. Afirmação Máxima

> *"O gráfico mostra quantos commits autorais o grupo registrou em cada dia do
> período selecionado. É registro de alteração e não mede todo o esforço do
> grupo: estudo, reunião e programação em dupla sem commit não aparecem, e um
> dia sem commit não é um dia sem trabalho."*

---

## 4. Teste de Vocabulário (Dado vs. Cliente)

| Termo | O que o dado registra | O que a cliente entende (premissa do grupo) |
| :--- | :--- | :--- |
| **Commit** | Uma alteração salva no Git, de 1 a milhares de linhas; merges e o histórico do template ficam fora da contagem | Uma unidade de trabalho do aluno |
| **Silêncio** | N dias seguidos sem commit autoral (premissa nossa: N = 3) | O grupo parou de trabalhar |
| **Entrega** | MR com situação `merged` (500 de 540); 463 dos 540 têm destino `main` | Trabalho validado e pronto para o projeto |
| **Atraso** | Cartão fechado depois de `prazo_em`, mas só 24 de 1.238 cartões (1,9%) têm prazo | Risco de não apresentar na sprint. **O dado não sustenta** |
| **Participação** | Contagem de commits, linhas ou eventos; só 24 das 83 pessoas do cadastro produzem algum registro | Dedicação e presença nos ritos do grupo |
| **Revisão** | Um identificador em `revisores_ids` do MR (417 de 540 preenchidos; só 24% no G01) | Análise crítica e discussão do código do colega |
| **Concluído** | Cartão `closed` (1.174 de 1.238) ou MR `merged` | Artefato pronto e aceito pela orientadora |
| **Ativo** | `situacao = active` em `pessoas.csv`, verdadeiro para as 83 pessoas | Aluno engajado. **O campo não distingue ninguém** |

---

## 5. Fluxo Anotado em 3 Raias

**Tarefa**: escolher qual grupo abordar sobre ritmo de trabalho na reunião de
acompanhamento.

- **RAIA DO USUÁRIO (amarela)**
  - ① Abre o painel.
  - ③ Escolhe o grupo e o período (a sprint, quando o grupo tem datas).
  - ⑤ Vê uma faixa de silêncio e pensa "o grupo parou de trabalhar".
  - ⑦ Clica no dia antes ou depois do silêncio e lê quem registrou o quê.
  - ⑨ Decide com qual grupo conversar e sobre qual período.
- **RAIA DA INTERFACE (azul)**
  - ② Abre com G01, todo o registro, silêncio a partir de 3 dias, e a lista do
    dia de pico já aberta.
  - ④ Mostra o título com grupo e janela, as colunas de todos os dias (zero
    marcado na linha de base) e a linha de recorte "Commits autorais: ficam
    fora N commits de merge…".
  - ⑥ Mostra a frase de limite junto ao gráfico, as faixas com "N dias" e o
    marco "fim da Sprint 05 do G03 (26/06)". Silêncios depois do marco vêm
    identificados no resumo, no tooltip e na lista.
  - ⑧ Abre a lista do dia com autoria não resolvida marcada; o rodapé traz o
    percentual do período.
- **RAIA DO DADO (verde)**
  - `commits` agrupado por `grupo` e `date(autorado_em)`, com `e_merge = 0` e
    `commitado_em >= grupos.criado_em`; calendário por CTE recursiva.
  - *Âncora D1* (passos ③–④): o total exclui merges e o histórico do template;
    a chave é (`grupo`, `commit_id`), porque 71 hashes se repetem entre grupos.
  - *Âncora D2* (passo ⑤): dia sem commit volta como `0`; o dado registra
    ausência de commit, não ausência de trabalho.
  - *Âncora D3* (passo ⑤): depois de 26/06 os três grupos somam 2 commits.
  - *Âncora D4* (passo ⑧): 17,5% dos commits contados no R01 não têm autoria
    resolvida (27,5% no G01).

---

## 6. Registro de Divergências (D1..D4)

### D1 · Passos ③–④ · Família: Grão / Completude

- **Leitura do usuário**: *"O G01 fez 662 commits."*
- **O que o dado autoriza**: o G01 tem 662 registros em `commits`. Desses, 197
  são merges e 71 são o histórico herdado do template (10 deles também
  merges). Sobram **404 commits autorais** entre 23/04 e 13/07/2026. Os
  merges não são automáticos: só 31 dos 762 são do `[bot]`; o resto é
  "Merge branch …" feito pelos próprios alunos.
- **Consequência**: inflar o volume de um grupo que faz muitos merges e contar
  como trabalho do grupo commits de 2022 que vieram do template.
- **Decisão de projeto**: a consulta do R01 filtra `e_merge = 0` e
  `commitado_em >= grupos.criado_em`. *Alternativa descartada*: somar tudo e
  explicar em nota de rodapé, porque a nota não impede a leitura errada.
- **Suporte exigido**: linha de recorte logo abaixo do título do gráfico,
  "Commits autorais: ficam fora N commits de merge do grupo neste período e o
  histórico herdado do repositório-template", com N recalculado pelos filtros.
- **Reteste**: o leitor diz que merges ficaram fora sem precisar perguntar ao
  grupo.

### D2 · Passo ⑤ · Família: Temporalidade / Causalidade

- **Leitura do usuário**: *"O G03 parou de trabalhar de 14 a 21/06."*
- **O que o dado autoriza**: o G03 não registrou commit autoral nesses 8 dias,
  que cobrem a primeira semana da Sprint 05 (15/06 a 26/06). Nada além disso.
- **Consequência**: uma conversa de cobrança com um grupo que pode ter usado a
  semana para planejar a sprint, estudar ou escrever documentação.
- **Decisão de projeto**: mostrar o silêncio (faixa com "8 dias", zero no eixo)
  em vez de escondê-lo, e colar nele a frase de limite.
- **Suporte exigido**: frase de limite junto ao gráfico, "Registro de
  alteração; não mede todo o esforço do grupo. Um dia sem commit não é um dia
  sem trabalho."; a mesma frase na lista quando o dia aberto não tem commit.
- **Reteste**: o leitor diz *"não houve registro de commit"* em vez de *"eles
  não trabalharam"*.

### D3 · Passo ⑤ · Família: Janela / Contexto

- **Leitura do usuário**: *"O maior silêncio do G01 é de 16 dias, de 27/06 a
  12/07; é com esse grupo que eu converso."*
- **O que o dado autoriza**: a Sprint 05 do G03 termina em 26/06, e depois
  dessa data os três grupos juntos somam 2 commits (G01 e G03, em 13/07). O
  maior silêncio de cada grupo (G01 16 dias, G02 17, G03 16) é o fim do
  calendário, não um grupo parado. G01 e G02 não têm datas de sprint, então o
  marco vem do G03.
- **Consequência**: escolher o grupo errado para a conversa, e pelo motivo
  errado, porque o indicador "Maior silêncio" aponta sempre para o fim do
  semestre quando o período é "Todo o registro".
- **Decisão de projeto**: marcar 26/06 no gráfico e identificar os silêncios
  posteriores. *Alternativa descartada*: cortar a janela em 26/06, porque
  esconderia os 2 commits de 13/07 e a própria informação de que o calendário
  acabou.
- **Suporte exigido**: linha "fim da Sprint 05 do G03 (26/06)" no gráfico; o
  complemento "depois do fim da Sprint 05 do G03" no indicador de maior
  silêncio, no tooltip e na lista de silêncios; nota no rodapé.
- **Reteste**: o leitor descarta o silêncio pós-26/06 e procura silêncios
  dentro das sprints.

### D4 · Passo ⑧ · Família: Atribuição / Cobertura

- **Leitura do usuário**: *"Na lista do dia 11/06 do G01, o G01-A17 fez 37 dos
  49 commits; os outros quase não contribuíram."*
- **O que o dado autoriza**: 305 dos 1.743 commits do R01 (17,5%) têm autor
  `[externo]` ou `[bot]`; no G01 são 111 de 404 (27,5%). Parte do trabalho do
  dia pode ser de alguém que aparece como `[externo]`.
- **Consequência**: atribuir o ritmo a pessoas, fora da unidade de análise do
  requisito (o grupo), e sobre um campo incompleto.
- **Decisão de projeto**: a contagem por dia não depende do autor e não é
  afetada. A lista mostra o autor, mas marca a autoria não resolvida.
- **Suporte exigido**: selo "autoria não resolvida" na lista; percentual do
  período no rodapé; o item "Quem trabalhou mais" em "O que esta tela não
  sustenta".
- **Reteste**: o leitor não tira conclusão sobre pessoas e cita a lacuna de
  autoria.

---

## 7. Suportes Implementados no Painel HTML

1. **Título que afirma, com unidade e janela**: "Commits registrados por dia,
   grupo G01, 23/04/2026 a 13/07/2026", que acompanha os filtros.
2. **Linha de recorte** junto ao gráfico, com o número de merges excluídos no
   período (D1).
3. **Frase de limite** junto ao gráfico (D2).
4. **Eixo temporal contínuo**: todo dia do período no eixo; dia sem commit com
   marca na linha de base.
5. **Faixas de silêncio** com a duração escrita e limiar ajustável (2 a 7 dias).
6. **Marco do fim da Sprint 05 do G03** e silêncios posteriores identificados
   (D3).
7. **Lista do dia (drill-down)**: clique ou teclado; hora, autor, título e
   linhas; o total bate com a coluna do gráfico; autoria não resolvida marcada
   (D4).
8. **Nota de origem**: fonte (`commits.csv` → `dados.db`), data de extração
   (não registrada; o rodapé diz isso e mostra o que se sabe) e fuso
   (America/Sao_Paulo, dia pela data de autoria).
9. **Um grupo por vez**, cada um na sua escala, e o rodapé "O que esta tela não
   sustenta".
10. **Visão em tabela** do gráfico diário, tooltip no mouse e no teclado, tema
    claro e escuro, sem acesso à rede.

---

## 8. Divergências Mantidas em Aberto

- **Data de autoria vs. data de commit**: mantida a data de autoria
  (`autorado_em`), como pede o requisito. Nos 1.743 commits contados, 98 têm as
  duas datas diferentes (rebase, cherry-pick ou commit aplicado por outra
  pessoa), e em 10 deles o dia muda.
- **Limiar de silêncio**: 3 dias é premissa do grupo, não da cliente. A tela
  deixa ajustar, mas o padrão precisa ser confirmado.
- **Marco de fim de calendário**: vem do G03 e é aplicado aos três grupos.
  Plausível (os três param no mesmo dia), mas não confirmado para G01 e G02.
- **Data de extração**: não registrada. Sem ela, "os últimos 14 dias" são
  relativos ao último commit (13/07/2026), não a hoje.
- **Tamanho do commit**: a contagem trata igual um commit sem linha alterada e
  um de 19.253 linhas. Normalizar exigiria outra definição de métrica, fora do
  R01.

---

## 9. Teste de Interpretação Independente

- **Situação**: não realizado. Fica como trabalho de casa, sujeito à auditoria
  por pares da Aula 06.
- **Roteiro** (critério de aceite do R01):
  1. Uma pessoa que não construiu a tela recebe o painel sem explicação.
  2. Tarefa falada: "Escolha um grupo e um período. Diga quantos commits houve
     por dia, aponte um dia sem registro e abra a lista de um dia qualquer."
  3. Pergunta final: "O que este gráfico não prova?" Ninguém do grupo ajuda.
- **Registrar**: frases literais da pessoa, onde ela hesitou e se tropeçou em
  D1 a D4.
- **Passa se** a pessoa acha o dia zerado no eixo, abre a lista e diz, sem
  ajuda, algo equivalente a "não mede esforço" ou "dia sem commit não é dia sem
  trabalho".
- **Falha se** conclui que um grupo "parou", que alguém "trabalhou mais", ou
  compara grupos pelo tamanho das colunas.

| Participante | Frase literal | Divergência tocada | Resultado |
| :--- | :--- | :--- | :--- |
| | | | |
