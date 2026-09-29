
-- Consulta 2: Detalhamento dos commits de um grupo em uma data específica
SELECT 
    commit_id,
    autor_id,
    autorado_em,
    titulo,
    linhas_adicionadas,
    linhas_removidas,
    linhas_total
FROM commits
WHERE grupo = 'G01'                -- Parâmetro de filtro por grupo
  AND DATE(autorado_em) = '2026-06-25' -- Parâmetro de filtro por data selecionada
  AND e_merge = 0
ORDER BY autorado_em ASC;

