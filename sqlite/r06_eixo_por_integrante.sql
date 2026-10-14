-- R06: Parte de cada eixo de tarefa nos cartões de cada integrante,
-- por grupo e sprint
--
-- Mesmas regras de r06_cartoes_por_eixo.sql (eixos, peso 1/eixos, integrante
-- do R05). Cada cartão tem um responsável só no conjunto (1.201 cartões com
-- responsável, 1.201 linhas em v_cartoes_responsaveis_ids).
--
-- Uma linha por grupo × sprint × integrante × eixo, com zero quando o
-- integrante não tem cartão naquele eixo (o zero não some do radar):
--   cartoes        soma dos pesos (cartão de dois eixos conta 0,5 em cada)
--   pct            parte do eixo no total do integrante, em %
--   cartoes_total  cartões com eixo do integrante no recorte
--   sem_eixo       cartões do integrante sem rótulo de eixo (fora do %)
-- Linha pessoa_id = '(grupo)': o perfil do grupo inteiro, com os cartões de
-- todos os integrantes, para servir de referência no radar.
--
-- sprint = '(todas)' soma o período inteiro, inclusive cartões sem sprint.
-- Cartões sem responsável ou de quem não é integrante ficam fora.
WITH
eixos(rotulo, eixo, ordem) AS (
    VALUES ('CODE', 'Código', 1), ('BUG', 'Código', 1), ('FIX', 'Código', 1),
           ('TEST', 'Código', 1), ('DEPLOY', 'Código', 1), ('CODE_REVIEW', 'Código', 1),
           ('DESIGN', 'Design', 2),
           ('DOCUMENTATION', 'Documentação', 3), ('REQUIREMENTS', 'Documentação', 3),
           ('USER-STORY', 'Documentação', 3),
           ('NEGÓCIOS', 'Negócio', 4), ('PRESENTATION', 'Negócio', 4)
),
lista_eixos AS (
    SELECT DISTINCT eixo, ordem FROM eixos
),
integrantes AS (
    SELECT DISTINCT k.grupo, k.pessoa_id
    FROM kanban_eventos k
    JOIN pessoas p ON p.pessoa_id = k.pessoa_id
    WHERE p.grupo = k.grupo
),
eixo_do_cartao AS (
    SELECT DISTINCT r.grupo, r.cartao_numero, e.eixo
    FROM v_cartoes_rotulos r
    JOIN eixos e ON e.rotulo = UPPER(r.rotulo)
),
qtd AS (
    SELECT grupo, cartao_numero, COUNT(*) AS n FROM eixo_do_cartao GROUP BY 1, 2
),
cartoes_integrantes AS (
    SELECT c.grupo, c.cartao_numero, COALESCE(c.sprint, '(sem sprint)') AS sprint,
           c.responsaveis_ids AS pessoa_id
    FROM cartoes c
    JOIN integrantes i ON i.grupo = c.grupo AND i.pessoa_id = c.responsaveis_ids
),
-- Cada cartão vale para a sprint dele e para '(todas)'
por_recorte AS (
    SELECT grupo, cartao_numero, '(todas)' AS sprint, pessoa_id FROM cartoes_integrantes
    UNION ALL
    SELECT grupo, cartao_numero, sprint, pessoa_id FROM cartoes_integrantes
    WHERE sprint <> '(sem sprint)'
),
-- Integrante e '(grupo)': o mesmo cartão entra nas duas visões
quem AS (
    SELECT grupo, cartao_numero, sprint, pessoa_id FROM por_recorte
    UNION ALL
    SELECT grupo, cartao_numero, sprint, '(grupo)' FROM por_recorte
),
pesos AS (
    SELECT q.grupo, q.sprint, q.pessoa_id, e.eixo, 1.0 / n.n AS peso
    FROM quem q
    JOIN eixo_do_cartao e ON e.grupo = q.grupo AND e.cartao_numero = q.cartao_numero
    JOIN qtd n            ON n.grupo = q.grupo AND n.cartao_numero = q.cartao_numero
),
totais AS (
    SELECT q.grupo, q.sprint, q.pessoa_id,
           SUM(n.n IS NOT NULL) AS cartoes_total,
           SUM(n.n IS NULL)     AS sem_eixo
    FROM quem q
    LEFT JOIN qtd n ON n.grupo = q.grupo AND n.cartao_numero = q.cartao_numero
    GROUP BY 1, 2, 3
),
-- Grade completa: todo integrante em toda sprint em que o grupo tem cartão,
-- com os quatro eixos
recortes AS (
    SELECT DISTINCT grupo, sprint FROM por_recorte
),
grade AS (
    SELECT r.grupo, r.sprint, i.pessoa_id, 1 AS e_integrante, l.eixo, l.ordem
    FROM recortes r JOIN integrantes i ON i.grupo = r.grupo CROSS JOIN lista_eixos l
    UNION ALL
    SELECT r.grupo, r.sprint, '(grupo)', 0, l.eixo, l.ordem
    FROM recortes r CROSS JOIN lista_eixos l
)
SELECT
    g.grupo, g.sprint, g.pessoa_id, g.e_integrante, g.eixo, g.ordem,
    ROUND(COALESCE(SUM(p.peso), 0), 4)                                   AS cartoes,
    ROUND(100.0 * COALESCE(SUM(p.peso), 0) / NULLIF(t.cartoes_total, 0), 1) AS pct,
    COALESCE(t.cartoes_total, 0)                                         AS cartoes_total,
    COALESCE(t.sem_eixo, 0)                                              AS sem_eixo
FROM grade g
LEFT JOIN pesos p
       ON p.grupo = g.grupo AND p.sprint = g.sprint AND p.pessoa_id = g.pessoa_id AND p.eixo = g.eixo
LEFT JOIN totais t
       ON t.grupo = g.grupo AND t.sprint = g.sprint AND t.pessoa_id = g.pessoa_id
GROUP BY g.grupo, g.sprint, g.pessoa_id, g.e_integrante, g.eixo, g.ordem
ORDER BY g.grupo, g.sprint, g.e_integrante, g.pessoa_id, g.ordem;
