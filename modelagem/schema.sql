-- =====================================================================
-- Projeto Data Vis - Modelo Dimensional (star schema / fact constellation)
-- Fonte: 8 CSVs de telemetria GitLab de 3 grupos academicos (G01/G02/G03)
-- Dialeto: PostgreSQL 14+ (compativel com DuckDB trocando os SERIAL)
-- =====================================================================
-- Grao declarado por fato:
--   fato_commit          1 linha por (grupo, commit_id)                 2.688
--   fato_cartao          1 linha por (grupo, cartao_numero)             1.238
--   fato_merge_request   1 linha por (grupo, mr_numero)                   540
--   fato_evento_cartao   1 linha por evento de quadro/rotulo em cartao 13.194
-- =====================================================================

DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;
SET search_path TO dw;


-- =====================================================================
-- 1. DIMENSOES
-- =====================================================================

-- ---------------------------------------------------------------------
-- dim_data  |  conformada, role-playing (criacao, fechamento, merge, ...)
-- Cobertura obrigatoria: 2022-04-01 .. 2026-12-31
--   (commits carregam historico do repositorio-template desde 2022;
--    a atividade dos alunos concentra-se em 2026-04 .. 2026-07)
-- ---------------------------------------------------------------------
CREATE TABLE dim_data (
    sk_data            INTEGER      PRIMARY KEY,   -- AAAAMMDD
    data               DATE         NOT NULL UNIQUE,
    ano                SMALLINT     NOT NULL,
    trimestre          SMALLINT     NOT NULL,
    mes                SMALLINT     NOT NULL,
    nome_mes           VARCHAR(12)  NOT NULL,
    ano_mes            CHAR(7)      NOT NULL,      -- '2026-04'
    semana_iso         SMALLINT     NOT NULL,
    ano_semana_iso     CHAR(8)      NOT NULL,      -- '2026-W18'
    dia                SMALLINT     NOT NULL,
    dia_da_semana      SMALLINT     NOT NULL,      -- 1=segunda .. 7=domingo
    nome_dia_semana    VARCHAR(13)  NOT NULL,
    e_fim_de_semana    BOOLEAN      NOT NULL,
    e_dia_letivo       BOOLEAN      NOT NULL       -- dia util dentro do periodo do modulo
);
COMMENT ON TABLE dim_data IS
    'Calendario diario. Usada em papeis multiplos; expor uma VIEW por papel na camada semantica.';

-- ---------------------------------------------------------------------
-- dim_hora  |  conformada. Separada de dim_data para nao explodir o grao
-- do calendario. Todo timestamp e convertido para America/Sao_Paulo antes
-- de derivar a hora (os CSVs misturam UTC 'Z' e offset -03:00).
-- ---------------------------------------------------------------------
CREATE TABLE dim_hora (
    sk_hora              SMALLINT    PRIMARY KEY,  -- 0..23
    hora                 SMALLINT    NOT NULL,
    hora_rotulo          CHAR(5)     NOT NULL,     -- '14:00'
    faixa_horaria        VARCHAR(20) NOT NULL,     -- Madrugada/Manha/Tarde/Noite
    e_horario_comercial  BOOLEAN     NOT NULL,     -- 09:00-18:00
    e_madrugada          BOOLEAN     NOT NULL      -- 00:00-05:59
);

-- ---------------------------------------------------------------------
-- dim_grupo  |  o projeto/repositorio. Origem: grupos.csv (3 linhas)
-- ---------------------------------------------------------------------
CREATE TABLE dim_grupo (
    sk_grupo             SMALLSERIAL PRIMARY KEY,
    grupo_id             CHAR(3)     NOT NULL UNIQUE,   -- chave natural: G01/G02/G03
    branch_padrao        VARCHAR(50) NOT NULL,
    criado_em            TIMESTAMPTZ NOT NULL,
    ultima_atividade_em  TIMESTAMPTZ NOT NULL,
    dias_de_vida         INTEGER     NOT NULL,
    qtd_membros          SMALLINT    NOT NULL       -- snapshot vindo de pessoas.csv
);

