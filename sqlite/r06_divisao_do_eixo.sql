-- R06: Como os cartões de cada eixo de tarefa se dividem entre os 7
-- integrantes do grupo, por grupo e sprint
--
-- É a leitura principal da tela: a unidade é o grupo, e o integrante só
-- aparece como parte da divisão. Mesmas regras de r06_eixo_por_integrante.sql
-- (eixos, peso 1/eixos, integrante do R05, um responsável por cartão).
--
-- Uma linha por grupo × sprint × eixo:
--   cartoes_eixo          soma dos pesos do eixo nos cartões dos integrantes
--   integrantes_no_eixo   integrantes com algum cartão no eixo (de 0 a 7)
--   dois_maiores          soma dos pesos dos 2 integrantes com mais cartões no eixo
--   pct_dois_maiores      dois_maiores ÷ cartoes_eixo, em %; com divisão igual
--                         entre 7, seria 2/7 = 28,6%
--   parte_do_grupo        cartoes_eixo ÷ cartões com eixo do grupo, em %
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
por_recorte AS (
    SELECT grupo, cartao_numero, '(todas)' AS sprint, pessoa_id FROM cartoes_integrantes
    UNION ALL
    SELECT grupo, cartao_numero, sprint, pessoa_id FROM cartoes_integrantes
    WHERE sprint <> '(sem sprint)'
),
-- Peso de cada integrante em cada eixo, no recorte
por_pessoa AS (
    SELECT q.grupo, q.sprint, q.pessoa_id, e.eixo, SUM(1.0 / n.n) AS peso
    FROM por_recorte q
    JOIN eixo_do_cartao e ON e.grupo = q.grupo AND e.cartao_numero = q.cartao_numero
    JOIN qtd n            ON n.grupo = q.grupo AND n.cartao_numero = q.cartao_numero
    GROUP BY 1, 2, 3, 4
),
ordenado AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY grupo, sprint, eixo ORDER BY peso DESC, pessoa_id) AS posicao
    FROM por_pessoa
),
total_grupo AS (
    SELECT grupo, sprint, SUM(peso) AS cartoes_com_eixo FROM por_pessoa GROUP BY 1, 2
),
recortes AS (
    SELECT DISTINCT grupo, sprint FROM por_recorte
)
SELECT
    r.grupo, r.sprint, l.eixo, l.ordem,
    ROUND(COALESCE(SUM(o.peso), 0), 4)                                              AS cartoes_eixo,
    COUNT(o.pessoa_id)                                                              AS integrantes_no_eixo,
    ROUND(COALESCE(SUM(CASE WHEN o.posicao <= 2 THEN o.peso END), 0), 4)            AS dois_maiores,
    ROUND(100.0 * SUM(CASE WHEN o.posicao <= 2 THEN o.peso END) / NULLIF(SUM(o.peso), 0), 1) AS pct_dois_maiores,
    ROUND(100.0 * COALESCE(SUM(o.peso), 0) / NULLIF(t.cartoes_com_eixo, 0), 1)       AS parte_do_grupo
FROM recortes r
CROSS JOIN lista_eixos l
LEFT JOIN ordenado o    ON o.grupo = r.grupo AND o.sprint = r.sprint AND o.eixo = l.eixo
LEFT JOIN total_grupo t ON t.grupo = r.grupo AND t.sprint = r.sprint
GROUP BY r.grupo, r.sprint, l.eixo, l.ordem
ORDER BY r.grupo, r.sprint, l.ordem;
