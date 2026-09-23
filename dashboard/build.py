"""Gera o dashboard estático (site/) a partir das tabelas da camada marts.

Uso:
    python dashboard/build.py
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
BANCO = RAIZ / "data" / "economia.duckdb"
TEMPLATE = RAIZ / "dashboard" / "template.html"
SAIDA = RAIZ / "site"


def registros(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    rel = con.sql(sql)
    colunas = rel.columns
    return [
        {c: (v.isoformat() if isinstance(v, date) else v) for c, v in zip(colunas, linha)}
        for linha in rel.fetchall()
    ]


def main() -> None:
    con = duckdb.connect(str(BANCO), read_only=True)
    dados = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "mensal": registros(con, "select * exclude (mes_em_andamento) from marts.fct_indicadores_mensais order by mes"),
        "copom": registros(con, "select * from marts.fct_decisoes_copom order by data_vigencia"),
    }

    (SAIDA / "dados").mkdir(parents=True, exist_ok=True)
    con.sql("select * from marts.fct_indicadores_mensais order by mes").write_csv(
        str(SAIDA / "dados" / "indicadores_mensais.csv"))
    con.close()

    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DADOS__*/null", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))
    (SAIDA / "index.html").write_text(html, encoding="utf-8")
    print(f"site gerado: {len(dados['mensal'])} meses, {len(dados['copom'])} decisões do Copom")


if __name__ == "__main__":
    main()
