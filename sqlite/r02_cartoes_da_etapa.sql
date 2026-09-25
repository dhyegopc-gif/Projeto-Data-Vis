-- R02: Cartões de uma etapa, para abrir a etapa de maior acúmulo
-- Mesmas regras de r02_acumulo_por_etapa.sql (etapa, emparelhamento,
-- intervalos sem saída e limite); os parâmetros ficam no fim do arquivo.
WITH
parametros AS (
    SELECT 48.0 AS limite_horas
),
corte AS (
    SELECT MAX(t) AS corte_em FROM (
        SELECT MAX(ocorrido_em)  AS t FROM kanban_eventos
        UNION ALL SELECT MAX(atualizado_em) FROM cartoes
        UNION ALL SELECT MAX(atualizado_em) FROM merge_requests
        UNION ALL SELECT MAX(commitado_em)  FROM commits
    )
),
movimentos AS (
    SELECT DISTINCT k.grupo, k.cartao_numero, k.acao, k.coluna AS etapa,
           qc.posicao, k.ocorrido_em
    FROM kanban_eventos k
    JOIN quadro_colunas qc ON qc.grupo = k.grupo AND qc.coluna = k.coluna
),
numerados AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY grupo, cartao_numero, etapa, acao
                              ORDER BY ocorrido_em) AS ordem
    FROM movimentos
),
intervalos AS (
    SELECT e.grupo, e.cartao_numero, e.etapa,
           e.ocorrido_em AS entrou_em,
           CASE
               WHEN s.ocorrido_em IS NOT NULL  THEN s.ocorrido_em
               WHEN c.fechado_em >= e.ocorrido_em THEN c.fechado_em
               ELSE (SELECT corte_em FROM corte)
           END AS saiu_em,
           CASE
               WHEN s.ocorrido_em IS NOT NULL  THEN 'saida registrada'
               WHEN c.fechado_em >= e.ocorrido_em THEN 'sem saida: fechado com o cartao'
               ELSE 'sem saida: aberto no corte'
           END AS tipo_fim,
           COALESCE(c.sprint, '(sem sprint)') AS sprint,
           c.titulo, c.situacao, c.responsaveis_ids
    FROM numerados e
    LEFT JOIN numerados s
           ON s.grupo = e.grupo AND s.cartao_numero = e.cartao_numero
          AND s.etapa = e.etapa AND s.acao = 'remove' AND s.ordem = e.ordem
    JOIN cartoes c ON c.grupo = e.grupo AND c.cartao_numero = e.cartao_numero
    WHERE e.acao = 'add'
)
SELECT
    i.grupo,
    i.sprint,
    i.etapa,
    i.cartao_numero,
    i.titulo,
    i.situacao,
    i.responsaveis_ids,
    COUNT(*)                                                        AS passagens,
    MIN(i.entrou_em)                                                AS primeira_entrada,
    MAX(i.saiu_em)                                                  AS ultima_saida,
    ROUND(SUM((JULIANDAY(i.saiu_em) - JULIANDAY(i.entrou_em)) * 24), 1) AS horas_na_etapa,
    CASE WHEN SUM((JULIANDAY(i.saiu_em) - JULIANDAY(i.entrou_em)) * 24) > p.limite_horas
         THEN 1 ELSE 0 END                                          AS acima_limite,
    GROUP_CONCAT(DISTINCT i.tipo_fim)                               AS tipo_fim
FROM intervalos i
CROSS JOIN parametros p
WHERE i.grupo  = 'G01'              -- Parâmetro: grupo
  AND i.sprint = 'Sprint 02'        -- Parâmetro: sprint ('(sem sprint)' para cartões sem sprint)
  AND i.etapa  = 'Backlog'          -- Parâmetro: etapa (Backlog, Doing, Waiting Review, Review)
GROUP BY i.grupo, i.sprint, i.etapa, i.cartao_numero
ORDER BY horas_na_etapa DESC;
