import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from skfolio import Portfolio
from skfolio.datasets import load_sp500_dataset
from skfolio.metrics import sharpe_ratio, volatility, mean_return
from skfolio.preprocessing import prices_to_returns

# 1. Definimos las acciones y sus pesos aproximados (de la imagen)
tickers = [
    "AAPL", "AXP", "KO", "BAC", "CVX", "OXY", "MCO", "KHC", "CB", "DVA",
    "KR", "VRSN", "V", "SIRI", "STZ", "MA", "AMZN", "AON", "COF", "DPZ",
    "ALLY", "TMUS", "LLYVK", "CHTR"
]

weights = [
    25.76, 15.77, 11.07, 10.19, 7.67, 5.06, 4.44, 3.83, 3.16, 2.08,
    1.31, 1.30, 1.12, 1.04, 0.85, 0.84, 0.79, 0.63, 0.50, 0.47,
    0.41, 0.40, 0.36, 0.28
]

# Normalizamos los pesos (por si no suman 100)
weights = np.array(weights) / np.sum(weights)

# 2. Descarga de precios históricos (últimos 2 años)
start_date = "2023-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")
data = yf.download(tickers, start=start_date, end=end_date)['Adj Close']

# 3. Calculamos retornos logarítmicos diarios
returns = np.log(data / data.shift(1)).dropna()

# 4. Retorno esperado del portafolio
mean_returns = returns.mean()
expected_return = np.dot(mean_returns, weights)

# 5. Volatilidad del portafolio
cov_matrix = returns.cov()
portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

# 6. Sharpe Ratio (sin tasa libre de riesgo)
sharpe = expected_return / portfolio_volatility

# 7. Resultados
print(f"Retorno esperado anual: {expected_return*252:.2%}")
print(f"Volatilidad anual: {portfolio_volatility*np.sqrt(252):.2%}")
print(f"Sharpe Ratio: {sharpe*np.sqrt(252):.2f}")

# 8. Visualización de la distribución del portafolio
plt.figure(figsize=(10, 7))
plt.pie(weights, labels=tickers, autopct='%1.1f%%', startangle=140)
plt.axis('equal')
plt.title('Distribución del Portafolio de Warren Buffett (Q1 2025)')
plt.show()
