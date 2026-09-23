with origem as (

    select * from {{ source('raw', 'bcb_sgs') }}

),

sem_duplicatas as (

    select *
    from origem
    qualify row_number() over (
        partition by codigo_serie, data
        order by extraido_em desc
    ) = 1

)

select
    o.codigo_serie,
    s.nome as serie,
    o.data,
    o.valor,
    o.extraido_em
from sem_duplicatas o
inner join {{ ref('series') }} s using (codigo_serie)
