import random
import json
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

def monte_carlo_simulation(activo, ruedas=1000, simulaciones=1000, perdida_max=0.3):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(13, 11))

    # Descarga de datos
    data = yf.download(activo, start="2002-01-01", end="2025-04-28")
    if 'Adj Close' in data.columns:
        data['pct_change'] = data['Adj Close'].pct_change()
    else:
        data['pct_change'] = data['Close'].pct_change()

    # Cálculo de media y volatilidad
    mu = data['pct_change'].mean() * 252
    sigma = data['pct_change'].std() * (252 ** 0.5)

    capital = [[100] for _ in range(simulaciones)]
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

    # Resumen de resultados
    df = pd.DataFrame(capital).round(2)
    resumen = {
        'minTemporal': df.min().min(),
        'maxTemporal': df.max().max(),
        'minFinal': df.transpose().iloc[-1:].squeeze().min(),
        'maxFinal': df.transpose().iloc[-1:].squeeze().max(),
        'medio': round(df.transpose().iloc[-1:].squeeze().mean(), 2),
        'errorAbsMedia': round(df.transpose().iloc[-1:].squeeze().std() / (simulaciones ** 0.5), 2),
        'quiebres': quiebres
    }
    print(json.dumps(resumen, indent=5))

# Llamada a la función
monte_carlo_simulation("GGALD.BA", ruedas=1000, simulaciones=1000, perdida_max=0.3)