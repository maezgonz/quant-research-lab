import pandas as pd
import datetime as dt
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Dict, Optional

# Configuración de estilo para gráficos
plt.style.use('dark_background')

def descargar_datos(tickers: List[str], años: int) -> pd.DataFrame:
    """
    Descarga datos históricos de precios para los tickers especificados.
    
    Args:
        tickers: Lista de símbolos de cotización
        años: Número de años para los que descargar datos
        
    Returns:
        DataFrame con los precios de cierre
    """
    start = dt.date.today() - dt.timedelta(365 * años)
    end = dt.date.today()
    
    try:
        data = yf.download(tickers, start=start, end=end, interval="1wk")['Close']
        data = data.dropna(how='all')
        return data
    except Exception as e:
        print(f"Error al descargar datos: {e}")
        raise

def calcular_rendimientos(data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcula los rendimientos semanales y los rendimientos pasados (con shift).
    
    Args:
        data: DataFrame con precios de cierre
        
    Returns:
        Tuple con (rendimientos, rendimientos_pasados)
    """
    yields = data.pct_change()
    yields = yields.fillna(0)
    yields_past = yields.shift()
    return yields, yields_past

def seleccionar_carteras(yields: pd.DataFrame, yields_past: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Selecciona carteras basadas en los mejores y peores rendimientos de la semana anterior.
    
    Args:
        yields: DataFrame con rendimientos actuales
        yields_past: DataFrame con rendimientos pasados
        
    Returns:
        Tuple con (cartera_mejores, cartera_peores)
    """
    best, worst = pd.DataFrame(), pd.DataFrame()
    
    for idx, row in yields_past.iterrows():
        ordenadas = row.sort_values()
        best5_tickers = list(ordenadas.index[-6:-1])
        worst5_tickers = list(ordenadas.index[0:5])
        
        week = yields.loc[yields.index == idx]
        weekBest = week.transpose().loc[best5_tickers]
        weekWorst = week.transpose().loc[worst5_tickers]
        
        worst = pd.concat([worst, weekWorst], axis=1)
        best = pd.concat([best, weekBest], axis=1)
    
    best = best.transpose()
    worst = worst.transpose()
    best['yield'] = best.mean(axis=1)
    worst['yield'] = worst.mean(axis=1)
    
    return best, worst

def calcular_rendimientos_acumulados(yields: pd.DataFrame, best: pd.DataFrame, worst: pd.DataFrame) -> None:
    """
    Calcula los rendimientos acumulados para todas las carteras.
    
    Args:
        yields: DataFrame con rendimientos de buy & hold
        best: DataFrame con rendimientos de cartera de mejores
        worst: DataFrame con rendimientos de cartera de peores
    """
    yields['yield'] = yields.mean(axis=1)
    
    best['yieldAcum'] = (best['yield'] + 1).cumprod() - 1
    worst['yieldAcum'] = (worst['yield'] + 1).cumprod() - 1
    yields['yieldAcum'] = (yields['yield'] + 1).cumprod() - 1
    
    return yields, best, worst

def calcular_metricas(yields: pd.DataFrame, best: pd.DataFrame, worst: pd.DataFrame, años: int) -> pd.DataFrame:
    """
    Calcula métricas de rendimiento para las tres carteras.
    
    Args:
        yields: DataFrame con rendimientos de buy & hold
        best: DataFrame con rendimientos de cartera de mejores
        worst: DataFrame con rendimientos de cartera de peores
        años: Número de años para cálculo de CAGR
        
    Returns:
        DataFrame con métricas calculadas
    """
    results = pd.DataFrame()
    
    # Calcular CAGR (Compound Annual Growth Rate)
    results.loc['Buy & Hold', 'CAGR'] = (yields['yield'] + 1).prod() ** (1 / años) - 1
    results.loc['Best 5 Portfolio', 'CAGR'] = (best['yield'] + 1).prod() ** (1 / años) - 1
    results.loc['Worst 5 Portfolio', 'CAGR'] = (worst['yield'] + 1).prod() ** (1 / años) - 1
    
    # Calcular Sharpe Ratio (asumiendo risk-free = 0)
    results['Sharpe'] = [
        sharpe_ratio(yields['yield']),
        sharpe_ratio(best['yield']),
        sharpe_ratio(worst['yield'])
    ]
    
    # Calcular volatilidad (desviación estándar anualizada)
    results['Volatilidad'] = [
        yields['yield'].std() * np.sqrt(52),
        best['yield'].std() * np.sqrt(52),
        worst['yield'].std() * np.sqrt(52)
    ]
    
    # Calcular máxima caída (drawdown)
    results['Max Drawdown'] = [
        calcular_max_drawdown(yields['yieldAcum']),
        calcular_max_drawdown(best['yieldAcum']),
        calcular_max_drawdown(worst['yieldAcum'])
    ]
    
    return results

def sharpe_ratio(returns, risk_free=0):
    """
    Calcula el ratio de Sharpe (anualizado).
    
    Args:
        returns: Serie de rendimientos
        risk_free: Tasa libre de riesgo
        
    Returns:
        Ratio de Sharpe anualizado
    """
    return (returns.mean() - risk_free) / returns.std() * (52 ** 0.5)  # 52 semanas

def calcular_max_drawdown(returns):
    """
    Calcula la máxima caída (drawdown) para una serie de rendimientos acumulados.

    Args:
        returns: Serie de rendimientos acumulados

    Returns:
        Máximo drawdown en porcentaje
    """
    peak = returns.cummax()
    drawdown = (returns - peak) / peak
    return drawdown.min()

def graficar_rendimientos(yields: pd.DataFrame, best: pd.DataFrame, worst: pd.DataFrame) -> Tuple[plt.Figure, plt.Figure]:
    """
    Genera gráficos de rendimientos acumulados.

    Args:
        yields: DataFrame con rendimientos de buy & hold
        best: DataFrame con rendimientos de cartera de mejores
        worst: DataFrame con rendimientos de cartera de peores

    Returns:
        Tuple con las figuras generadas
    """
    # Gráfico principal
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(yields.yieldAcum, lw=1, c='tab:blue', label='Buy&Hold')
    ax.plot(best.yieldAcum, lw=1, c='tab:green', label='Rolling Best5 previous yield week return')
    ax.plot(worst.yieldAcum, lw=1, c='tab:red', label='Rolling Worst5 previous yield week return')
    plt.suptitle('Compare Buy&Hold vs Active Portfolio', y=0.95, fontsize=16)
    plt.legend(fontsize=14)
    plt.grid(alpha=0.3)

    # Gráficos anuales
    end = dt.date.today()
    años_total = años
    columns = 3
    rows = años_total // columns + (1 if años_total % columns > 0 else 0)

    fig2, ax2 = plt.subplots(figsize=(14, 4 * rows), nrows=rows, ncols=columns)

    for i in range(años_total):
        dtFrom = dt.datetime(end.year - años_total + i, 1, 1)
        dtTo = dt.datetime(end.year - años_total + i + 1, 1, 1)

        yieldsYr = yields.loc[(yields.index > dtFrom) & (yields.index < dtTo)].copy()
        bestYr = best.loc[(best.index > dtFrom) & (best.index < dtTo)].copy()
        worstYr = worst.loc[(worst.index > dtFrom) & (worst.index < dtTo)].copy()

        bestYr['yieldAcum'] = (bestYr['yield'] + 1).cumprod() - 1
        worstYr['yieldAcum'] = (worstYr['yield'] + 1).cumprod() - 1
        yieldsYr['yieldAcum'] = (yieldsYr['yield'] + 1).cumprod() - 1

        row = i // columns
        col = i % columns

        ax2[row][col].plot(yieldsYr.yieldAcum, lw=1, c='tab:blue')
        ax2[row][col].plot(bestYr.yieldAcum, lw=1, c='tab:green')
        ax2[row][col].plot(worstYr.yieldAcum, lw=1, c='tab:red')
        ax2[row][col].set_title(str(end.year - años_total + i), y=0.83, fontsize=20, alpha=0.4)
        ax2[row][col].grid(alpha=0.2)
        plt.setp(ax2[row][col].get_xticklabels(), visible=False)

    plt.tight_layout()
    return fig, fig2

def main(tickers: Optional[List[str]] = None, años: int = 10) -> None:
    """
    Función principal que ejecuta todo el análisis.

    Args:
        tickers: Lista de símbolos de cotización (opcional)
        años: Número de años para el análisis
    """
    if tickers is None:
        tickers = ["GGAL", "BMA", "YPF", "PAM", "TGS", "CRESY", "IRS", "TEO", "MELI",
                   "EDN", "BBAR", "CEPU", "TX", "SUPV", "LOMA"]

    print(f"Analizando {len(tickers)} activos durante {años} años...")

    # Descargar y procesar datos
    data = descargar_datos(tickers, años)
    yields, yields_past = calcular_rendimientos(data)
    best, worst = seleccionar_carteras(yields, yields_past)
    yields, best, worst = calcular_rendimientos_acumulados(yields, best, worst)

    # Calcular métricas
    results = calcular_metricas(yields, best, worst, años)
    print("\nResultados del análisis:")
    print(results)

    # Generar gráficos
    fig1, fig2 = graficar_rendimientos(yields, best, worst, años)

    plt.show()

if __name__ == "__main__":
    main()