-- ---------------------------------------------------------------------
-- dim_pessoa  |  conformada. ATENCAO: pessoa_id e GLOBAL, nao por grupo.
-- Ha atividade cruzada (membros de G03 com commits em G01 e G02), portanto
-- a chave natural e pessoa_id sozinho e o grupo de origem e so um atributo.
-- Inclui 3 linhas sentinela para preservar a integridade referencial:
--   [externo]      -> conta fora do roster        (aparece em todos os fatos)
--   [bot]          -> automacao                   (aparece so em commits)
--   [desconhecido] -> fallback de ETL             (hoje sem ocorrencias)
-- ---------------------------------------------------------------------
CREATE TABLE dim_pessoa (
    sk_pessoa        SERIAL       PRIMARY KEY,
    pessoa_id        VARCHAR(20)  NOT NULL UNIQUE,  -- 'G01-A13', '[externo]', '[bot]'
    grupo_origem     CHAR(3),                       -- NULL nas sentinelas
    papel            VARCHAR(15),                   -- owner/maintainer/reporter/guest
    situacao         VARCHAR(10),
    e_sentinela      BOOLEAN      NOT NULL DEFAULT FALSE,
    tipo_pessoa      VARCHAR(15)  NOT NULL,         -- MEMBRO/EXTERNO/BOT/DESCONHECIDO
    teve_atividade   BOOLEAN      NOT NULL DEFAULT FALSE  -- 24 de 83 membros produzem fatos
);

-- ---------------------------------------------------------------------
-- dim_sprint  |  chave natural COMPOSTA (grupo, sprint).
-- Apenas G03 preenche inicio/prazo no CSV; G01 e G02 vem nulos.
-- A coluna origem_datas registra a procedencia para nao mascarar a lacuna.
-- ---------------------------------------------------------------------
CREATE TABLE dim_sprint (
    sk_sprint      SMALLSERIAL PRIMARY KEY,
    grupo_id       CHAR(3)     NOT NULL,
    sprint_nome    VARCHAR(20) NOT NULL,            -- 'Sprint 01' .. 'Sprint 05'
    sprint_num     SMALLINT    NOT NULL,
    situacao       VARCHAR(10) NOT NULL,
    data_inicio    DATE,
    data_prazo     DATE,
    duracao_dias   SMALLINT,
    origem_datas   VARCHAR(15) NOT NULL,            -- INFORMADA / IMPUTADA / AUSENTE
    UNIQUE (grupo_id, sprint_nome)
);

-- ---------------------------------------------------------------------
-- dim_situacao  |  conformada entre cartao e merge request.
-- Valores: opened, closed, merged.
-- ---------------------------------------------------------------------
CREATE TABLE dim_situacao (
    sk_situacao    SMALLSERIAL PRIMARY KEY,
    situacao       VARCHAR(10) NOT NULL UNIQUE,
    situacao_pt    VARCHAR(20) NOT NULL,
    e_encerrado    BOOLEAN     NOT NULL,
    e_sucesso      BOOLEAN     NOT NULL             -- merged = TRUE; closed = FALSE
);

-- ---------------------------------------------------------------------
-- dim_coluna_quadro  |  chave natural COMPOSTA (grupo, quadro, coluna).
-- Origem: quadro_colunas.csv (12 linhas = 3 grupos x 4 colunas).
-- posicao da a ordem do fluxo: 0 Backlog -> 1 Doing -> 2 Waiting Review -> 3 Review
-- ---------------------------------------------------------------------
CREATE TABLE dim_coluna_quadro (
    sk_coluna        SMALLSERIAL PRIMARY KEY,
    grupo_id         CHAR(3)     NOT NULL,
    quadro           VARCHAR(50) NOT NULL,
    coluna           VARCHAR(50) NOT NULL,
    posicao          SMALLINT    NOT NULL,
    e_coluna_inicial BOOLEAN     NOT NULL,
    e_coluna_final   BOOLEAN     NOT NULL,
    UNIQUE (grupo_id, quadro, coluna)
);

