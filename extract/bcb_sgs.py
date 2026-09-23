"""Extrai séries temporais do SGS (Banco Central do Brasil) e grava na camada raw do DuckDB.

Uso:
    python extract/bcb_sgs.py

Cada execução faz a carga completa das séries (são poucas milhares de linhas),
o que mantém o pipeline idempotente: rodar duas vezes gera o mesmo resultado.
"""

from __future__ import annotations

import csv
import logging
import time
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb
import requests

RAIZ = Path(__file__).resolve().parents[1]
BANCO = RAIZ / "data" / "economia.duckdb"
CATALOGO = RAIZ / "transform" / "seeds" / "series.csv"

DATA_INICIAL = date(2012, 1, 1)
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
# A API recusa consultas de séries diárias com janela maior que 10 anos.
JANELA_ANOS = 5
TENTATIVAS = 4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("extract")


def ler_catalogo() -> list[dict]:
    with CATALOGO.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def janelas(inicio: date, fim: date):
    atual = inicio
    while atual <= fim:
        proximo = date(atual.year + JANELA_ANOS, 1, 1)
        yield atual, min(fim, date(proximo.year - 1, 12, 31))
        atual = proximo


def buscar(codigo: int, inicio: date, fim: date) -> list[dict]:
    params = {
        "formato": "json",
        "dataInicial": inicio.strftime("%d/%m/%Y"),
        "dataFinal": fim.strftime("%d/%m/%Y"),
    }
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            r = requests.get(URL.format(codigo=codigo), params=params, timeout=60,
                             headers={"User-Agent": "pipeline-economia-brasil"})
            if r.status_code == 404:  # janela sem observações
                return []
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as erro:
            if tentativa == TENTATIVAS:
                raise
            espera = 2 ** tentativa
            log.warning("série %s: %s (nova tentativa em %ss)", codigo, erro, espera)
            time.sleep(espera)
    return []


def extrair_serie(codigo: int, hoje: date) -> list[tuple]:
    linhas = []
    for inicio, fim in janelas(DATA_INICIAL, hoje):
        for obs in buscar(codigo, inicio, fim):
            dia = datetime.strptime(obs["data"], "%d/%m/%Y").date()
            # A meta Selic vem com datas futuras (vale até a próxima reunião do Copom).
            if dia > hoje or obs["valor"] in ("", None):
                continue
            linhas.append((codigo, dia, float(obs["valor"])))
    return linhas


def main() -> None:
    hoje = date.today()
    extraido_em = datetime.now(timezone.utc).replace(tzinfo=None)
    BANCO.parent.mkdir(exist_ok=True)

    con = duckdb.connect(str(BANCO))
    con.execute("create schema if not exists raw")
    con.execute("""
        create table if not exists raw.bcb_sgs (
            codigo_serie integer,
            data date,
            valor double,
            extraido_em timestamp
        )
    """)

    for serie in ler_catalogo():
        codigo = int(serie["codigo_serie"])
        linhas = extrair_serie(codigo, hoje)
        if not linhas:
            raise RuntimeError(f"série {codigo} ({serie['nome']}) voltou vazia")
        con.execute("begin")
        con.execute("delete from raw.bcb_sgs where codigo_serie = ?", [codigo])
        con.executemany("insert into raw.bcb_sgs values (?, ?, ?, ?)",
                        [(*linha, extraido_em) for linha in linhas])
        con.execute("commit")
        log.info("série %s (%s): %s observações", codigo, serie["nome"], len(linhas))

    con.close()


if __name__ == "__main__":
    main()
