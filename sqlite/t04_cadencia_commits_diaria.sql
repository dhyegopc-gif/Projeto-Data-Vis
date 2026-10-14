-- Consulta 1: Contagem diária de commits por grupo (incluindo dias sem registro com valor 0)
WITH RECURSIVE
-- 0. Commits autorais do projeto: fora os herdados do repositório-template
--    (commitados antes da criação do grupo) e fora os merges
commits_projeto AS (
    SELECT c.grupo, c.autorado_em
    FROM commits c
    JOIN grupos g ON g.grupo = c.grupo
    WHERE c.commitado_em >= g.criado_em
      AND c.e_merge = 0
),
-- 1. Gerar o calendário contínuo de datas entre o menor e maior dia de commits
calendario(dia) AS (
    SELECT DATE(MIN(autorado_em)) FROM commits_projeto
    UNION ALL
    SELECT DATE(dia, '+1 day')
    FROM calendario
    WHERE dia < (SELECT DATE(MAX(autorado_em)) FROM commits_projeto)
),
-- 2. Selecionar os grupos existentes
lista_grupos AS (
    SELECT grupo FROM grupos
),
-- 3. Criar a grade completa de (grupo x dia) para não deixar buracos
grade_grupo_dia AS (
    SELECT g.grupo, c.dia
    FROM lista_grupos g
    CROSS JOIN calendario c
),
-- 4. Agrupar os commits autorais por grupo e dia
commits_agrupados AS (
    SELECT
        grupo,
        DATE(autorado_em) AS dia,
        COUNT(*) AS total_commits
    FROM commits_projeto
    GROUP BY grupo, DATE(autorado_em)
)
-- 5. Cruzar a grade completa com os commits contados
SELECT
    grid.grupo,
    grid.dia,
    COALESCE(ca.total_commits, 0) AS total_commits
FROM grade_grupo_dia grid
LEFT JOIN commits_agrupados ca
    ON grid.grupo = ca.grupo AND grid.dia = ca.dia
ORDER BY grid.grupo, grid.dia;
