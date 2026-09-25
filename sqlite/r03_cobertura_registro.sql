-- R03: Cobertura do próprio registro, por campo e por grupo
--
-- Percentual de preenchimento sobre o total de registros do arquivo no grupo.
-- Nada é imputado nem corrigido: o vazio é o dado.
-- Autoria "resolvida" = autor_id que não é sentinela ([externo] ou [bot]),
-- porque as sentinelas não existem em pessoas (Contrato de dados).
-- commits aparece duas vezes: o arquivo inteiro (a evidência do requisito)
-- e só a base que o R01 conta (sem merges e sem o histórico do template).
WITH
medidas AS (
    SELECT c.grupo,
           'commits' AS arquivo,
           'autor_id resolvido (arquivo inteiro)' AS campo,
           COUNT(*) AS registros,
           SUM(c.autor_id NOT IN ('[externo]', '[bot]')) AS preenchidos,
           'atribuir commits a pessoas: a coluna autor da lista de commits fica sem dono' AS o_que_inviabiliza,
           'R01' AS tela
    FROM commits c
    GROUP BY c.grupo

    UNION ALL
    SELECT c.grupo, 'commits', 'autor_id resolvido (base do R01)',
           COUNT(*),
           SUM(c.autor_id NOT IN ('[externo]', '[bot]')),
           'atribuir a pessoas os commits contados no gráfico de ritmo',
           'R01'
    FROM commits c
    JOIN grupos g ON g.grupo = c.grupo
    WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em
    GROUP BY c.grupo

    UNION ALL
    SELECT grupo, 'cartoes', 'sprint',
           COUNT(*), SUM(sprint IS NOT NULL),
           'cortar o acúmulo por sprint: sem sprint o cartão cai em "(sem sprint)"',
           'R02'
    FROM cartoes GROUP BY grupo

    UNION ALL
    SELECT grupo, 'cartoes', 'responsaveis_ids',
           COUNT(*), SUM(responsaveis_ids IS NOT NULL),
           'saber quem responde pelo cartão parado na etapa',
           'R02'
    FROM cartoes GROUP BY grupo

    UNION ALL
    SELECT grupo, 'cartoes', 'prazo_em',
           COUNT(*), SUM(prazo_em IS NOT NULL),
           'dizer se um cartão está atrasado (fora do escopo das telas)',
           '-'
    FROM cartoes GROUP BY grupo

    UNION ALL
    SELECT grupo, 'merge_requests', 'revisores_ids',
           COUNT(*), SUM(revisores_ids IS NOT NULL),
           'ler a espera em Waiting Review: sem revisor designado, não há de quem esperar',
           'R02'
    FROM merge_requests GROUP BY grupo

    UNION ALL
    SELECT grupo, 'sprints', 'inicio_em e prazo_em',
           COUNT(*), SUM(inicio_em IS NOT NULL AND prazo_em IS NOT NULL),
           'situar a sprint no calendário: o período do gráfico de ritmo não pode ser cortado por sprint',
           'R01, R02'
    FROM sprints GROUP BY grupo
)
SELECT
    grupo,
    arquivo,
    campo,
    registros,
    preenchidos,
    registros - preenchidos                         AS vazios,
    ROUND(100.0 * preenchidos / registros, 1)       AS pct_preenchido,
    o_que_inviabiliza,
    tela
FROM medidas
ORDER BY arquivo, campo, grupo;
