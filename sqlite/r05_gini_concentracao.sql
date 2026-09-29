-- R05: Índice de Gini da concentração do trabalho registrado, por grupo
--
-- Um valor por grupo x sprint x medida. Mesmas regras de
-- r05_contribuicao_por_integrante.sql (integrante, medidas, sprint, parcela
-- não atribuída); o bloco WITH é o mesmo.
--
-- Gini sobre os n integrantes (zeros incluídos), valores em ordem crescente:
--     G = SUM( (2i - n - 1) * x_i ) / ( n * SUM(x) )
-- 0 = todos registraram o mesmo; o máximo com n integrantes é (n - 1) / n
-- (0,857 com 7), quando uma pessoa só tem tudo.
--
-- A parcela '(não atribuído)' fica FORA do índice: não se sabe de quem é.
-- pct_nao_atribuido diz o quanto isso pesa; a tela mostra o intervalo de Gini
-- possível se essa parcela fosse de alguém.
WITH
tamanhos(tamanho, dias_planejados) AS (
    VALUES ('PP', 0.25), ('P', 0.5), ('M', 1.0), ('G', 3.0), ('GG', 5.0)
),
tamanho_do_cartao AS (
    SELECT r.grupo, r.cartao_numero,
           CASE UPPER(r.rotulo)
               WHEN 'PP' THEN 'PP' WHEN 'SIZE_PP' THEN 'PP'
               WHEN 'P'  THEN 'P'  WHEN 'SIZE_P'  THEN 'P'
               WHEN 'M'  THEN 'M'  WHEN 'SIZE_M'  THEN 'M'
               WHEN 'G'  THEN 'G'  WHEN 'SIZE_G'  THEN 'G'
               WHEN 'GG' THEN 'GG' WHEN 'SIZE_GG' THEN 'GG'
           END AS tamanho
    FROM v_cartoes_rotulos r
    WHERE UPPER(r.rotulo) IN ('PP', 'SIZE_PP', 'P', 'SIZE_P', 'M', 'SIZE_M',
                              'G', 'SIZE_G', 'GG', 'SIZE_GG')
),
integrantes AS (
    SELECT DISTINCT k.grupo, k.pessoa_id
    FROM kanban_eventos k
    JOIN pessoas p ON p.pessoa_id = k.pessoa_id
    WHERE p.grupo = k.grupo
),
-- Cartões fechados, um registro por responsável (sem responsável: '(vazio)')
cartoes_fechados AS (
    SELECT c.grupo, COALESCE(c.sprint, '(sem sprint)') AS sprint,
           COALESCE(r.pessoa_id, '(vazio)')            AS pessoa_id,
           COALESCE(r.peso_alocacao, 1.0)              AS peso,
           tm.dias_planejados
    FROM cartoes c
    LEFT JOIN v_cartoes_responsaveis_ids r
           ON r.grupo = c.grupo AND r.cartao_numero = c.cartao_numero
    LEFT JOIN tamanho_do_cartao t ON t.grupo = c.grupo AND t.cartao_numero = c.cartao_numero
    LEFT JOIN tamanhos tm         ON tm.tamanho = t.tamanho
    WHERE c.fechado_em IS NOT NULL
),
registros AS (
    SELECT grupo, sprint, pessoa_id, 'dias_planejados_concluidos' AS medida,
           peso * dias_planejados AS valor
    FROM cartoes_fechados WHERE dias_planejados IS NOT NULL
    UNION ALL
    SELECT grupo, sprint, pessoa_id, 'cartoes_concluidos', peso
    FROM cartoes_fechados
    UNION ALL
    SELECT c.grupo, NULL, c.autor_id, 'commits_autorais', 1
    FROM commits c
    JOIN grupos g ON g.grupo = c.grupo
    WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em
    UNION ALL
    SELECT grupo, COALESCE(sprint, '(sem sprint)'), autor_id, 'mrs_autorados', 1
    FROM merge_requests
),
-- Cada registro vale para a sprint dele e para '(todas)'
por_recorte AS (
    SELECT grupo, '(todas)' AS sprint, pessoa_id, medida, valor FROM registros
    UNION ALL
    SELECT grupo, sprint, pessoa_id, medida, valor FROM registros
    WHERE sprint IS NOT NULL AND sprint <> '(sem sprint)'
),
-- Integrante recebe o que é dele; o resto vira '(não atribuído)'. Registro de
-- pessoa de outro grupo também cai aqui: não é integrante deste grupo.
classificados AS (
    SELECT r.grupo, r.sprint, r.medida,
           CASE WHEN i.pessoa_id IS NOT NULL THEN r.pessoa_id ELSE '(não atribuído)' END AS pessoa_id,
           r.valor
    FROM por_recorte r
    LEFT JOIN integrantes i ON i.grupo = r.grupo AND i.pessoa_id = r.pessoa_id
),
-- Grade completa: todo integrante em todo recorte, para o zero não sumir
recortes AS (
    SELECT DISTINCT grupo, sprint, medida FROM por_recorte
),
grade AS (
    SELECT rc.grupo, rc.sprint, rc.medida, i.pessoa_id, 1 AS e_integrante
    FROM recortes rc JOIN integrantes i ON i.grupo = rc.grupo
    UNION ALL
    SELECT grupo, sprint, medida, '(não atribuído)', 0 FROM recortes
),
somados AS (
    SELECT gr.grupo, gr.sprint, gr.medida, gr.pessoa_id, gr.e_integrante,
           COALESCE(SUM(c.valor), 0) AS valor
    FROM grade gr
    LEFT JOIN classificados c
           ON c.grupo = gr.grupo AND c.sprint = gr.sprint
          AND c.medida = gr.medida AND c.pessoa_id = gr.pessoa_id
    GROUP BY gr.grupo, gr.sprint, gr.medida, gr.pessoa_id, gr.e_integrante
),
ordenados AS (
    SELECT grupo, sprint, medida, pessoa_id, valor,
           ROW_NUMBER() OVER (PARTITION BY grupo, sprint, medida ORDER BY valor, pessoa_id) AS i,
           COUNT(*)     OVER (PARTITION BY grupo, sprint, medida)                           AS n
    FROM somados
    WHERE e_integrante = 1
),
indice AS (
    SELECT grupo, sprint, medida,
           MAX(n)                                                    AS integrantes,
           SUM(valor)                                                AS total_integrantes,
           SUM((2 * i - n - 1) * valor) * 1.0 / (MAX(n) * SUM(valor)) AS gini,  -- * 1.0: sem divisão inteira
           MAX(valor)                                                AS maior_valor,
           SUM(valor = 0)                                            AS integrantes_sem_registro
    FROM ordenados
    GROUP BY grupo, sprint, medida
    HAVING SUM(valor) > 0
),
maior AS (
    SELECT grupo, sprint, medida, MIN(pessoa_id) AS pessoa_maior
    FROM ordenados o
    WHERE valor = (SELECT MAX(valor) FROM ordenados x
                   WHERE x.grupo = o.grupo AND x.sprint = o.sprint AND x.medida = o.medida)
    GROUP BY grupo, sprint, medida
)
SELECT
    ix.grupo,
    ix.sprint,
    ix.medida,
    ix.integrantes,
    ROUND(ix.total_integrantes, 2)                                          AS total_integrantes,
    ROUND(na.valor, 2)                                                      AS nao_atribuido,
    ROUND(100.0 * na.valor / (ix.total_integrantes + na.valor), 1)          AS pct_nao_atribuido,
    ROUND(ix.gini, 3)                                                       AS gini,
    ROUND((ix.integrantes - 1.0) / ix.integrantes, 3)                       AS gini_maximo_possivel,
    ROUND(100.0 * ix.maior_valor / ix.total_integrantes, 1)                 AS pct_do_maior,
    m.pessoa_maior,
    ROUND(100.0 / ix.integrantes, 1)                                        AS pct_divisao_igual,
    ix.integrantes_sem_registro
FROM indice ix
JOIN maior m    ON m.grupo = ix.grupo AND m.sprint = ix.sprint AND m.medida = ix.medida
JOIN somados na ON na.grupo = ix.grupo AND na.sprint = ix.sprint AND na.medida = ix.medida
               AND na.e_integrante = 0
ORDER BY ix.medida, ix.sprint, ix.grupo;
