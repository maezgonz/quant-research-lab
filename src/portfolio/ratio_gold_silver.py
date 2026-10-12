import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def analyze_gold_silver_ratio():
    print("⚗️  Analizando correlación de metales preciosos...")

    # Descargamos Futuros de Oro (GC=F) y Plata (SI=F)
    # Usamos futuros porque son los que marcan el precio spot global
    tickers = ['GC=F', 'SI=F']
    data = yf.download(tickers, period="10y", interval="1d", progress=False, auto_adjust=False)

    # Manejo de MultiIndex
    if isinstance(data.columns, pd.MultiIndex):
        closes = data['Close']
    else:
        closes = data

    # Limpieza
    closes = closes.dropna()

    # CÁLCULO DEL RATIO
    # Cuántas onzas de plata comprás con 1 onza de oro
    ratio = closes['GC=F'] / closes['SI=F']

    # Estadísticas Clave
    current_ratio = ratio.iloc[-1]
    mean_ratio = ratio.mean()
    std_ratio = ratio.std()

    # Percentiles para definir zonas extremas
    p90 = ratio.quantile(0.90)  # Zona: Plata muy barata (Oportunidad PAAS)
    p10 = ratio.quantile(0.10)  # Zona: Plata cara (Pasarse a Oro)

    print(f"\n💎 REPORTE DE RATIO (Oro/Plata) 💎")
    print(f"===================================")
    print(f"Ratio Actual:      {current_ratio:.2f}x")
    print(f"Promedio 10 años:   {mean_ratio:.2f}x")
    print(f"-----------------------------------")
    print(f"Zona de Oportunidad Plata (> {p90:.1f}): {'✅ SÍ' if current_ratio > p90 else '❌ NO'}")

    # Interpretación para tu Trade
    gap_percent = ((current_ratio - mean_ratio) / mean_ratio) * 100
    print(f"Desvío de la media: {gap_percent:.1f}%")

    if current_ratio > 80:
        print("💡 SEÑAL: PLATA BARATA. El Oro subió mucho, la Plata debe correr (Buy PAAS).")
    elif current_ratio < 65:
        print("💡 SEÑAL: NEUTRO/ORO. El ratio está comprimido.")

    # GRÁFICO
    plt.figure(figsize=(12, 6))

    # Plot Ratio
    plt.plot(ratio.index, ratio, label='Ratio Oro/Plata', color='#d4af37', linewidth=1.5)

    # Referencias
    plt.axhline(mean_ratio, color='black', linestyle='--', label=f'Media ({mean_ratio:.1f})')
    plt.axhline(p90, color='green', linestyle=':', label=f'Zona Compra Plata ({p90:.1f})')
    plt.axhline(p10, color='red', linestyle=':', label=f'Zona Compra Oro ({p10:.1f})')

    # Rellenos
    plt.fill_between(ratio.index, ratio, p90, where=(ratio > p90), color='green', alpha=0.1,
                     label='Plata Infravalorada')

    plt.title(f"Gold/Silver Ratio: \nActual: {current_ratio:.2f}", fontsize=14)
    plt.ylabel("Onzas de Plata por 1 Onza de Oro")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()


# Ejecutar
analyze_gold_silver_ratio()