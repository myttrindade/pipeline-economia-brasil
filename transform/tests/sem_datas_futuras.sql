-- A extração deve descartar observações com data futura (ex.: meta Selic já anunciada).
select *
from {{ ref('stg_bcb__observacoes') }}
where data > current_date
