import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ta

# Definir el símbolo del activo (por ejemplo, 'AAPL' para Apple)
symbol = 'GGAL.BA'

# Obtener datos históricos de Yahoo Finance
data = yf.download(symbol, period='1y', interval='1d', auto_adjust=True)

# Verifica las columnas disponibles en el DataFrame
print("Columnas disponibles:", data.columns)

# Verifica si 'Adj Close' está en las columnas
if 'Adj Close' not in data.columns:
    print(f"La columna 'Adj Close' no está disponible en los datos descargados para {symbol}.")
    # Manejo adicional si es necesario
    if 'Close' in data.columns:
        data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
    else:
        print("No se encontró ninguna columna de precios para calcular el RSI.")

# Cálculo de indicadores técnicos
if 'Adj Close' in data.columns:
    data['RSI'] = ta.momentum.RSIIndicator(data['Adj Close'], window=14).rsi()
else:
    print(f"La columna 'Adj Close' no está disponible en los datos descargados para {symbol}.")
data['MACD'] = ta.trend.MACD(data['Adj Close']).macd()
data['MACD_signal'] = ta.trend.MACD(data['Adj Close']).macd_signal()
data['EMA_50'] = ta.trend.EMAIndicator(data['Adj Close'], window=50).ema_indicator()
data['EMA_200'] = ta.trend.EMAIndicator(data['Adj Close'], window=200).ema_indicator()
data['Upper_BB'], data['Lower_BB'] = ta.volatility.BollingerBands(data['Adj Close']).bollinger_hband(), ta.volatility.BollingerBands(data['Adj Close']).bollinger_lband()

# Simulación de Monte Carlo con volatilidad histórica
def monte_carlo_simulation(data, n_simulations=1000, n_days=252):
    daily_returns = data['Daily_Return'].dropna()
    volatility = daily_returns.std()
    simulations = np.zeros((n_simulations, n_days))
    
    for i in range(n_simulations):
        drift = daily_returns.mean()
        shock = np.random.normal(loc=drift, scale=volatility, size=n_days)
        simulations[i, :] = np.cumprod(1 + shock)  # Simulación de la evolución de precios

    return simulations

# Estrategias de Inversión con Ajustes
def strategy_evaluation(data):
    strategies = []
    
    for i in range(10):
        threshold_rsi = np.random.randint(30, 70)  # Condiciones aleatorias de RSI
        threshold_macd = np.random.choice([-1, 1])  # Señales de compra o venta de MACD
        
        data['Signal'] = 0
        data['Signal'] = np.where(data['RSI'] > threshold_rsi, 1, data['Signal'])
        data['Signal'] = np.where(data['RSI'] < (100 - threshold_rsi), -1, data['Signal'])
        data['Signal'] = np.where(data['MACD'] > data['MACD_signal'], 1, data['Signal'])
        data['Signal'] = np.where(data['MACD'] < data['MACD_signal'], -1, data['Signal'])

        data['Strategy_Return'] = data['Signal'].shift(1) * data['Daily_Return']
        
        simulations = monte_carlo_simulation(data)
        strategy_success_rate = (simulations[:, -1] > 1).mean()  # Probabilidad de éxito
        strategies.append({
            'Strategy': f'Estrategia {i+1}',
            'RSI Threshold': threshold_rsi,
            'MACD Signal': threshold_macd,
            'Success Rate': strategy_success_rate
        })
    
    return pd.DataFrame(strategies)

# Cálculo de los retornos diarios
data['Daily_Return'] = data['Adj Close'].pct_change()

# Evaluación de las estrategias
strategies_df = strategy_evaluation(data)

# Mostrar las mejores estrategias
best_strategies = strategies_df.sort_values(by='Success Rate', ascending=False)
print(f"\nMejores estrategias basadas en la probabilidad de éxito:")
print(best_strategies)

# Graficar los resultados de Monte Carlo
simulations = monte_carlo_simulation(data)
plt.figure(figsize=(10,6))
plt.plot(simulations.T, color='blue', alpha=0.1)
plt.title(f"Simulación de Monte Carlo para {symbol} (1000 simulaciones)")
plt.xlabel('Días')
plt.ylabel('Valor acumulado')
plt.show()

# Muestra los primeros registros del DataFrame
print(data.head())