-- ---------------------------------------------------------------------
-- dim_rotulo  |  a dimensao que carrega o maior ganho da modelagem.
-- O CSV traz 81 grafias distintas de rotulo; a normalizacao as reduz a 50
-- valores canonicos organizados em 6 categorias:
--   ARTEFATO        42 grafias -> 18 canonicos (ART. 5 / ART.5 / ART.05 -> ART-05)
--   TAMANHO         11 grafias ->  5 canonicos (SIZE_M e M -> M)
--   TIPO_TRABALHO   13 grafias -> 12 canonicos (BUG e Fix -> CORRECAO)
--   PRIORIDADE       8 grafias ->  8 canonicos (P1..P8)
--   ESTADO_QUADRO    4 grafias ->  4 canonicos (nome de coluna vazado p/ rotulo)
--   METADADO_TURMA   3 grafias ->  3 canonicos (ruido: 'Ano: 2025', etc.)
-- CUIDADO: 'P' isolado e TAMANHO (pequeno); 'P1'..'P8' sao PRIORIDADE.
-- ---------------------------------------------------------------------
CREATE TABLE dim_rotulo (
    sk_rotulo        SMALLSERIAL PRIMARY KEY,
    categoria        VARCHAR(20) NOT NULL,
    valor_canonico   VARCHAR(40) NOT NULL,
    rotulo_exibicao  VARCHAR(60) NOT NULL,
    ordem            SMALLINT,                      -- ordenacao dentro da categoria
    artefato_num     SMALLINT,                      -- 1..18, so em ARTEFATO
    pontos_tamanho   SMALLINT,                      -- PP=1 P=2 M=3 G=5 GG=8 (proxy de esforco)
    UNIQUE (categoria, valor_canonico)
);

-- ---------------------------------------------------------------------
-- stg_map_rotulo  |  rastreabilidade da normalizacao (81 -> 50).
-- Nao e dimensao: e a tabela de-para que documenta a limpeza e permite
-- auditar de qual grafia bruta veio cada linha das pontes.
-- ---------------------------------------------------------------------
CREATE TABLE stg_map_rotulo (
    rotulo_bruto   VARCHAR(60) PRIMARY KEY,
    sk_rotulo      SMALLINT    NOT NULL REFERENCES dim_rotulo(sk_rotulo),
    ocorrencias    INTEGER     NOT NULL
);


-- =====================================================================
-- 2. FATOS
-- =====================================================================

-- ---------------------------------------------------------------------
-- fato_commit  |  TRANSACIONAL
-- Grao: 1 linha por (grupo, commit_id). 2.688 linhas, chave 100% unica.
-- e_historico_template isola os 213 commits anteriores a criacao do grupo,
-- herdados do fork do repositorio-template (datas de 2022 a 2025).
-- Sem esse filtro, toda metrica de volume de codigo fica inflada.
-- ---------------------------------------------------------------------
CREATE TABLE fato_commit (
    sk_commit                  BIGSERIAL   PRIMARY KEY,
    -- dimensoes
    sk_grupo                   SMALLINT    NOT NULL REFERENCES dim_grupo(sk_grupo),
    sk_autor                   INTEGER     NOT NULL REFERENCES dim_pessoa(sk_pessoa),
    sk_data_autoria            INTEGER     NOT NULL REFERENCES dim_data(sk_data),
    sk_hora_autoria            SMALLINT    NOT NULL REFERENCES dim_hora(sk_hora),
    sk_data_commit             INTEGER     NOT NULL REFERENCES dim_data(sk_data),
    sk_hora_commit             SMALLINT    NOT NULL REFERENCES dim_hora(sk_hora),
    -- dimensao degenerada
    commit_id                  VARCHAR(12) NOT NULL,
    titulo                     TEXT,
    -- flags
    e_merge                    BOOLEAN     NOT NULL,
    e_historico_template       BOOLEAN     NOT NULL,
    e_autoria_terceiros        BOOLEAN     NOT NULL,   -- autorado_em <> commitado_em (109 casos)
    -- medidas aditivas
    linhas_adicionadas         INTEGER     NOT NULL,
    linhas_removidas           INTEGER     NOT NULL,
    linhas_total               INTEGER     NOT NULL,   -- = adicionadas + removidas (validado: 2688/2688)
    linhas_liquidas            INTEGER     NOT NULL,   -- = adicionadas - removidas
    -- medida nao aditiva
    defasagem_autoria_seg      INTEGER     NOT NULL,
    UNIQUE (sk_grupo, commit_id)
);

