import requests
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime

# Configuración Data912 consolidada
BASE_URL = "https://data912.com"

# Definición de clústeres para tus 93M
PARES = [
    {'name': 'BANCOS', 'a': 'GGAL', 'b': 'BMA', 'tipo': 'stocks'},
    {'name': 'ENERGIA', 'a': 'PAMP', 'b': 'YPFD', 'tipo': 'stocks'},
    {'name': 'GAS', 'a': 'TGSU2', 'b': 'TGNO4', 'tipo': 'stocks'},
    {'name': 'BONOS', 'a': 'AL30', 'b': 'GD30', 'tipo': 'bonds'}
]


def fetch_live_panel(tipo):
    """Descarga el panel completo como hace tu screener."""
    endpoint = f"/live/arg_{tipo}"
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        df = pd.DataFrame(r.json())
        # Mapeo de columnas según screener_data912.py
        df = df.rename(columns={'symbol': 'ticker', 'c': 'last', 'price': 'last'})
        return df.set_index('ticker')['last']
    except Exception as e:
        print(f"❌ Error en panel {tipo}: {e}")
        return pd.Series()


def get_stats(ticker_a, ticker_b, tipo):
    """Calcula Mediana y Sigma histórico."""
    try:
        def get_prices(t):
            url = f"{BASE_URL}/historical/{tipo}/{t}"
            data = requests.get(url, timeout=10).json()
            return pd.DataFrame(data)['c'].tail(20)  # 'c' es la llave de cierre

        ratio_hist = get_prices(ticker_a).values / get_prices(ticker_b).values
        return {'mediana': np.median(ratio_hist), 'sigma': np.std(ratio_hist)}
    except Exception:
        return None


# Cache de estadísticas para no saturar requests históricos
stats_cache = {}


def scan_arbitrage():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"--- 📡 SCANNER DATA912 CORREGIDO ({datetime.now().strftime('%H:%M:%S')}) ---")

    # Descarga masiva de paneles (Optimizado para Ryzen 9)
    panels = {
        'stocks': fetch_live_panel('stocks'),
        'bonds': fetch_live_panel('bonds')
    }

    results = []
    for p in PARES:
        t_a, t_b = p['a'], p['b']

        # 1. Stats base
        if t_a not in stats_cache:
            print(f"📊 Calculando Z-Score base para {p['name']}...")
            stats_cache[t_a] = get_stats(t_a, t_b, p['tipo'])
            time.sleep(1)

        if not stats_cache[t_a]: continue

        # 2. Precios Live
        source = panels[p['tipo']]
        if t_a in source.index and t_b in source.index:
            ratio = source.loc[t_a] / source.loc[t_b]
            z = (ratio - stats_cache[t_a]['mediana']) / stats_cache[t_a]['sigma']

            # Lógica M1/M2 de tu planilla de arbitraje
            accion = "NEUTRAL"
            if z > 1.0:
                accion = f"🔴 M1: VENTA {t_a} / COMPRA {t_b}"
            elif z < -1.0:
                accion = f"🟢 M2: COMPRA {t_a} / VENTA {t_b}"

            results.append({
                'Par': f"{t_a}/{t_b}", 'Ratio': round(ratio, 4),
                'Z-Score': round(z, 2), 'Accion': accion
            })

    if results:
        print("\n" + pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    while True:
        scan_arbitrage()
        time.sleep(30)