with mensal as (

    select * from {{ ref('int_series__mensal') }}

),

pivotado as (

    select
        mes,
        max(case when serie = 'selic_meta'  then valor_fim_mes end) as selic_meta,
        max(case when serie = 'ipca_mensal' then valor_fim_mes end) as ipca_mensal,
        max(case when serie = 'ipca_12m'    then valor_fim_mes end) as ipca_12m,
        max(case when serie = 'dolar_ptax'  then valor_medio   end) as dolar_medio,
        max(case when serie = 'dolar_ptax'  then valor_fim_mes end) as dolar_fim_mes,
        max(case when serie = 'desocupacao' then valor_fim_mes end) as desocupacao
    from mensal
    group by mes

)

select
    mes,
    selic_meta,
    ipca_mensal,
    ipca_12m,
    -- Juro real ex-post: Selic descontada da inflação dos últimos 12 meses.
    round(((1 + selic_meta / 100) / (1 + ipca_12m / 100) - 1) * 100, 2) as juro_real,
    round(dolar_medio, 4) as dolar_medio,
    dolar_fim_mes,
    round((dolar_medio / lag(dolar_medio) over (order by mes) - 1) * 100, 2) as dolar_variacao_mensal,
    desocupacao,
    mes = date_trunc('month', current_date) as mes_em_andamento
from pivotado
order by mes
