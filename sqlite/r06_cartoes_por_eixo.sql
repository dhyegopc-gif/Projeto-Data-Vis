-- R06: Eixo de tarefa de cada cartão, com o responsável
--
-- Um cartão por linha (os 1.238). O eixo vem dos rótulos de tipo de tarefa
-- (PREMISSA DO GRUPO, o agrupamento dos rótulos em quatro eixos):
--   Código        CODE, BUG, Fix, TEST, DEPLOY, CODE_REVIEW
--   Design        DESIGN (não há rótulo UX no conjunto; DESIGN é o mais próximo)
--   Documentação  DOCUMENTATION, REQUIREMENTS, user-story
--   Negócio       NEGÓCIOS (só G01), Presentation (só G02)
-- Os demais rótulos não são tipo de tarefa: tamanho (PP a GG), prioridade
-- (P1–P8), artefato (ART.N), etapa do quadro (Backlog, Doing, Review...) e
-- COMP (um cartão, sentido desconhecido).
--
-- Cartão com rótulos de dois eixos conta metade em cada um (peso = 1/eixos),
-- para a soma de cada integrante fechar em 100%. Cartão sem rótulo de eixo
-- fica com eixos = NULL: aparece como "sem eixo" e fica fora do radar.
--
-- Integrante: o mesmo critério do R05 (pessoa do cadastro do grupo com pelo
-- menos um movimento no quadro do próprio grupo; 7 por grupo).
WITH
eixos(rotulo, eixo, ordem) AS (
    VALUES ('CODE', 'Código', 1), ('BUG', 'Código', 1), ('FIX', 'Código', 1),
           ('TEST', 'Código', 1), ('DEPLOY', 'Código', 1), ('CODE_REVIEW', 'Código', 1),
           ('DESIGN', 'Design', 2),
           ('DOCUMENTATION', 'Documentação', 3), ('REQUIREMENTS', 'Documentação', 3),
           ('USER-STORY', 'Documentação', 3),
           ('NEGÓCIOS', 'Negócio', 4), ('PRESENTATION', 'Negócio', 4)
),
integrantes AS (
    SELECT DISTINCT k.grupo, k.pessoa_id
    FROM kanban_eventos k
    JOIN pessoas p ON p.pessoa_id = k.pessoa_id
    WHERE p.grupo = k.grupo
),
eixo_do_cartao AS (
    SELECT DISTINCT r.grupo, r.cartao_numero, e.eixo, e.ordem
    FROM v_cartoes_rotulos r
    JOIN eixos e ON e.rotulo = UPPER(r.rotulo)
),
por_cartao AS (
    SELECT grupo, cartao_numero,
           GROUP_CONCAT(eixo, ';') AS eixos,
           COUNT(*)                AS qtd_eixos
    FROM (SELECT * FROM eixo_do_cartao ORDER BY grupo, cartao_numero, ordem)
    GROUP BY grupo, cartao_numero
)
SELECT
    c.grupo,
    c.cartao_numero,
    c.titulo,
    COALESCE(c.sprint, '(sem sprint)')                        AS sprint,
    CASE WHEN c.fechado_em IS NULL THEN 'aberto' ELSE 'fechado' END AS situacao,
    COALESCE(c.responsaveis_ids, '(vazio)')                   AS responsavel,
    CASE WHEN i.pessoa_id IS NULL THEN 0 ELSE 1 END           AS e_integrante,
    pc.eixos,
    COALESCE(pc.qtd_eixos, 0)                                 AS qtd_eixos,
    c.rotulos
FROM cartoes c
LEFT JOIN integrantes i ON i.grupo = c.grupo AND i.pessoa_id = c.responsaveis_ids
LEFT JOIN por_cartao pc ON pc.grupo = c.grupo AND pc.cartao_numero = c.cartao_numero
ORDER BY c.grupo, c.cartao_numero;
