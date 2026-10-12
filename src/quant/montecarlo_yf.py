import random
import json
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

# Configuración de estilo de gráfico
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(13, 11))

# Parámetros de simulación
activo = "AAPL"  # Cambia esto al ticker que desees analizar
data = yf.download(activo, start="2020-01-01", end="2023-01-01")  # Ajusta las fechas según sea necesario

# Verifica si 'Adj Close' está en las columnas, si no, usa 'Close'
if 'Adj Close' in data.columns:
    data['pct_change'] = data['Adj Close'].pct_change()  # Calcula el cambio porcentual
else:
    print("La columna 'Adj Close' no está disponible, usando 'Close' en su lugar.")
    data['pct_change'] = data['Close'].pct_change()  # Calcula el cambio porcentual

# Calcula la media y la volatilidad diaria
mu = data['pct_change'].mean() * 252  # Media anualizada
sigma = data['pct_change'].std() * (252 ** 0.5)  # Volatilidad anualizada

ruedas = 250
simulaciones = 1000
perdida_max = 0.3  # % de pérdida máxima tolerada
capital = [[100] for i in range(simulaciones)]

quiebres = {'parcial': 0, 'final': 0}
for j in range(simulaciones):
    for i in range(ruedas):
        v = random.normalvariate(mu, sigma)
        capital[j].append(capital[j][i] * (1 + v / 100))
    ax.plot(capital[j], lw=1, alpha=0.05, color='white')

    if min(capital[j]) < (1 - perdida_max) * 100:
        quiebres['parcial'] += 1

    if capital[j][i] < (1 - perdida_max) * 100:
        quiebres['final'] += 1

ax.plot([(1 - perdida_max) * 100] * ruedas, 'r--')
ax.set_yscale('log')
fig.suptitle(f'Montecarlo básico cartera mu diario={mu:.4f}, sigma diario={sigma:.4f}',
             y=0.17, fontsize=18, color='silver')
plt.show()

df = pd.DataFrame(capital).round(2)

resumen = {}
resumen['minTemporal'] = df.min().min()
resumen['maxTemporal'] = df.max().max()
resumen['minFinal'] = df.transpose().iloc[-1:].squeeze().min()
resumen['maxFinal'] = df.transpose().iloc[-1:].squeeze().max()
resumen['medio'] = round(df.transpose().iloc[-1:].squeeze().mean(), 2)
resumen['errorAbsMedia'] = round(resumen['medio'] * 1 / (simulaciones ** 0.5), 2)
resumen['quiebres'] = quiebres
print(json.dumps(resumen, indent=5))