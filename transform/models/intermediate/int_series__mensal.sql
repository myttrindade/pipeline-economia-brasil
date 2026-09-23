-- Leva todas as séries para o grão mensal.
-- Séries diárias viram média do mês e último valor do mês; séries mensais ficam iguais nas duas colunas.

select
    serie,
    date_trunc('month', data)::date as mes,
    avg(valor) as valor_medio,
    arg_max(valor, data) as valor_fim_mes,
    count(*) as observacoes
from {{ ref('stg_bcb__observacoes') }}
group by 1, 2
