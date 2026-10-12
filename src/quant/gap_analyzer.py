import yfinance as yf
import pandas as pd

# Descargar datos de ejemplo (puedes cambiar el ticker)
ticker = 'GGAL'
data = yf.download(ticker, start='2014-01-01', end='2025-12-26')

# Calcular el gap positivo: cuando el mínimo del día actual es mayor que el máximo del día anterior
data['Gap positivo'] = data['Low'] > data['High'].shift(1)

# Calcular el gap negativo: cuando el máximo del día actual es menor que el mínimo del día anterior
data['Gap negativo'] = data['High'] < data['Low'].shift(1)

# Filtrar gaps positivos y negativos
gaps_positivos = data[data['Gap positivo']]
gaps_negativos = data[data['Gap negativo']]

# Mostrar la cantidad de gaps positivos y negativos
cantidad_gaps_positivos = len(gaps_positivos)
cantidad_gaps_negativos = len(gaps_negativos)

print( "Gaps")
print(f"Cantidad de gaps positivos: {cantidad_gaps_positivos}")
print(f"Cantidad de gaps negativos: {cantidad_gaps_negativos}")


# Mostrar los primeros gaps positivos y negativos
print("Gaps positivos:")
print(gaps_positivos[['High', 'Low']].head())

print("\nGaps negativos:")
print(gaps_negativos[['High', 'Low']].head())

## aca te dejo como funciona shift()

import pandas as pd

# Crear un DataFrame de ejemplo
df = pd.DataFrame({'A': [1, 2, 3, 4, 5]})

# Desplazar los valores de la columna 'A' hacia abajo (periods=1)
df['Shifted_A'] = df['A'].shift(1)
print(df)

import matplotlib.pyplot as plt

# Gráfico de los precios de cierre
plt.figure(figsize=(12, 6))
plt.plot(data['Close'], label='Precio de cierre')
plt.title(f'Precio de cierre de {ticker}')
plt.xlabel('Fecha')
plt.ylabel('Precio')
plt.legend()
plt.grid(True)
plt.show()

# Gráfico de los gaps positivos y negativos
plt.figure(figsize=(12, 6))
plt.plot(data['Close'], label='Precio de cierre')
plt.scatter(gaps_positivos.index, gaps_positivos['Low'], color='green', label='Gap positivo')
plt.scatter(gaps_negativos.index, gaps_negativos['High'], color='red', label='Gap negativo')
plt.title(f'Gaps positivos y negativos de {ticker}')
plt.xlabel('Fecha')
plt.ylabel('Precio')
plt.legend()
plt.grid(True)
plt.show()
