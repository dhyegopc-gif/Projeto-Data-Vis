"""Comparação da mesma consulta mensal no SQLite e no DuckDB (seção 4 do roteiro).

A consulta junta itens e pedidos e agrega receita, pedidos distintos e itens por
mês da compra. No SQLite ela lê olist_order_items/olist_orders; no DuckDB, as
mesmas tabelas já nativas (não o mart), para que o trabalho seja equivalente.
A receita é somada em centavos inteiros para que os dois resultados possam ser
comparados linha a linha sem diferença de arredondamento.

Execução fria: cinco processos novos, cada um abre a conexão e roda a consulta
uma vez. Execução aquecida: um processo, uma conexão, uma execução descartada e
cinco medidas. Registra a mediana, a máquina e as versões em
saida/medicoes_tempo.json, junto com os tempos totais de cada etapa do pipeline.
O cache de arquivos do sistema operacional não é esvaziado entre execuções.
"""
import ctypes
import json
import os
import platform
import sqlite3
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent.parent
SAIDA = BASE / "saida"
SQLITE = SAIDA / "olist.sqlite"
DUCK = SAIDA / "olist.duckdb"
DESTINO = SAIDA / "medicoes_tempo.json"
EXECUCOES = 5

SQL = {
    "sqlite": """
        SELECT substr(o.order_purchase_timestamp, 1, 7) AS mes,
               sum(CAST(round(i.price * 100) AS INTEGER)) AS receita_centavos,
               count(DISTINCT i.order_id) AS pedidos,
               count(*) AS itens
        FROM olist_order_items AS i
        JOIN olist_orders AS o ON o.order_id = i.order_id
        GROUP BY mes ORDER BY mes""",
    "duckdb": """
        SELECT strftime(o.order_purchase_timestamp, '%Y-%m') AS mes,
               sum(CAST(round(i.price * 100) AS BIGINT)) AS receita_centavos,
               count(DISTINCT i.order_id) AS pedidos,
               count(*) AS itens
        FROM olist_order_items AS i
        JOIN olist_orders AS o ON o.order_id = i.order_id
        GROUP BY mes ORDER BY mes""",
}


def conectar(motor):
    if motor == "sqlite":
        return sqlite3.connect(SQLITE.resolve().as_uri() + "?mode=ro", uri=True)
    return duckdb.connect(str(DUCK), read_only=True)


def medir(con, motor):
    t0 = time.perf_counter()
    linhas = con.execute(SQL[motor]).fetchall()
    return (time.perf_counter() - t0) * 1000, linhas


def uma_execucao_fria(motor):
    """Processo filho: abre a conexão, executa uma vez e devolve JSON no stdout."""
    t0 = time.perf_counter()
    con = conectar(motor)
    ms_conexao = (time.perf_counter() - t0) * 1000
    ms, linhas = medir(con, motor)
    con.close()
    print(json.dumps({"ms": ms, "ms_conexao": ms_conexao, "linhas": [list(r) for r in linhas]}))


def maquina():
    info = {
        "sistema": platform.platform(),
        "arquitetura": platform.machine(),
        "processador": platform.processor(),
        "nucleos_logicos": os.cpu_count(),
        "python": sys.version.split()[0],
        "sqlite": sqlite3.sqlite_version,
        "duckdb": duckdb.__version__,
    }
    if sys.platform == "win32":
        try:
            import winreg
            chave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            info["processador"] = winreg.QueryValueEx(chave, "ProcessorNameString")[0].strip()
        except OSError:
            pass

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MEMORYSTATUSEX()
        m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            info["memoria_gib"] = round(m.ullTotalPhys / 2 ** 30, 1)
    return info


def resumo(valores):
    return {"execucoes_ms": [round(v, 3) for v in valores], "mediana_ms": round(statistics.median(valores), 3),
            "min_ms": round(min(valores), 3), "max_ms": round(max(valores), 3)}


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--fria":
        uma_execucao_fria(sys.argv[2])
        return
    sys.stdout.reconfigure(encoding="utf-8")
    resultados, linhas_por_motor = {}, {}
    for motor in ("sqlite", "duckdb"):
        frias, conexoes = [], []
        for _ in range(EXECUCOES):
            saida = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--fria", motor],
                                   capture_output=True, text=True, check=True)
            r = json.loads(saida.stdout)
            frias.append(r["ms"])
            conexoes.append(r["ms_conexao"])
            linhas_por_motor.setdefault(motor, r["linhas"])
        con = conectar(motor)
        threads = con.execute("SELECT current_setting('threads')").fetchone()[0] if motor == "duckdb" else 1
        descartada, _ = medir(con, motor)
        quentes = []
        for _ in range(EXECUCOES):
            ms, linhas = medir(con, motor)
            quentes.append(ms)
        con.close()
        resultados[motor] = {
            "fria": resumo(frias),
            "conexao_na_fria": resumo(conexoes),
            "aquecida": resumo(quentes),
            "aquecimento_descartado_ms": round(descartada, 3),
            "threads": threads,
            "linhas_resultado": len(linhas),
        }
        print(f"{motor}: fria mediana {resultados[motor]['fria']['mediana_ms']} ms | "
              f"aquecida mediana {resultados[motor]['aquecida']['mediana_ms']} ms", flush=True)

    a = [tuple(r) for r in linhas_por_motor["sqlite"]]
    b = [tuple(r) for r in linhas_por_motor["duckdb"]]
    mesmo_resultado = a == b
    totais = {m: {"meses": len(l), "receita_centavos": sum(r[1] for r in l), "pedidos": sum(r[2] for r in l),
                  "itens": sum(r[3] for r in l)} for m, l in linhas_por_motor.items()}

    etapas = {}
    for nome, arq in [("00_perfil_excel", "perfil_excel.json"), ("01_excel_para_sqlite", "carga_sqlite.json"),
                      ("03_sqlite_para_duckdb", "reconciliacao_duckdb.json"), ("04_criar_mart_olap", "testes_mart.json")]:
        p = SAIDA / arq
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            etapas[nome] = d.get("segundos_total", d.get("segundos", {}).get("total"))

    rel = {
        "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "script": "src/06_comparar_sqlite_duckdb.py",
        "maquina": maquina(),
        "consulta": {m: " ".join(s.split()) for m, s in SQL.items()},
        "protocolo": {
            "execucoes": EXECUCOES,
            "fria": "processo Python novo por execução; mede só execute+fetchall, depois de abrir a conexão",
            "aquecida": "mesma conexão; uma execução descartada e cinco medidas",
            "cache_do_so": "não esvaziado; 'fria' significa processo e conexão novos, não disco frio",
            "relogio": "time.perf_counter, em milissegundos",
        },
        "resultados": resultados,
        "mesmo_resultado_linha_a_linha": mesmo_resultado,
        "totais_por_motor": totais,
        "segundos_por_etapa_do_pipeline": etapas,
        "ressalva": "Os tempos descrevem esta consulta, nesta máquina, nesta execução; não provam superioridade "
                    "geral de um mecanismo sobre o outro.",
    }
    DESTINO.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"gravado {DESTINO.relative_to(BASE)} | mesmo resultado nos dois bancos: {mesmo_resultado}")
    if not mesmo_resultado:
        print("FALHA: os dois bancos devolveram resultados diferentes")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