-- ---------------------------------------------------------------------
-- fato_cartao  |  SNAPSHOT ACUMULADO (accumulating snapshot)
-- Grao: 1 linha por (grupo, cartao_numero). 1.238 linhas, chave 100% unica.
-- A linha e atualizada conforme o cartao avanca no fluxo; os marcos sao as
-- FKs de data (criacao -> fechamento) e as medidas de duracao entre elas.
-- sk_tamanho e sk_tipo_trabalho sao "pull-outs" de dim_rotulo: o rotulo
-- dominante de cada categoria promovido a FK para facilitar o corte direto,
-- sem impedir a analise multi-rotulo pela ponte.
-- ---------------------------------------------------------------------
CREATE TABLE fato_cartao (
    sk_cartao                  BIGSERIAL   PRIMARY KEY,
    -- dimensoes
    sk_grupo                   SMALLINT    NOT NULL REFERENCES dim_grupo(sk_grupo),
    sk_autor                   INTEGER     NOT NULL REFERENCES dim_pessoa(sk_pessoa),
    sk_responsavel             INTEGER              REFERENCES dim_pessoa(sk_pessoa),
    sk_fechado_por             INTEGER              REFERENCES dim_pessoa(sk_pessoa),
    sk_sprint                  SMALLINT             REFERENCES dim_sprint(sk_sprint),
    sk_situacao                SMALLINT    NOT NULL REFERENCES dim_situacao(sk_situacao),
    sk_tamanho                 SMALLINT             REFERENCES dim_rotulo(sk_rotulo),
    sk_tipo_trabalho           SMALLINT             REFERENCES dim_rotulo(sk_rotulo),
    -- marcos do snapshot acumulado
    sk_data_criacao            INTEGER     NOT NULL REFERENCES dim_data(sk_data),
    sk_hora_criacao            SMALLINT    NOT NULL REFERENCES dim_hora(sk_hora),
    sk_data_fechamento         INTEGER              REFERENCES dim_data(sk_data),
    sk_data_prazo              INTEGER              REFERENCES dim_data(sk_data),
    sk_data_atualizacao        INTEGER     NOT NULL REFERENCES dim_data(sk_data),
    -- dimensao degenerada
    cartao_numero              INTEGER     NOT NULL,
    titulo                     TEXT        NOT NULL,
    descricao                  TEXT,
    -- flags
    e_fechado                  BOOLEAN     NOT NULL,   -- 1.174 fechados / 64 abertos
    tem_prazo                  BOOLEAN     NOT NULL,   -- so 24 cartoes tem prazo
    e_atrasado                 BOOLEAN,                -- NULL quando nao ha prazo
    tem_descricao              BOOLEAN     NOT NULL,   -- 538 cartoes sem descricao
    tem_responsavel            BOOLEAN     NOT NULL,
    -- medidas
    lead_time_horas            NUMERIC(10,2),          -- fechamento - criacao (media 101,4 h)
    lead_time_dias             NUMERIC(8,2),
    qtd_comentarios            SMALLINT    NOT NULL,
    qtd_rotulos                SMALLINT    NOT NULL,
    qtd_eventos_kanban         SMALLINT    NOT NULL,   -- contagem vinda de fato_evento_cartao
    tempo_estimado_seg         INTEGER     NOT NULL,   -- preenchido em apenas 17 cartoes
    contador_cartao            SMALLINT    NOT NULL DEFAULT 1,
    UNIQUE (sk_grupo, cartao_numero)
);
-- NAO MODELADAS: cartoes.peso (100% nulo) e cartoes.tempo_gasto_s (constante 0).
-- Colunas mortas na origem; carregar so cria ilusao de metrica disponivel.

