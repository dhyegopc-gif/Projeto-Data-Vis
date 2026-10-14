-- R03: Cobertura do próprio registro, por campo e por grupo
--
-- Percentual de preenchimento sobre o total de registros do arquivo no grupo.
-- Nada é imputado nem corrigido: o vazio é o dado.
-- Autoria e responsável "resolvidos" = pessoa_id que não é sentinela
-- ([externo] ou [bot]), porque as sentinelas não existem em pessoas
-- (Contrato de dados). Preenchido com [externo] conta como vazio.
-- commits aparece duas vezes: o arquivo inteiro (a evidência do requisito)
-- e só a base que o R01 conta (sem merges e sem o histórico do template).
-- Duas medidas servem ao R04 e ao R05: cartão com rótulo de tamanho (P1..P8
-- são prioridade e não contam) e commit autoral que cita "#N" de um cartão do
-- próprio grupo (mesma regra de vínculo de r04_prazo_planejado_realizado.sql).
-- Uma serve ao R06: cartão com rótulo de eixo de tarefa (mesma tabela de
-- r06_cartoes_por_eixo.sql).
WITH RECURSIVE
commits_autorais AS (
    SELECT c.grupo, c.commit_id, c.titulo, c.mensagem
    FROM commits c
    JOIN grupos g ON g.grupo = c.grupo
    WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em
),
-- Cada passo corta o texto logo depois do próximo '#' (depois = 1).
trechos(grupo, commit_id, origem, resto, depois) AS (
    SELECT grupo, commit_id, 'titulo', titulo, 0
    FROM commits_autorais WHERE titulo LIKE '%#%'
    UNION ALL
    SELECT grupo, commit_id, 'mensagem', mensagem, 0
    FROM commits_autorais WHERE mensagem LIKE '%#%'
    UNION ALL
    SELECT grupo, commit_id, origem, SUBSTR(resto, INSTR(resto, '#') + 1), 1
    FROM trechos
    WHERE INSTR(resto, '#') > 0
),
-- O que vem depois do '#' começa com dígito: CAST lê o número inteiro (para
-- no primeiro não-dígito). Só vale se o número vem escrito sem zero à
-- esquerda e não é seguido de letra ou dígito: "#12)" e "#12 " contam;
-- "#12abc" e cores como "#9ab445" não.
candidatos AS (
    SELECT grupo, commit_id, origem, resto AS apos, CAST(resto AS INTEGER) AS numero
    FROM trechos
    WHERE depois = 1 AND SUBSTR(resto, 1, 1) BETWEEN '0' AND '9'
),
citacoes AS (
    SELECT DISTINCT grupo, commit_id, origem, numero
    FROM candidatos
    WHERE SUBSTR(apos, 1, LENGTH(CAST(numero AS TEXT))) = CAST(numero AS TEXT)
      AND SUBSTR(apos, LENGTH(CAST(numero AS TEXT)) + 1, 1) NOT GLOB '[A-Za-z0-9]'
),
citacoes_validas AS (
    SELECT grupo, commit_id, numero FROM citacoes WHERE origem = 'titulo'
    UNION
    SELECT m.grupo, m.commit_id, m.numero
    FROM citacoes m
    WHERE m.origem = 'mensagem'
      AND NOT EXISTS (SELECT 1 FROM citacoes t
                      WHERE t.origem = 'titulo' AND t.grupo = m.grupo AND t.commit_id = m.commit_id)
),
commits_com_cartao AS (
    SELECT DISTINCT v.grupo, v.commit_id
    FROM citacoes_validas v
    JOIN cartoes k ON k.grupo = v.grupo AND k.cartao_numero = v.numero
),
cartoes_com_eixo AS (
    SELECT DISTINCT grupo, cartao_numero
    FROM v_cartoes_rotulos
    WHERE UPPER(rotulo) IN ('CODE', 'BUG', 'FIX', 'TEST', 'DEPLOY', 'CODE_REVIEW', 'DESIGN',
                            'DOCUMENTATION', 'REQUIREMENTS', 'USER-STORY', 'NEGÓCIOS', 'PRESENTATION')
),
cartoes_com_tamanho AS (
    SELECT DISTINCT grupo, cartao_numero
    FROM v_cartoes_rotulos
    WHERE UPPER(rotulo) IN ('PP', 'SIZE_PP', 'P', 'SIZE_P', 'M', 'SIZE_M',
                            'G', 'SIZE_G', 'GG', 'SIZE_GG')
),
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
           'atribuir a pessoas os commits contados no gráfico de ritmo e na concentração por commits',
           'R01, R05'
    FROM commits c
    JOIN grupos g ON g.grupo = c.grupo
    WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em
    GROUP BY c.grupo

    UNION ALL
    SELECT grupo, 'cartoes', 'sprint',
           COUNT(*), SUM(sprint IS NOT NULL),
           'cortar por sprint: sem sprint o cartão cai em "(sem sprint)" e só aparece no recorte de todas as sprints',
           'R02, R04, R05, R06'
    FROM cartoes GROUP BY grupo

    UNION ALL
    SELECT grupo, 'cartoes', 'responsaveis_ids resolvido',
           COUNT(*), SUM(responsaveis_ids IS NOT NULL AND responsaveis_ids NOT IN ('[externo]', '[bot]')),
           'saber quem responde pelo cartão parado na etapa, a quem somar o cartão concluído na concentração e em que eixo de tarefa a pessoa está',
           'R02, R05, R06'
    FROM cartoes GROUP BY grupo

    UNION ALL
    SELECT c.grupo, 'cartoes', 'eixo de tarefa (rótulo CODE, DESIGN, DOCUMENTATION...)',
           COUNT(*), SUM(e.cartao_numero IS NOT NULL),
           'saber em que tipo de tarefa o integrante trabalhou: sem rótulo de eixo o cartão fica fora do radar',
           'R06'
    FROM cartoes c
    LEFT JOIN cartoes_com_eixo e ON e.grupo = c.grupo AND e.cartao_numero = c.cartao_numero
    GROUP BY c.grupo

    UNION ALL
    SELECT c.grupo, 'cartoes', 'tamanho (rótulo PP a GG)',
           COUNT(*), SUM(t.cartao_numero IS NOT NULL),
           'comparar planejado com realizado e pesar o cartão concluído: sem tamanho o cartão sai das duas telas',
           'R04, R05'
    FROM cartoes c
    LEFT JOIN cartoes_com_tamanho t ON t.grupo = c.grupo AND t.cartao_numero = c.cartao_numero
    GROUP BY c.grupo

    UNION ALL
    SELECT ca.grupo, 'commits', 'número do cartão (#N) na base do R01',
           COUNT(*), SUM(v.commit_id IS NOT NULL),
           'ligar o commit ao cartão: commit sem #N não entra na contagem de commits por cartão',
           'R04'
    FROM commits_autorais ca
    LEFT JOIN commits_com_cartao v ON v.grupo = ca.grupo AND v.commit_id = ca.commit_id
    GROUP BY ca.grupo

    UNION ALL
    SELECT grupo, 'cartoes', 'prazo_em',
           COUNT(*), SUM(prazo_em IS NOT NULL),
           'dizer se um cartão está atrasado (fora do escopo das telas)',
           '-'
    FROM cartoes GROUP BY grupo

    UNION ALL
    SELECT grupo, 'merge_requests', 'autor_id resolvido',
           COUNT(*), SUM(autor_id NOT IN ('[externo]', '[bot]')),
           'atribuir o merge request a uma pessoa na concentração por MRs',
           'R05'
    FROM merge_requests GROUP BY grupo

    UNION ALL
    SELECT grupo, 'merge_requests', 'sprint',
           COUNT(*), SUM(sprint IS NOT NULL),
           'cortar a concentração por MRs por sprint: sem sprint o MR só entra no recorte de todas as sprints',
           'R05'
    FROM merge_requests GROUP BY grupo

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
