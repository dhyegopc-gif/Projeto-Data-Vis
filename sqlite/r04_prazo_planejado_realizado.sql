-- R04: Tamanho planejado x tempo realizado, um cartão por linha
--
-- Grão: um cartão fechado que tem rótulo de tamanho, identificado por
-- (grupo, cartao_numero).
--
-- Tamanho: rótulo de cartoes.rotulos, em qualquer grafia (PP/SIZE_PP/size_PP,
-- P/SIZE_P, M/SIZE_M, G/SIZE_G, GG/SIZE_GG). Só o token exato conta: P1..P8 são
-- PRIORIDADE e não entram (Vocabulário, seção 8). Nenhum cartão tem dois tamanhos.
--
-- Dias planejados por tamanho. PREMISSA DO GRUPO, A CONFIRMAR com o professor:
--   PP = 0,25   P = 0,5   M = 1   G = 3   GG = 5
--
-- Dias realizados: fechado_em - criado_em, em dias corridos (noite e fim de
-- semana contam). Inclui a espera no Backlog antes de alguém pegar o cartão.
--
-- Commits ligados: commit autoral (sem merge, sem o histórico herdado do
-- template, o mesmo recorte do R01) que cita "#N" no título, onde N é o número
-- do cartão no mesmo grupo. Se o título não cita nenhum número, vale a
-- mensagem. Um commit que cita dois cartões conta nos dois.
WITH RECURSIVE
parametros AS (
    SELECT 1.0 AS limite_razao,      -- realizado/planejado acima disto: levou mais que o planejado
           2.0 AS limite_razao_alta  -- acima disto: levou mais que o dobro
),
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
-- Vínculo commit -> cartão ---------------------------------------------------
commits_autorais AS (
    SELECT c.grupo, c.commit_id, c.titulo, c.mensagem,
           c.linhas_adicionadas, c.linhas_removidas, c.autor_id
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
-- título primeiro; a mensagem só vale para quem não cita número no título
citacoes_validas AS (
    SELECT grupo, commit_id, numero FROM citacoes WHERE origem = 'titulo'
    UNION
    SELECT m.grupo, m.commit_id, m.numero
    FROM citacoes m
    WHERE m.origem = 'mensagem'
      AND NOT EXISTS (SELECT 1 FROM citacoes t
                      WHERE t.origem = 'titulo' AND t.grupo = m.grupo AND t.commit_id = m.commit_id)
),
vinculos AS (
    SELECT v.grupo, v.numero AS cartao_numero, ca.commit_id, ca.autor_id,
           ca.linhas_adicionadas + ca.linhas_removidas AS linhas
    FROM citacoes_validas v
    JOIN commits_autorais ca ON ca.grupo = v.grupo AND ca.commit_id = v.commit_id
    JOIN cartoes k ON k.grupo = v.grupo AND k.cartao_numero = v.numero
),
commits_do_cartao AS (
    SELECT grupo, cartao_numero,
           COUNT(*)                   AS commits_ligados,
           COUNT(DISTINCT autor_id)   AS autores_distintos,
           SUM(linhas)                AS linhas_alteradas
    FROM vinculos
    GROUP BY grupo, cartao_numero
)
SELECT
    c.grupo,
    c.cartao_numero,
    c.titulo,
    COALESCE(c.sprint, '(sem sprint)')                                  AS sprint,
    c.responsaveis_ids,
    t.tamanho,
    tm.ordem                                                            AS ordem_tamanho,
    tm.dias_planejados,
    c.criado_em,
    c.fechado_em,
    ROUND(JULIANDAY(c.fechado_em) - JULIANDAY(c.criado_em), 4)          AS dias_realizados,
    ROUND((JULIANDAY(c.fechado_em) - JULIANDAY(c.criado_em)) / tm.dias_planejados, 3)
                                                                        AS razao_realizado_planejado,
    CASE
        WHEN (JULIANDAY(c.fechado_em) - JULIANDAY(c.criado_em)) / tm.dias_planejados <= p.limite_razao
            THEN 'dentro do planejado'
        WHEN (JULIANDAY(c.fechado_em) - JULIANDAY(c.criado_em)) / tm.dias_planejados <= p.limite_razao_alta
            THEN 'até o dobro'
        ELSE 'mais que o dobro'
    END                                                                 AS faixa,
    COALESCE(v.commits_ligados, 0)                                      AS commits_ligados,
    COALESCE(v.autores_distintos, 0)                                    AS autores_distintos,
    COALESCE(v.linhas_alteradas, 0)                                     AS linhas_alteradas
FROM cartoes c
JOIN tamanho_do_cartao t ON t.grupo = c.grupo AND t.cartao_numero = c.cartao_numero
JOIN tamanhos tm         ON tm.tamanho = t.tamanho
LEFT JOIN commits_do_cartao v ON v.grupo = c.grupo AND v.cartao_numero = c.cartao_numero
CROSS JOIN parametros p
WHERE c.fechado_em IS NOT NULL
ORDER BY c.grupo, tm.ordem, c.cartao_numero;