-- ---------------------------------------------------------------------
-- fato_merge_request  |  SNAPSHOT ACUMULADO
-- Grao: 1 linha por (grupo, mr_numero). 540 linhas, chave 100% unica.
-- e_automerge e tem_revisor sustentam a analise de pratica de code review:
-- 34 dos 500 MRs mesclados foram mesclados pelo proprio autor e 115 seguiram
-- sem revisor designado.
-- ---------------------------------------------------------------------
CREATE TABLE fato_merge_request (
    sk_mr                      BIGSERIAL   PRIMARY KEY,
    -- dimensoes
    sk_grupo                   SMALLINT    NOT NULL REFERENCES dim_grupo(sk_grupo),
    sk_autor                   INTEGER     NOT NULL REFERENCES dim_pessoa(sk_pessoa),
    sk_merged_por              INTEGER              REFERENCES dim_pessoa(sk_pessoa),
    sk_revisor                 INTEGER              REFERENCES dim_pessoa(sk_pessoa),
    sk_responsavel             INTEGER              REFERENCES dim_pessoa(sk_pessoa),
    sk_sprint                  SMALLINT             REFERENCES dim_sprint(sk_sprint),
    sk_situacao                SMALLINT    NOT NULL REFERENCES dim_situacao(sk_situacao),
    -- marcos
    sk_data_criacao            INTEGER     NOT NULL REFERENCES dim_data(sk_data),
    sk_hora_criacao            SMALLINT    NOT NULL REFERENCES dim_hora(sk_hora),
    sk_data_merge              INTEGER              REFERENCES dim_data(sk_data),
    sk_data_fechamento         INTEGER              REFERENCES dim_data(sk_data),
    -- dimensao degenerada
    mr_numero                  INTEGER     NOT NULL,
    titulo                     TEXT        NOT NULL,
    branch_origem              TEXT        NOT NULL,
    branch_destino             VARCHAR(80) NOT NULL,  -- main / dev / develop / feat/edicao-cadastros
    -- flags
    e_merged                   BOOLEAN     NOT NULL,  -- 500 merged / 39 closed / 1 opened
    e_rascunho                 BOOLEAN     NOT NULL,
    tem_revisor                BOOLEAN     NOT NULL,
    e_automerge                BOOLEAN     NOT NULL,  -- autor = quem mesclou
    e_para_branch_padrao       BOOLEAN     NOT NULL,
    -- medidas
    tempo_ate_merge_horas      NUMERIC(10,2),         -- media 22,9 h
    qtd_comentarios            SMALLINT    NOT NULL,
    qtd_rotulos                SMALLINT    NOT NULL,
    contador_mr                SMALLINT    NOT NULL DEFAULT 1,
    UNIQUE (sk_grupo, mr_numero)
);

-- ---------------------------------------------------------------------
-- fato_evento_cartao  |  TRANSACIONAL (o fato mais fino do modelo)
-- Grao: 1 linha por evento registrado sobre um cartao. 13.194 linhas.
--
-- DECISAO CENTRAL: a coluna 'coluna' de kanban_eventos.csv mistura dois
-- assuntos diferentes sob o mesmo nome. Dos 13.194 eventos, 9.052 movem o
-- cartao entre colunas do Scrum Board e 4.142 apenas adicionam/removem um
-- rotulo. O discriminador tipo_evento separa os dois, com uma FK exclusiva
-- para cada caso (exatamente uma preenchida por linha).
-- Mantidos na mesma tabela para preservar a linha do tempo do cartao em
-- ordem; a camada semantica expoe as duas visoes separadas.
--
-- 24 linhas sao duplicatas exatas na origem (13.194 linhas / 13.170 chaves
-- naturais distintas). Por isso a PK e substituta e nao a combinacao natural.
-- ---------------------------------------------------------------------
CREATE TABLE fato_evento_cartao (
    sk_evento                  BIGSERIAL   PRIMARY KEY,
    -- dimensoes
    sk_grupo                   SMALLINT    NOT NULL REFERENCES dim_grupo(sk_grupo),
    sk_cartao                  BIGINT      NOT NULL REFERENCES fato_cartao(sk_cartao),
    sk_pessoa                  INTEGER     NOT NULL REFERENCES dim_pessoa(sk_pessoa),
    sk_data                    INTEGER     NOT NULL REFERENCES dim_data(sk_data),
    sk_hora                    SMALLINT    NOT NULL REFERENCES dim_hora(sk_hora),
    sk_coluna                  SMALLINT             REFERENCES dim_coluna_quadro(sk_coluna),
    sk_rotulo                  SMALLINT             REFERENCES dim_rotulo(sk_rotulo),
    -- discriminador + dimensao degenerada
    tipo_evento                VARCHAR(20) NOT NULL, -- MOVIMENTO_COLUNA | MARCACAO_ROTULO
    acao                       VARCHAR(6)  NOT NULL, -- add | remove
    -- medidas
    seq_no_cartao              SMALLINT    NOT NULL, -- ordem do evento dentro do cartao
    horas_ate_proximo_evento   NUMERIC(10,2),        -- NULL no ultimo evento do cartao
    contador_evento            SMALLINT    NOT NULL DEFAULT 1,
    CONSTRAINT ck_evento_alvo CHECK (
        (tipo_evento = 'MOVIMENTO_COLUNA' AND sk_coluna IS NOT NULL AND sk_rotulo IS NULL) OR
        (tipo_evento = 'MARCACAO_ROTULO'  AND sk_rotulo IS NOT NULL AND sk_coluna IS NULL)
    )
);


