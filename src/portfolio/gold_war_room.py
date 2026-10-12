import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sympy.printing.pretty.pretty_symbology import line_width

# Configuración de Estilo "Dark Trader"
plt.style.use('default')


def analyze_gold_assets():
    print("⚔️  INICIANDO GOLD WAR ROOM: HMY vs GOLD vs GLD...")

    # 1. Definición de Activos
    # GC=F: Futuro Oro (Referencia)
    # GLD: ETF Spot
    # GOLD: Barrick (Minera Blue Chip)
    # HMY: Harmony (Minera High Beta/Riesgo)
    tickers = ['GC=F', 'GLD', 'GOLD', 'HMY']

    # Descarga de datos (1 Año para ver la tendencia actual)
    data = yf.download(tickers, period="20y", interval="1d", progress=False, auto_adjust=False)

    # Limpieza de MultiIndex (Corrección para versiones nuevas de yfinance)
    if isinstance(data.columns, pd.MultiIndex):
        closes = data['Close']
    else:
        closes = data[tickers]  # Fallback

    closes = closes.ffill().dropna()

    # ==========================================
    # 2. CÁLCULOS TÁCTICOS (La "Inteligencia")
    # ==========================================

    # A. Rendimiento Normalizado (Base 100)
    # Para comparar peras con manzanas visualmente
    norm_prices = (closes / closes.iloc[0]) * 100

    # B. Ratio de Riesgo (HMY / GOLD)
    # Si sube, el mercado prefiere riesgo (HMY). Si baja, prefiere seguridad (GOLD).
    risk_ratio = closes['HMY'] / closes['GOLD']
    mean_risk_ratio = risk_ratio.mean()

    # C. Beta Rolling (30 días) vs GLD
    # Cuánto se mueve la minera por cada 1% que se mueve el Oro
    returns = closes.pct_change().dropna()
    rolling_beta_hmy = returns['HMY'].rolling(30).cov(returns['GLD']) / returns['GLD'].rolling(30).var()
    rolling_beta_gold = returns['GOLD'].rolling(30).cov(returns['GLD']) / returns['GLD'].rolling(30).var()

    # D. RSI (14 días) para Timing
    def calculate_rsi(series, window=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    rsi_hmy = calculate_rsi(closes['HMY']).iloc[-1]
    rsi_gold = calculate_rsi(closes['GOLD']).iloc[-1]
    rsi_spot = calculate_rsi(closes['GC=F']).iloc[-1]

    # ==========================================
    # 3. VISUALIZACIÓN (DASHBOARD)
    # ==========================================

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(f"GOLD ASSETS DASHBOARD\nEstrategia: HMY (Agresivo) + GOLD (Base)", fontsize=16, color='black')

    # --- PANEL 1: La Carrera (Retorno %) ---
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(norm_prices.index, norm_prices['HMY'], label='HMY (Harmony)', color='blue', linewidth=1.5)
    ax1.plot(norm_prices.index, norm_prices['GOLD'], label='GOLD (Barrick)', color='gold', linewidth=1.5)
    ax1.plot(norm_prices.index, norm_prices['GLD'], label='GLD (Spot Proxy)', color='black', linewidth=2, linestyle='--')
    ax1.set_title("1. Rendimiento Relativo (Base 100)", fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.2)

    # --- PANEL 2: Beta Dinámico (Apalancamiento) ---
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(rolling_beta_hmy.index, rolling_beta_hmy, label='Beta HMY', color='blue')
    ax2.plot(rolling_beta_gold.index, rolling_beta_gold, label='Beta GOLD', color='gold')
    ax2.axhline(1, color='white', linestyle=':', label='Oro (1x)')
    ax2.axhline(rolling_beta_hmy.iloc[-1], color='black', linestyle='--', alpha=0.5,
                label=f"HMY Actual: {rolling_beta_hmy.iloc[-1]:.1f}x")
    ax2.set_title("2. Factor de Apalancamiento vs Oro (Beta)", fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.2)

    # --- PANEL 3: Ratio HMY/GOLD (¿Está barata la riesgosa?) ---
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(risk_ratio.index, risk_ratio, color='black', linewidth=1.0 , label='Ratio HMY / GOLD')
    ax3.axhline(mean_risk_ratio, color='orange', linestyle='--', label='Media')

    # Zonas de decisión
    std_rr = risk_ratio.std()
    ax3.axhline(mean_risk_ratio - std_rr, color='green', linestyle=':', label='HMY Barata (Buy)')
    ax3.axhline(mean_risk_ratio + std_rr, color='red', linestyle=':', label='HMY Cara (Switch to GOLD)')
    ax3.fill_between(risk_ratio.index, risk_ratio, mean_risk_ratio - std_rr,
                     where=(risk_ratio < mean_risk_ratio - std_rr), color='green', alpha=0.3)
    ax3.fill_between(risk_ratio.index, risk_ratio, mean_risk_ratio + std_rr,
                     where=(risk_ratio > mean_risk_ratio + std_rr), color='red', alpha=0.3)


    ax3.set_title("3. Valuación Relativa: ¿HMY o GOLD?", fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.2)

    # --- PANEL 4: Semáforo RSI (Timing) ---
    ax4 = plt.subplot(2, 2, 4)
    assets = ['HMY', 'GOLD', 'Oro Futuro']
    rsis = [rsi_hmy, rsi_gold, rsi_spot]
    colors = ['blue', 'gold', 'black']

    bars = ax4.bar(assets, rsis, color=colors, alpha=0.7)
    ax4.axhline(70, color='red', linestyle='--', label='Sobrecompra (Venta)')
    ax4.axhline(30, color='green', linestyle='--', label='Sobreventa (Compra)')
    ax4.set_ylim(0, 100)
    ax4.set_title(f"4. RSI Actual (Timing Entrada)", fontsize=12)

    # Etiquetas en las barras
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{height:.1f}', ha='center', va='bottom', color='white', fontweight='bold')

    plt.tight_layout()
    plt.show()

    # Interpretación Textual
    print(f"\n📊 ANÁLISIS TÁCTICO PARA MATÍAS:")
    print(f"---------------------------------")
    print(f"1. Beta de HMY hoy: {rolling_beta_hmy.iloc[-1]:.2f}x")
    print(f"   (Significa: Si el oro sube 1%, HMY sube {rolling_beta_hmy.iloc[-1]:.2f}%)")
    print(f"2. RSI HMY: {rsi_hmy:.1f}")

    if rsi_hmy > 70:
        print("⚠️ ALERTA: HMY está en Sobrecompra. Esperar retroceso o entrar con 50% de la posición.")
    elif rsi_hmy < 30:
        print("✅ OPORTUNIDAD: HMY en piso técnico. Gatillar compra agresiva.")
    else:
        print("➡️ ESTADO: Zona Neutra/Tendencia. Operable con Stop Loss.")


# Ejecutar
analyze_gold_assets()