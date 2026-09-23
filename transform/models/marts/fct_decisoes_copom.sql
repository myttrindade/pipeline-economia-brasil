-- Cada mudança na meta Selic corresponde a uma decisão do Copom.

with selic as (

    select data, valor as selic_meta
    from {{ ref('stg_bcb__observacoes') }}
    where serie = 'selic_meta'

),

com_anterior as (

    select
        data,
        selic_meta,
        lag(selic_meta) over (order by data) as selic_anterior
    from selic

)

select
    data as data_vigencia,
    selic_anterior,
    selic_meta as selic_nova,
    round(selic_meta - selic_anterior, 2) as variacao_pp,
    case
        when selic_meta > selic_anterior then 'alta'
        else 'corte'
    end as direcao
from com_anterior
where selic_anterior is not null
  and selic_meta <> selic_anterior
order by data_vigencia
