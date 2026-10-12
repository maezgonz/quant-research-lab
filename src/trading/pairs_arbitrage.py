import pandas as pd
import numpy as np
import vectorbt as vbt
import yfinance as yf
import matplotlib.pyplot as plt

# =====================================================================
# 1. SETUP DE ACTIVOS (Ejemplo Bancos locales para tus 93M)
# =====================================================================
tickers = ['GGAL.BA', 'BMA.BA'] #
data = yf.download(tickers, start="2024-01-01")['Close']

# =====================================================================
# 2. CÁLCULO DE RATIO Y BANDAS ESTADÍSTICAS
# =====================================================================
ratio = data['GGAL.BA'] / data['BMA.BA']

# Definimos la ventana móvil (ej. 20 días para capturar el corto plazo)
window = 20

# Cálculo de Mediana y Desviación Estándar (1 Sigma)
rolling_median = ratio.rolling(window=window).median()
rolling_std = ratio.rolling(window=window).std()

upper_band = rolling_median + rolling_std # +1 Sigma
lower_band = rolling_median - rolling_std # -1 Sigma

# =====================================================================
# 3. LÓGICA DE TOMA DE DECISIÓN
# =====================================================================
# SEÑAL VENTA RATIO (M1): Ratio cruza hacia arriba la banda superior
# Vendemos GGAL / Compramos BMA esperando convergencia
entries = ratio > upper_band

# SEÑAL COMPRA RATIO (M2): Ratio cruza hacia abajo la banda inferior
# Compramos GGAL / Vendemos BMA
exits = ratio < lower_band

# =====================================================================
# 4. VISUALIZACIÓN ANALÍTICA (Ryzen 9 Optimized)
# =====================================================================
plt.figure(figsize=(14, 8))
plt.plot(ratio, label='Ratio GGAL/BMA', color='black', lw=1.5)
plt.plot(rolling_median, label='Mediana Móvil', color='blue', linestyle='--', alpha=0.6)
plt.plot(upper_band, label='+1 Sigma (Venta Ratio)', color='red', alpha=0.4)
plt.plot(lower_band, label='-1 Sigma (Compra Ratio)', color='green', alpha=0.4)

# Sombreado de la zona de equilibrio
plt.fill_between(ratio.index, lower_band, upper_band, color='gray', alpha=0.1)

plt.title(f"Arbitraje de Ratio: {tickers[0]} vs {tickers[1]} (Z-Score 1$\sigma$)", fontsize=14)
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)
plt.show()

# =====================================================================
# 5. BACKTEST RÁPIDO (VECTORBT)
# =====================================================================
pf = vbt.Portfolio.from_signals(ratio, entries, exits, fees=0.002, init_cash=5000000)
print("\n" + "="*40)
print("📈 PERFORMANCE DEL ARBITRAJE")
print("="*40)
print(f"Sharpe Ratio: {pf.sharpe_ratio():.2f}") # Comparar con tu 1.91 anterior
print(f"Retorno Acumulado: {pf.total_return()*100:.2f}%")