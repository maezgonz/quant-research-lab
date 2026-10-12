import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

def get_data():
    """Descarga datos históricos para S&P 500 y Oro."""
    start_date = "2005-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    sp500 = yf.Ticker("^GSPC").history(start=start_date, end=end_date)['Close']
    gold = yf.Ticker("GC=F").history(start=start_date, end=end_date)['Close']
    data = pd.DataFrame({'SP500': sp500, 'Gold': gold})
    data.index = data.index.tz_localize(None)
    return data.ffill().dropna()

def calculate_strategy_returns(data, ma_period, commission_rate):
    """Calcula los retornos de la estrategia aplicando comisiones en cada operación."""
    ratio = data['SP500'] / data['Gold']
    ma = ratio.rolling(window=ma_period).mean()

    # Generar señal y determinar operaciones
    signal = pd.Series(np.where(ratio > ma, 1, 0), index=data.index)
    trades = signal.diff().abs().fillna(0)

    # Calcular retornos base
    shifted_signal = signal.shift(1)
    sp500_return = data['SP500'].pct_change()
    gold_return = data['Gold'].pct_change()
    strategy_return = pd.Series(np.where(shifted_signal == 1, sp500_return, gold_return), index=data.index)

    # Aplicar comisiones
    commission_cost = trades * commission_rate
    final_returns = strategy_return - commission_cost

    return final_returns, trades.sum()

def calculate_metrics(returns):
    """Calcula las métricas de rendimiento clave."""
    returns = returns.dropna()
    if returns.empty: return pd.Series(0, index=['Retorno Total', 'Retorno Anualizado', 'Volatilidad Anualizada', 'Ratio de Sharpe', 'Máximo Drawdown'])

    total_return = (1 + returns).cumprod().iloc[-1] - 1
    annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
    annualized_volatility = returns.std() * np.sqrt(252)
    sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility != 0 else 0

    wealth_index = (1 + returns).cumprod()
    max_drawdown = (wealth_index / wealth_index.cummax() - 1).min()

    return pd.Series({
        'Retorno Total': total_return, 'Retorno Anualizado': annualized_return,
        'Volatilidad Anualizada': annualized_volatility, 'Ratio de Sharpe': sharpe_ratio,
        'Máximo Drawdown': max_drawdown
    })

# --- Ejecución Principal ---
# 1. Parámetros de la estrategia
ma_period = 140
commission_rate = 0.0005  # 0.05%

# 2. Obtener datos y calcular retornos
data = get_data()
data['Strategy_Return'], total_trades = calculate_strategy_returns(data, ma_period, commission_rate)
data['SP500_Return'] = data['SP500'].pct_change()
data['Gold_Return'] = data['Gold'].pct_change()

# 3. Calcular retornos acumulados
for col in ['Strategy', 'SP500', 'Gold']:
    data[f'{col}_Cum_Return'] = (1 + data[f'{col}_Return']).cumprod()

# 4. Generar y mostrar métricas de rendimiento
metrics = pd.DataFrame({
    'Estrategia': calculate_metrics(data['Strategy_Return']),
    'S&P 500': calculate_metrics(data['SP500_Return']),
    'Oro': calculate_metrics(data['Gold_Return'])
}).T

print(f"Estrategia Fija: SMA con período {ma_period} y comisión de {commission_rate:.2%}")
print("\nMétricas de Rendimiento:")
print(metrics.to_string(formatters={
    'Retorno Total': '{:,.2%}'.format, 'Retorno Anualizado': '{:,.2%}'.format,
    'Volatilidad Anualizada': '{:,.2%}'.format, 'Ratio de Sharpe': '{:,.2f}'.format,
    'Máximo Drawdown': '{:,.2%}'.format
}))

# 5. Información final
total_commission_paid = total_trades * commission_rate
print(f"\nComisiones totales pagadas ({total_trades:.0f} operaciones): {total_commission_paid:.2%}")

# Posición actual
current_ratio = data['SP500'].iloc[-1] / data['Gold'].iloc[-1]
current_ma = data['SP500'].iloc[-ma_period:].mean() / data['Gold'].iloc[-ma_period:].mean()
current_position = "Largo en S&P 500" if current_ratio > current_ma else "Largo en Oro"
print(f"Posición actual: {current_position}")

# 6. Gráfico de rendimiento
fig, ax = plt.subplots(figsize=(15, 8))
ax.plot(data.index, data['SP500_Cum_Return'], label='S&P 500', color='blue', alpha=0.7)
ax.plot(data.index, data['Gold_Cum_Return'], label='Oro', color='gold', alpha=0.7)
ax.plot(data.index, data['Strategy_Cum_Return'], label=f'Estrategia (SMA {ma_period})', color='green', linewidth=2)
ax.set_title('Comparación de Rendimiento: Estrategia vs. Benchmarks', fontsize=16)
ax.set_ylabel('Retorno Acumulado (Escala Logarítmica)')
ax.set_xlabel('Fecha')
ax.set_yscale('log')
ax.legend()
ax.grid(True, which="both", ls="--", linewidth=0.5)
plt.tight_layout()
plt.show()