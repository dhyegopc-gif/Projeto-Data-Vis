-- R02: Acúmulo de cartões por etapa do quadro, por grupo e sprint
--
-- Etapa = valor de kanban_eventos.coluna que casa com quadro_colunas pelo par
-- (grupo, coluna): Backlog, Doing, Waiting Review, Review. O que não casa é
-- rótulo (CODE, SIZE_M, ART.5...) e fica de fora (Contrato de dados, Regras de junção).
--
-- Permanência: cada entrada ("add") numa etapa é emparelhada com a saída
-- ("remove") de mesma ordem, no mesmo cartão e etapa. Nos dados a sequência
-- sempre alterna entrada/saída, então a n-ésima entrada fecha na n-ésima saída.
-- Entrada sem saída (intervalo aberto) não some da conta, termina em:
--   1. fechado_em do cartão, se o cartão foi fechado depois da entrada;
--   2. senão, o corte da extração (último registro do conjunto de dados).
--
-- Acúmulo: cartão que somou mais de limite_horas na etapa, contando todas as
-- passagens por ela. PREMISSA DO GRUPO, A CONFIRMAR: 48 horas.
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
-- 1. Só movimentos de coluna, sem as 24 linhas repetidas
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
-- 2. Um intervalo por passagem do cartão pela etapa
intervalos AS (
    SELECT e.grupo, e.cartao_numero, e.etapa, e.posicao,
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
           COALESCE(c.sprint, '(sem sprint)') AS sprint
    FROM numerados e
    LEFT JOIN numerados s
           ON s.grupo = e.grupo AND s.cartao_numero = e.cartao_numero
          AND s.etapa = e.etapa AND s.acao = 'remove' AND s.ordem = e.ordem
    JOIN cartoes c ON c.grupo = e.grupo AND c.cartao_numero = e.cartao_numero
    WHERE e.acao = 'add'
),
-- 3. Tempo de cada cartão em cada etapa, somando reentradas
por_cartao AS (
    SELECT grupo, sprint, etapa, posicao, cartao_numero,
           COUNT(*) AS passagens,
           SUM((JULIANDAY(saiu_em) - JULIANDAY(entrou_em)) * 24) AS horas,
           SUM(tipo_fim <> 'saida registrada') AS sem_saida,
           SUM(tipo_fim = 'sem saida: aberto no corte') AS abertos_no_corte
    FROM intervalos
    GROUP BY grupo, sprint, etapa, posicao, cartao_numero
),
-- 4. Resumo por grupo, sprint e etapa
resumo AS (
    SELECT p.grupo, p.sprint, p.etapa, p.posicao,
           COUNT(*)                                     AS cartoes,
           SUM(p.passagens)                             AS passagens,
           ROUND(SUM(p.horas), 1)                       AS horas_total,
           ROUND(AVG(p.horas), 1)                       AS horas_media_por_cartao,
           ROUND(MAX(p.horas), 1)                       AS horas_max,
           SUM(p.horas > par.limite_horas)              AS cartoes_acima_limite,
           SUM(p.sem_saida)                             AS intervalos_sem_saida,
           SUM(p.abertos_no_corte)                      AS intervalos_abertos_no_corte,
           par.limite_horas
    FROM por_cartao p
    CROSS JOIN parametros par
    GROUP BY p.grupo, p.sprint, p.etapa, p.posicao
)
SELECT r.*,
       CASE WHEN RANK() OVER (PARTITION BY grupo, sprint
                              ORDER BY cartoes_acima_limite DESC, horas_total DESC) = 1
            THEN 1 ELSE 0 END AS e_maior_acumulo
FROM resumo r
ORDER BY grupo, sprint, posicao;
