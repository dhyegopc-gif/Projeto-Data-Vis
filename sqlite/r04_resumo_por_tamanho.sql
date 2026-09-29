-- R04: Resumo por grupo e tamanho do cartão
--
-- Mesmas regras de r04_prazo_planejado_realizado.sql (tamanho, dias planejados,
-- dias realizados, vínculo de commits). Uma linha por grupo x tamanho, mais uma
-- linha "(sem tamanho)" por grupo para os cartões que ficam fora do gráfico.
--
-- cartoes            todos os cartões do tamanho, abertos e fechados
-- no_grafico         fechados: os que o gráfico de dispersão mostra
-- mediana_*          mediana entre os cartões do gráfico
-- pct_acima_*        % dos cartões do gráfico que passaram do planejado / do dobro
-- commits_ligados    commits autorais citando os cartões do gráfico
WITH RECURSIVE
tamanhos(tamanho, ordem, dias_planejados) AS (
    VALUES ('PP', 1, 0.25), ('P', 2, 0.5), ('M', 3, 1.0), ('G', 4, 3.0), ('GG', 5, 5.0)
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
commits_do_cartao AS (
    SELECT v.grupo, v.numero AS cartao_numero, COUNT(*) AS commits_ligados
    FROM citacoes_validas v
    JOIN cartoes k ON k.grupo = v.grupo AND k.cartao_numero = v.numero
    GROUP BY v.grupo, v.numero
),
-- Todos os cartões, com tamanho (ou "(sem tamanho)") e as medidas do gráfico
base AS (
    SELECT c.grupo, c.cartao_numero,
           COALESCE(t.tamanho, '(sem tamanho)')            AS tamanho,
           COALESCE(tm.ordem, 9)                           AS ordem,
           tm.dias_planejados,
           c.fechado_em IS NOT NULL AND tm.tamanho IS NOT NULL AS no_grafico,
           JULIANDAY(c.fechado_em) - JULIANDAY(c.criado_em) AS dias_realizados,
           COALESCE(v.commits_ligados, 0)                  AS commits_ligados
    FROM cartoes c
    LEFT JOIN tamanho_do_cartao t ON t.grupo = c.grupo AND t.cartao_numero = c.cartao_numero
    LEFT JOIN tamanhos tm         ON tm.tamanho = t.tamanho
    LEFT JOIN commits_do_cartao v ON v.grupo = c.grupo AND v.cartao_numero = c.cartao_numero
),
-- Mediana: posição do meio numa lista ordenada (média dos dois do meio se par)
ordenados AS (
    SELECT grupo, tamanho, dias_realizados, commits_ligados,
           ROW_NUMBER() OVER (PARTITION BY grupo, tamanho ORDER BY dias_realizados) AS pos_dias,
           ROW_NUMBER() OVER (PARTITION BY grupo, tamanho ORDER BY commits_ligados) AS pos_commits,
           COUNT(*)     OVER (PARTITION BY grupo, tamanho)                          AS n
    FROM base WHERE no_grafico
),
medianas AS (
    SELECT grupo, tamanho,
           AVG(CASE WHEN pos_dias    IN ((n + 1) / 2, (n + 2) / 2) THEN dias_realizados END) AS mediana_dias,
           AVG(CASE WHEN pos_commits IN ((n + 1) / 2, (n + 2) / 2) THEN commits_ligados END) AS mediana_commits
    FROM ordenados
    GROUP BY grupo, tamanho
)
SELECT
    b.grupo,
    b.tamanho,
    MAX(b.dias_planejados)                                                     AS dias_planejados,
    COUNT(*)                                                                   AS cartoes,
    SUM(b.no_grafico)                                                          AS no_grafico,
    COUNT(*) - SUM(b.no_grafico)                                               AS fora_do_grafico,
    ROUND(m.mediana_dias, 2)                                                   AS mediana_dias_realizados,
    ROUND(m.mediana_dias / MAX(b.dias_planejados), 2)                          AS mediana_razao,
    ROUND(100.0 * SUM(b.no_grafico AND b.dias_realizados > b.dias_planejados)
          / NULLIF(SUM(b.no_grafico), 0), 1)                                   AS pct_acima_planejado,
    ROUND(100.0 * SUM(b.no_grafico AND b.dias_realizados > 2 * b.dias_planejados)
          / NULLIF(SUM(b.no_grafico), 0), 1)                                   AS pct_acima_dobro,
    m.mediana_commits                                                          AS mediana_commits_por_cartao,
    SUM(CASE WHEN b.no_grafico THEN b.commits_ligados ELSE 0 END)              AS commits_ligados,
    SUM(b.no_grafico AND b.commits_ligados = 0)                                AS cartoes_sem_commit
FROM base b
LEFT JOIN medianas m ON m.grupo = b.grupo AND m.tamanho = b.tamanho
GROUP BY b.grupo, b.tamanho, b.ordem
ORDER BY b.grupo, b.ordem;
