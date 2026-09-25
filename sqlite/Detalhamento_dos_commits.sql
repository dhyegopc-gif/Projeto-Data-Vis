-- Consulta 2 (R01): Detalhamento dos commits de um grupo em uma data específica
-- Mesmo recorte do t04, para a lista bater com o total do dia no gráfico:
-- sem merges e sem os commits herdados do repositório-template.
SELECT
    c.grupo,
    c.commit_id,
    c.autor_id,
    c.autorado_em,
    c.titulo,
    c.linhas_adicionadas,
    c.linhas_removidas,
    c.linhas_total
FROM commits c
JOIN grupos g ON g.grupo = c.grupo
WHERE c.grupo = 'G01'                        -- Parâmetro de filtro por grupo
  AND DATE(c.autorado_em) = '2026-06-25'     -- Parâmetro de filtro por data selecionada
  AND c.e_merge = 0
  AND c.commitado_em >= g.criado_em
ORDER BY c.autorado_em ASC;
