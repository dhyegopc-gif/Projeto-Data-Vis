-- T05: Eventos tratados do Kanban, deduplicados e prontos para resolver SKs.
--
-- A base SQLite contem as tabelas brutas, nao dim_* nem fato_* modeladas.
-- Esta view expoe as chaves naturais para a carga dimensional resolver os SKs
-- por (grupo, cartao_numero), pessoa_id, grupo/quadro/coluna e rotulo canonico.
--
-- A coluna "coluna" e discriminada pelo join em quadro_colunas: casar significa
-- movimento; nao casar significa rotulo. Valor vazio e desconhecido.
-- O calendario informado de G03 e reaplicado aos tres grupos por premissa.

DROP VIEW IF EXISTS t05_eventos_kanban;

CREATE VIEW t05_eventos_kanban AS
WITH
calendario_sprint AS (
    SELECT sprint, inicio_em, prazo_em
    FROM sprints
    WHERE grupo = 'G03'
      AND inicio_em IS NOT NULL
      AND prazo_em IS NOT NULL
),
eventos_deduplicados AS (
    SELECT MIN(evento_id) AS evento_origem_id,
           grupo,
           cartao_numero,
           acao,
           coluna,
           pessoa_id,
           ocorrido_em
    FROM kanban_eventos
    GROUP BY grupo, cartao_numero, acao, coluna, pessoa_id, ocorrido_em
),
eventos_classificados AS (
    SELECT e.evento_origem_id,
           e.grupo,
           e.cartao_numero,
           e.pessoa_id,
           e.acao,
           e.coluna AS coluna_origem,
           e.ocorrido_em,
           qc.quadro AS quadro_natural,
           CASE
               WHEN e.coluna IS NULL OR trim(e.coluna) = '' THEN 'DESCONHECIDO'
               WHEN qc.coluna IS NOT NULL THEN 'MUDANCA_COLUNA'
               ELSE 'MARCACAO_ROTULO'
           END AS tipo_evento,
           CASE
               WHEN instr(lower(COALESCE(e.pessoa_id, '')), 'bot') > 0
                 OR instr(lower(COALESCE(e.pessoa_id, '')), 'automat') > 0
                 OR instr(lower(COALESCE(e.pessoa_id, '')), 'automation') > 0
                 OR instr(lower(COALESCE(e.pessoa_id, '')), 'pipeline') > 0
                 OR instr(lower(COALESCE(e.pessoa_id, '')), 'runner') > 0
               THEN 1 ELSE 0
           END AS is_bot,
           CASE
               WHEN e.coluna IS NOT NULL AND trim(e.coluna) <> ''
                AND qc.coluna IS NULL
               THEN upper(trim(e.coluna))
           END AS rotulo_bruto_normalizado,
           replace(
               replace(
                   replace(upper(trim(e.coluna)), 'ART', ''),
                   '.', ''
               ),
               ' ', ''
           ) AS numero_artigo
    FROM eventos_deduplicados e
    LEFT JOIN quadro_colunas qc
           ON qc.grupo = e.grupo
          AND qc.quadro = 'Scrum Board'
          AND qc.coluna = e.coluna
),
rotulos_normalizados AS (
    SELECT e.*,
           CASE
               WHEN e.tipo_evento <> 'MARCACAO_ROTULO' THEN NULL
               WHEN upper(trim(e.coluna_origem)) LIKE 'ART%'
                AND e.numero_artigo <> ''
                AND e.numero_artigo NOT GLOB '*[^0-9]*'
                AND CAST(e.numero_artigo AS INTEGER) BETWEEN 1 AND 18
               THEN printf('ART-%02d', CAST(e.numero_artigo AS INTEGER))
               WHEN e.rotulo_bruto_normalizado IN ('SIZE_PP', 'SIZE PP', 'PP') THEN 'SIZE_PP'
               WHEN e.rotulo_bruto_normalizado IN ('SIZE_P', 'SIZE P', 'P') THEN 'SIZE_P'
               WHEN e.rotulo_bruto_normalizado IN ('SIZE_M', 'SIZE M', 'M') THEN 'SIZE_M'
               WHEN e.rotulo_bruto_normalizado IN ('SIZE_G', 'SIZE G', 'G') THEN 'SIZE_G'
               WHEN e.rotulo_bruto_normalizado IN ('SIZE_GG', 'SIZE GG', 'GG') THEN 'SIZE_GG'
               WHEN e.rotulo_bruto_normalizado IN ('BUG', 'FIX') THEN 'BUG'
               ELSE e.rotulo_bruto_normalizado
           END AS rotulo_canonico
    FROM eventos_classificados e
),
rotulos_categorizados AS (
    SELECT e.*,
           CASE
               WHEN e.tipo_evento <> 'MARCACAO_ROTULO' THEN NULL
               WHEN e.rotulo_canonico LIKE 'ART-%' THEN 'ARTEFATO'
               WHEN e.rotulo_canonico IN ('SIZE_PP', 'SIZE_P', 'SIZE_M', 'SIZE_G', 'SIZE_GG') THEN 'TAMANHO'
               WHEN e.rotulo_canonico IN ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8') THEN 'PRIORIDADE'
               WHEN e.rotulo_canonico = 'BUG' THEN 'BUG'
               WHEN e.rotulo_canonico LIKE 'ANO:%'
                 OR e.rotulo_canonico LIKE 'CURSO:%'
                 OR e.rotulo_canonico LIKE 'TRIMESTRE:%' THEN 'METADADO_TURMA'
               ELSE 'TIPO_TRABALHO'
           END AS categoria_rotulo
    FROM rotulos_normalizados e
),
eventos_com_sprint AS (
    SELECT e.*,
           s.sprint AS sprint_nome,
           CASE WHEN s.sprint IS NOT NULL THEN e.grupo END AS sprint_grupo,
           CASE WHEN s.sprint IS NOT NULL THEN 'G03' END AS origem_calendario_sprint
    FROM rotulos_categorizados e
    LEFT JOIN calendario_sprint s
           ON date(e.ocorrido_em) BETWEEN s.inicio_em AND s.prazo_em
),
eventos_sequenciados AS (
    SELECT e.*,
           ROW_NUMBER() OVER (
               PARTITION BY e.grupo, e.cartao_numero
               ORDER BY e.ocorrido_em, e.evento_origem_id
           ) AS seq_no_cartao,
           LEAD(e.ocorrido_em) OVER (
               PARTITION BY e.grupo, e.cartao_numero
               ORDER BY e.ocorrido_em, e.evento_origem_id
           ) AS proximo_evento_em
    FROM eventos_com_sprint e
)
SELECT evento_origem_id,
       grupo,
       cartao_numero,
       pessoa_id,
       date(ocorrido_em) AS data_evento,
       CAST(strftime('%H', ocorrido_em) AS INTEGER) AS hora_evento,
       ocorrido_em,
       acao,
       tipo_evento,
       is_bot,
    coluna_origem,
       CASE WHEN tipo_evento = 'MUDANCA_COLUNA' THEN coluna_origem END AS coluna_quadro,
       CASE WHEN tipo_evento = 'MARCACAO_ROTULO' THEN categoria_rotulo END AS categoria_rotulo,
       CASE WHEN tipo_evento = 'MARCACAO_ROTULO' THEN rotulo_canonico END AS rotulo_canonico,
       sprint_grupo,
       sprint_nome,
       origem_calendario_sprint,
       seq_no_cartao,
       CASE
           WHEN proximo_evento_em IS NULL THEN NULL
           ELSE ROUND((julianday(proximo_evento_em) - julianday(ocorrido_em)) * 24.0, 2)
       END AS horas_ate_proximo_evento,
       1 AS contador_evento
FROM eventos_sequenciados;
