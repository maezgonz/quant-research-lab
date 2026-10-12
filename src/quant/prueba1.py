import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ta

# Definir el símbolo del activo (por ejemplo, 'AAPL' para Apple)
symbol = 'AAPL'

# Obtener datos históricos de Yahoo Finance
data = yf.download(symbol, period='1y', interval='1d')

# Cálculo de indicadores técnicos
data['RSI'] = ta.momentum.RSIIndicator(data['Adj Close'], window=14).rsi()
data['MACD'] = ta.trend.MACD(data['Adj Close']).macd()
data['MACD_signal'] = ta.trend.MACD(data['Adj Close']).macd_signal()

# Cálculo de la probabilidad de éxito (P_win)
data['Daily_Return'] = data['Adj Close'].pct_change()
P_win = (data['Daily_Return'] > 0).mean()  # Probabilidad de tener rendimiento positivo

# Cálculo de la esperanza matemática (E)
R_win = data['Daily_Return'].mean()  # Rendimiento promedio
P_loss = 1 - P_win  # Probabilidad de rendimiento negativo
R_loss = data['Daily_Return'].min()  # Rendimiento más bajo en el período analizado
E = P_win * R_win + P_loss * R_loss  # Esperanza matemática

# Función para simulación de Monte Carlo
def monte_carlo_simulation(data, n_simulations=1000, n_days=252):
    simulations = np.zeros((n_simulations, n_days))
    for i in range(n_simulations):
        daily_returns = np.random.choice(data['Daily_Return'].dropna(), size=n_days, replace=True)
        simulations[i, :] = np.cumprod(1 + daily_returns)  # Simulación de la evolución de precios
    return simulations

# Realizar la simulación de Monte Carlo
simulations = monte_carlo_simulation(data)

# Graficar los resultados de Monte Carlo
plt.figure(figsize=(10,6))
plt.plot(simulations.T, color='blue', alpha=0.1)
plt.title(f"Simulación de Monte Carlo para {symbol} (1000 simulaciones)")
plt.xlabel('Días')
plt.ylabel('Valor acumulado')
plt.show()

# Evaluación de 10 Estrategias con Monte Carlo
strategies = []

for i in range(10):
    # Cada estrategia utilizará un conjunto de condiciones en RSI y MACD
    threshold_rsi = np.random.randint(30, 70)  # Condiciones aleatorias de RSI
    threshold_macd = np.random.choice([-1, 1])  # Señales de compra o venta de MACD
    data['Signal'] = 0

    # Estrategia de RSI
    data['Signal'] = np.where(data['RSI'] > threshold_rsi, 1, data['Signal'])
    data['Signal'] = np.where(data['RSI'] < (100 - threshold_rsi), -1, data['Signal'])

    # Estrategia de MACD
    data['Signal'] = np.where(data['MACD'] > data['MACD_signal'], 1, data['Signal'])
    data['Signal'] = np.where(data['MACD'] < data['MACD_signal'], -1, data['Signal'])

    # Simulación con la señal obtenida (Compra=1, Venta=-1, No hacer nada=0)
    data['Strategy_Return'] = data['Signal'].shift(1) * data['Daily_Return']
    strategy_result = monte_carlo_simulation(data)

    # Evaluar la probabilidad de éxito de la estrategia
    strategy_success_rate = (strategy_result[:,-1] > 1).mean()  # Proporción de simulaciones exitosas (superan 1)
    strategies.append({
        'Strategy': f'Estrategia {i+1}',
        'RSI Threshold': threshold_rsi,
        'MACD Signal': threshold_macd,
        'Success Rate': strategy_success_rate
    })

# Crear un DataFrame con los resultados de las estrategias
strategies_df = pd.DataFrame(strategies)

# Mostrar las estrategias con sus tasas de éxito
print(strategies_df)

# Mostrar las mejores estrategias (porcentaje de éxito)
best_strategies = strategies_df.sort_values(by='Success Rate', ascending=False)
print(f"\nMejores estrategias basadas en la probabilidad de éxito:")
print(best_strategies)