-- =====================================================================
-- 3. PONTES (relacao muitos-para-muitos com dim_rotulo)
-- =====================================================================
-- Um cartao carrega ate 6 rotulos e um MR ate 5; os campos 'rotulos' vem
-- como string separada por ';'. Sem ponte, qualquer soma por rotulo contaria
-- o mesmo cartao varias vezes. peso_alocacao = 1/qtd_rotulos permite somas
-- sem dupla contagem quando isso for desejado.
-- Duas pontes separadas (e nao uma polimorfica) para manter FK real.

CREATE TABLE ponte_cartao_rotulo (
    sk_cartao       BIGINT       NOT NULL REFERENCES fato_cartao(sk_cartao),
    sk_rotulo       SMALLINT     NOT NULL REFERENCES dim_rotulo(sk_rotulo),
    peso_alocacao   NUMERIC(6,4) NOT NULL,
    PRIMARY KEY (sk_cartao, sk_rotulo)
);

CREATE TABLE ponte_mr_rotulo (
    sk_mr           BIGINT       NOT NULL REFERENCES fato_merge_request(sk_mr),
    sk_rotulo       SMALLINT     NOT NULL REFERENCES dim_rotulo(sk_rotulo),
    peso_alocacao   NUMERIC(6,4) NOT NULL,
    PRIMARY KEY (sk_mr, sk_rotulo)
);


-- =====================================================================
-- 4. INDICES DE APOIO AS CONSULTAS ANALITICAS
-- =====================================================================
CREATE INDEX ix_commit_grupo_data  ON fato_commit (sk_grupo, sk_data_autoria);
CREATE INDEX ix_commit_autor       ON fato_commit (sk_autor);
CREATE INDEX ix_cartao_grupo_data  ON fato_cartao (sk_grupo, sk_data_criacao);
CREATE INDEX ix_cartao_sprint      ON fato_cartao (sk_sprint);
CREATE INDEX ix_mr_grupo_data      ON fato_merge_request (sk_grupo, sk_data_criacao);
CREATE INDEX ix_mr_autor           ON fato_merge_request (sk_autor);
CREATE INDEX ix_evento_cartao_seq  ON fato_evento_cartao (sk_cartao, seq_no_cartao);
CREATE INDEX ix_evento_tipo_data   ON fato_evento_cartao (tipo_evento, sk_data);


-- =====================================================================
-- 5. CAMADA SEMANTICA - VIEWS DE PAPEL E DE ASSUNTO
-- =====================================================================

-- Role-playing de dim_data: uma view por papel evita apelidos ambiguos no BI
CREATE VIEW vw_data_criacao    AS SELECT * FROM dim_data;
CREATE VIEW vw_data_fechamento AS SELECT * FROM dim_data;
CREATE VIEW vw_data_merge      AS SELECT * FROM dim_data;

-- As duas faces de fato_evento_cartao
CREATE VIEW vw_movimento_kanban AS
SELECT e.*, c.coluna, c.posicao
FROM   fato_evento_cartao e
JOIN   dim_coluna_quadro  c ON c.sk_coluna = e.sk_coluna
WHERE  e.tipo_evento = 'MOVIMENTO_COLUNA';

CREATE VIEW vw_marcacao_rotulo AS
SELECT e.*, r.categoria, r.valor_canonico
FROM   fato_evento_cartao e
JOIN   dim_rotulo         r ON r.sk_rotulo = e.sk_rotulo
WHERE  e.tipo_evento = 'MARCACAO_ROTULO';

-- Trabalho de codigo efetivo dos alunos: exclui o historico herdado do template
CREATE VIEW vw_commit_autoral AS
SELECT * FROM fato_commit WHERE NOT e_historico_template;
