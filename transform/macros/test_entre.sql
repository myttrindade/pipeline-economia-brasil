{# Teste genérico: falha nas linhas em que a coluna fica fora do intervalo esperado. #}
{% test entre(model, column_name, minimo, maximo) %}
select *
from {{ model }}
where {{ column_name }} < {{ minimo }}
   or {{ column_name }} > {{ maximo }}
{% endtest %}
