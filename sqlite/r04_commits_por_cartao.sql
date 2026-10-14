-- R04: Commits ligados a cada cartão (um vínculo commit -> cartão por linha)
--
-- Detalhe que a tela abre ao clicar num cartão. Mesma regra de vínculo de
-- r04_prazo_planejado_realizado.sql:
--   - commit autoral: sem merge e sem o histórico herdado do template (R01);
--   - "#N" no título casa com o cartão N do MESMO grupo; se o título não cita
--     número nenhum, vale a mensagem;
--   - um commit que cita dois cartões aparece nas duas linhas.
-- Citação que não casa com cartão do grupo (numero_sem_cartao) fica listada
-- no fim, com cartao_numero nulo, para a conta de cobertura não esconder nada.
WITH RECURSIVE
commits_autorais AS (
    SELECT c.grupo, c.commit_id, c.titulo, c.mensagem, c.autor_id, c.autorado_em,
           c.linhas_adicionadas, c.linhas_removidas
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
    SELECT grupo, commit_id, origem, numero FROM citacoes WHERE origem = 'titulo'
    UNION
    SELECT m.grupo, m.commit_id, m.origem, m.numero
    FROM citacoes m
    WHERE m.origem = 'mensagem'
      AND NOT EXISTS (SELECT 1 FROM citacoes t
                      WHERE t.origem = 'titulo' AND t.grupo = m.grupo AND t.commit_id = m.commit_id)
)
SELECT
    v.grupo,
    k.cartao_numero,
    v.numero                                        AS numero_citado,
    CASE WHEN k.cartao_numero IS NULL THEN 1 ELSE 0 END AS numero_sem_cartao,
    v.origem                                        AS citado_no,
    ca.commit_id,
    ca.autor_id,
    ca.autorado_em,
    ca.titulo,
    ca.linhas_adicionadas,
    ca.linhas_removidas
FROM citacoes_validas v
JOIN commits_autorais ca ON ca.grupo = v.grupo AND ca.commit_id = v.commit_id
LEFT JOIN cartoes k      ON k.grupo = v.grupo AND k.cartao_numero = v.numero
ORDER BY numero_sem_cartao, v.grupo, k.cartao_numero, ca.autorado_em;
