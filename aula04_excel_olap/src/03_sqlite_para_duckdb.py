"""Fase D - SQLite para DuckDB.

Conecta a saida/olist.duckdb, instala e carrega a extensão oficial sqlite, anexa
saida/olist.sqlite como sqlite_src (somente leitura) e materializa as nove tabelas
no catálogo main com CREATE OR REPLACE TABLE ... AS SELECT. As colunas de data,
guardadas como texto ISO 8601 no SQLite, viram TIMESTAMP por CAST explícito: um
valor fora do padrão interrompe a cópia em vez de virar texto. Executa ANALYZE,
reconcilia contagens (e nulos das colunas convertidas) e grava
saida/reconciliacao_duckdb.json. Falha se qualquer tabela divergir.
"""
import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent.parent
SQLITE = BASE / "saida" / "olist.sqlite"
DUCK = BASE / "saida" / "olist.duckdb"
DESTINO = BASE / "saida" / "reconciliacao_duckdb.json"

# Contrato de tipos do lado analítico: colunas de data passam a TIMESTAMP.
COLUNAS_TIMESTAMP = {
    "olist_orders": ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
                     "order_delivered_customer_date", "order_estimated_delivery_date"],
    "olist_order_items": ["shipping_limit_date"],
    "olist_order_reviews": ["review_creation_date", "review_answer_timestamp"],
}
TIPO_DUCK = {"TEXT": "VARCHAR", "INTEGER": "BIGINT", "REAL": "DOUBLE"}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    inicio = time.perf_counter()
    falhas = []

    # Catálogo e tipos declarados do SQLite (somente leitura).
    src = sqlite3.connect(SQLITE.resolve().as_uri() + "?mode=ro", uri=True)
    tabelas = [r[0] for r in src.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    colunas_sqlite = {t: [(r[1], r[2]) for r in src.execute(f"PRAGMA table_info('{t}')")] for t in tabelas}
    src.close()

    if DUCK.exists():
        DUCK.unlink()
    con = duckdb.connect(str(DUCK))
    t0 = time.perf_counter()
    con.execute("INSTALL sqlite")
    con.execute("LOAD sqlite")
    ext = con.execute("SELECT extension_name, loaded, installed, install_path, extension_version "
                      "FROM duckdb_extensions() WHERE extension_name = 'sqlite' OR list_contains(aliases, 'sqlite')").fetchone()
    seg_extensao = round(time.perf_counter() - t0, 3)
    con.execute(f"ATTACH '{SQLITE.as_posix()}' AS sqlite_src (TYPE sqlite, READ_ONLY)")

    tabelas_rel = []
    for t in tabelas:
        ts = set(COLUNAS_TIMESTAMP.get(t, []))
        selecao = ", ".join(f"CAST({c} AS TIMESTAMP) AS {c}" if c in ts else c for c, _ in colunas_sqlite[t])
        t1 = time.perf_counter()
        con.execute(f"CREATE OR REPLACE TABLE main.{t} AS SELECT {selecao} FROM sqlite_src.{t}")
        seg = round(time.perf_counter() - t1, 3)
        n_sqlite = con.execute(f"SELECT count(*) FROM sqlite_src.{t}").fetchone()[0]
        n_duck = con.execute(f"SELECT count(*) FROM main.{t}").fetchone()[0]
        tipos_duck = {r[0]: r[1] for r in con.execute(f"DESCRIBE main.{t}").fetchall()}
        tipos_esperados = {c: ("TIMESTAMP" if c in ts else TIPO_DUCK[tp]) for c, tp in colunas_sqlite[t]}
        nulos = []
        for c in sorted(ts):
            a = con.execute(f"SELECT count(*) FROM sqlite_src.{t} WHERE {c} IS NULL").fetchone()[0]
            b = con.execute(f"SELECT count(*) FROM main.{t} WHERE {c} IS NULL").fetchone()[0]
            nulos.append({"coluna": c, "nulos_sqlite": a, "nulos_duckdb": b, "confere": a == b})
            if a != b:
                falhas.append(f"{t}.{c}: nulos {a} no SQLite e {b} no DuckDB")
        if n_sqlite != n_duck:
            falhas.append(f"{t}: {n_sqlite} linhas no SQLite e {n_duck} no DuckDB")
        if tipos_duck != tipos_esperados:
            falhas.append(f"{t}: tipos {tipos_duck} diferem do esperado {tipos_esperados}")
        tabelas_rel.append({"tabela": t, "linhas_sqlite": n_sqlite, "linhas_duckdb": n_duck,
                            "confere": n_sqlite == n_duck, "tipos_duckdb": tipos_duck,
                            "colunas_convertidas_para_timestamp": nulos, "segundos_copia": seg})
        print(f"  {t}: SQLite {n_sqlite} | DuckDB {n_duck} | {seg} s", flush=True)

    con.execute("DETACH sqlite_src")
    t2 = time.perf_counter()
    con.execute("ANALYZE")
    seg_analyze = round(time.perf_counter() - t2, 3)

    nativas = con.execute("""
        SELECT table_name, table_type FROM information_schema.tables
        WHERE table_catalog = current_database() AND table_schema = 'main' ORDER BY table_name""").fetchall()
    n_nativas = sum(1 for _, tipo in nativas if tipo == "BASE TABLE")
    if sorted(n for n, _ in nativas) != sorted(tabelas) or n_nativas != len(tabelas):
        falhas.append(f"catálogo main do DuckDB: {nativas}")
    versao = con.execute("SELECT version()").fetchone()[0]
    con.close()

    rel = {
        "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "script": "src/03_sqlite_para_duckdb.py",
        "origem": "saida/olist.sqlite (ATTACH ... AS sqlite_src (TYPE sqlite, READ_ONLY))",
        "destino": "saida/olist.duckdb",
        "bytes_destino": DUCK.stat().st_size,
        "duckdb_version": versao,
        "extensao_sqlite": {"nome": ext[0], "carregada": ext[1], "instalada": ext[2],
                            "versao": ext[4], "segundos_install_load": seg_extensao} if ext else None,
        "tabelas_sqlite": len(tabelas),
        "tabelas_nativas_duckdb": n_nativas,
        "tabelas": tabelas_rel,
        "segundos_analyze": seg_analyze,
        "gate": {"falhas": falhas, "passou": not falhas},
        "segundos_total": round(time.perf_counter() - inicio, 3),
    }
    DESTINO.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"gravado {DESTINO.relative_to(BASE)} | tabelas nativas: {n_nativas} | DuckDB {versao}")
    if falhas:
        for f in falhas:
            print("FALHA:", f)
        raise SystemExit(1)
    print("GATE D PASSOU")


if __name__ == "__main__":
    main()
