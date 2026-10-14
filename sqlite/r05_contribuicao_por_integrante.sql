-- R05: Contribuição registrada de cada integrante, por grupo, sprint e medida
--
-- Integrante (PREMISSA DO GRUPO): pessoa do roster do grupo (pessoas.grupo)
-- que fez pelo menos um evento no quadro do próprio grupo. Dá 7 por grupo e
-- deixa de fora os maintainers sem registro nenhum e quem só aparece em outro
-- grupo. pessoas.grupo aqui é critério de pertencimento, não chave de junção:
-- a junção de pessoa continua sendo só por pessoa_id (Contrato de dados).
--
-- Medidas (valor por integrante; integrante sem registro entra com 0):
--   dias_planejados_concluidos  PRINCIPAL. Soma, por responsável, dos dias
--                               planejados dos cartões fechados com tamanho
--                               (PP 0,25 · P 0,5 · M 1 · G 3 · GG 5, premissa
--                               do R04). Cartão com mais de um responsável
--                               divide o valor (peso_alocacao).
--   cartoes_concluidos          Cartões fechados por responsável, de qualquer
--                               tamanho (com peso_alocacao).
--   commits_autorais            Commits sem merge e sem o histórico do template
--                               (recorte do R01), por autor. Sem sprint.
--   mrs_autorados               Merge requests por autor.
--
-- O que não tem dono identificado ([externo], [bot], responsável vazio) não
-- entra no índice: aparece na linha pessoa_id = '(não atribuído)', com
-- e_integrante = 0, para a tela mostrar a parcela e o intervalo possível.
--
-- sprint = '(todas)' soma o período inteiro, inclusive cartões e MRs sem sprint.
-- commits_autorais só existe em '(todas)': commit não tem sprint no dado.
WITH
tamanhos(tamanho, dias_planejados) AS (
    VALUES ('PP', 0.25), ('P', 0.5), ('M', 1.0), ('G', 3.0), ('GG', 5.0)
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
integrantes AS (
    SELECT DISTINCT k.grupo, k.pessoa_id
    FROM kanban_eventos k
    JOIN pessoas p ON p.pessoa_id = k.pessoa_id
    WHERE p.grupo = k.grupo
),
-- Cartões fechados, um registro por responsável (sem responsável: '(vazio)')
cartoes_fechados AS (
    SELECT c.grupo, COALESCE(c.sprint, '(sem sprint)') AS sprint,
           COALESCE(r.pessoa_id, '(vazio)')            AS pessoa_id,
           COALESCE(r.peso_alocacao, 1.0)              AS peso,
           tm.dias_planejados
    FROM cartoes c
    LEFT JOIN v_cartoes_responsaveis_ids r
           ON r.grupo = c.grupo AND r.cartao_numero = c.cartao_numero
    LEFT JOIN tamanho_do_cartao t ON t.grupo = c.grupo AND t.cartao_numero = c.cartao_numero
    LEFT JOIN tamanhos tm         ON tm.tamanho = t.tamanho
    WHERE c.fechado_em IS NOT NULL
),
registros AS (
    SELECT grupo, sprint, pessoa_id, 'dias_planejados_concluidos' AS medida,
           peso * dias_planejados AS valor
    FROM cartoes_fechados WHERE dias_planejados IS NOT NULL
    UNION ALL
    SELECT grupo, sprint, pessoa_id, 'cartoes_concluidos', peso
    FROM cartoes_fechados
    UNION ALL
    SELECT c.grupo, NULL, c.autor_id, 'commits_autorais', 1
    FROM commits c
    JOIN grupos g ON g.grupo = c.grupo
    WHERE c.e_merge = 0 AND c.commitado_em >= g.criado_em
    UNION ALL
    SELECT grupo, COALESCE(sprint, '(sem sprint)'), autor_id, 'mrs_autorados', 1
    FROM merge_requests
),
-- Cada registro vale para a sprint dele e para '(todas)'
por_recorte AS (
    SELECT grupo, '(todas)' AS sprint, pessoa_id, medida, valor FROM registros
    UNION ALL
    SELECT grupo, sprint, pessoa_id, medida, valor FROM registros
    WHERE sprint IS NOT NULL AND sprint <> '(sem sprint)'
),
-- Integrante recebe o que é dele; o resto vira '(não atribuído)'. Registro de
-- pessoa de outro grupo também cai aqui: não é integrante deste grupo.
classificados AS (
    SELECT r.grupo, r.sprint, r.medida,
           CASE WHEN i.pessoa_id IS NOT NULL THEN r.pessoa_id ELSE '(não atribuído)' END AS pessoa_id,
           r.valor
    FROM por_recorte r
    LEFT JOIN integrantes i ON i.grupo = r.grupo AND i.pessoa_id = r.pessoa_id
),
-- Grade completa: todo integrante em todo recorte, para o zero não sumir
recortes AS (
    SELECT DISTINCT grupo, sprint, medida FROM por_recorte
),
grade AS (
    SELECT rc.grupo, rc.sprint, rc.medida, i.pessoa_id, 1 AS e_integrante
    FROM recortes rc JOIN integrantes i ON i.grupo = rc.grupo
    UNION ALL
    SELECT grupo, sprint, medida, '(não atribuído)', 0 FROM recortes
),
somados AS (
    SELECT gr.grupo, gr.sprint, gr.medida, gr.pessoa_id, gr.e_integrante,
           COALESCE(SUM(c.valor), 0) AS valor
    FROM grade gr
    LEFT JOIN classificados c
           ON c.grupo = gr.grupo AND c.sprint = gr.sprint
          AND c.medida = gr.medida AND c.pessoa_id = gr.pessoa_id
    GROUP BY gr.grupo, gr.sprint, gr.medida, gr.pessoa_id, gr.e_integrante
)
SELECT
    grupo, sprint, medida, pessoa_id, e_integrante,
    ROUND(valor, 4)                                                   AS valor,
    ROUND(100.0 * valor / NULLIF(SUM(CASE WHEN e_integrante = 1 THEN valor END)
          OVER (PARTITION BY grupo, sprint, medida), 0), 1)            AS pct_dos_integrantes
FROM somados
ORDER BY grupo, medida, sprint, e_integrante DESC, valor DESC, pessoa_id;
