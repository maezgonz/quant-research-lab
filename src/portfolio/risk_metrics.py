import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
import yaml

# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_plot_style():
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['axes.grid'] = True
    plt.rcParams['lines.linewidth'] = 2

def calcular_sortino_ratio(returns, risk_free_rate=0.02):
    """
    Calcula el ratio de Sortino
    """
    excess_returns = returns - risk_free_rate/252
    downside_returns = returns[returns < 0]
    downside_std = np.sqrt(252) * downside_returns.std()
    
    if downside_std == 0:
        return np.nan
    
    return np.mean(excess_returns) * 252 / downside_std

def calcular_beta(returns, benchmark_returns):
    """
    Calcula el beta del activo respecto al benchmark
    """
    if benchmark_returns is None:
        return None
    
    # Asegurar que los índices coincidan
    common_index = returns.index.intersection(benchmark_returns.index)
    returns = returns[common_index]
    benchmark_returns = benchmark_returns[common_index]
    
    covariance = returns.cov(benchmark_returns)
    benchmark_variance = benchmark_returns.var()
    
    if benchmark_variance == 0:
        return np.nan
        
    return covariance / benchmark_variance

def calcular_metricas(returns, adj_close):
    metrics = {
        'total_return': (adj_close[-1] / adj_close[0]) - 1,
        'volatility': returns.std() * np.sqrt(252),
        'cumulative_returns': (1 + returns).cumprod(),
    }
    metrics['annualized_return'] = (1 + metrics['total_return'])**(252/len(adj_close)) - 1
    metrics['sharpe_ratio'] = metrics['annualized_return'] / metrics['volatility']
    return metrics

def calcular_metricas_adicionales(returns, benchmark_returns=None):
    metrics = {
        'skewness': returns.skew(),
        'kurtosis': returns.kurtosis(),
        'var_95': returns.quantile(0.05),
        'sortino_ratio': calcular_sortino_ratio(returns),
        'beta': calcular_beta(returns, benchmark_returns) if benchmark_returns is not None else None
    }
    return metrics

def visualizar_metricas(data, metrics, ticker, benchmark_data=None):
    # Visualización de precios
    plt.figure(figsize=(12, 6))
    plt.plot(data, label=ticker)
    if benchmark_data is not None:
        plt.plot(benchmark_data, label='Benchmark', alpha=0.7)
    plt.title(f'Precios de {ticker}')
    plt.xlabel('Fecha')
    plt.ylabel('Precio')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    # Visualización de métricas numéricas
    metricas_plot = {k: v for k, v in metrics.items() 
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and k != 'cumulative_returns'}
    
    plt.figure(figsize=(12, 6))
    plt.bar(metricas_plot.keys(), metricas_plot.values())
    plt.title(f'Métricas de {ticker}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def analizar_activo(ticker, benchmark_ticker=None, start_date='2020-01-01', end_date=None):
    """
    Analiza un activo financiero, calcula métricas de rendimiento y riesgo,
    y genera visualizaciones comparativas con un benchmark opcional.

    Args:
        ticker (str): El ticker del activo a analizar (ej: 'AAPL').
        benchmark_ticker (str, optional): El ticker del benchmark para comparar (ej: '^GSPC'). Defaults to None.
        start_date (str, optional): Fecha de inicio para la descarga de datos (YYYY-MM-DD). Defaults to '2020-01-01'.
        end_date (str, optional): Fecha de fin para la descarga de datos (YYYY-MM-DD). Defaults to hoy.

    Returns:
        pandas.DataFrame: Un DataFrame con los precios ajustados del activo y el benchmark (si se proporciona).
    """
    print(f"\n--- Análisis para el activo: {ticker} ---")

    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            raise ValueError(f"No se pudieron descargar datos para {ticker}")
        
        adj_close = data['Close']  # Usar 'Close' en lugar de 'Adj Close'
        returns = adj_close.pct_change().dropna()

        print(f"Número total de observaciones: {len(returns)}")

        # Calcular métricas de rendimiento
        metrics = calcular_metricas(returns, adj_close)

        print(f"Retorno total: {metrics['total_return']:.4f}")
        print(f"Retorno anualizado: {metrics['annualized_return']:.4f}")
        print(f"Volatilidad anualizada: {metrics['volatility']:.4f}")
        print(f"Ratio de Sharpe: {metrics['sharpe_ratio']:.4f}")

        # Calcular drawdown máximo
        cumulative_returns = metrics['cumulative_returns']
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()
        print(f"Drawdown máximo: {max_drawdown:.4f}")

        # Visualizar precios y retornos
        plt.figure(figsize=(12, 6))
        plt.plot(adj_close, label=ticker)
        if benchmark_ticker:
            benchmark_data = yf.download(benchmark_ticker, start=start_date, end=end_date, auto_adjust=False)['Close']
            if not benchmark_data.empty:
                plt.plot(benchmark_data, label=benchmark_ticker, alpha=0.7)
        plt.title(f"Precio Ajustado de {ticker} {'vs ' + benchmark_ticker if benchmark_ticker else ''}")
        plt.xlabel("Fecha")
        plt.ylabel("Precio")
        plt.legend()
        plt.grid(True)
        plt.show()

        plt.figure(figsize=(12, 6))
        plt.plot(returns, label=f"Retornos de {ticker}")
        plt.title(f"Retornos Diarios de {ticker}")
        plt.xlabel("Fecha")
        plt.ylabel("Retorno Diario")
        plt.grid(True)
        plt.show()

        plt.figure(figsize=(12, 6))
        plt.plot(cumulative_returns, label=f"Retornos Acumulados de {ticker}")
        if benchmark_ticker and not benchmark_data.empty:
            benchmark_returns = benchmark_data.pct_change().dropna()
            cumulative_benchmark_returns = (1 + benchmark_returns).cumprod()
            plt.plot(cumulative_benchmark_returns, label=f"Retornos Acumulados de {benchmark_ticker}", alpha=0.7)
        plt.title(f"Retornos Acumulados de {ticker} {'vs ' + benchmark_ticker if benchmark_ticker else ''}")
        plt.xlabel("Fecha")
        plt.ylabel("Retorno Acumulado")
        plt.legend()
        plt.grid(True)
        plt.show()

        plt.figure(figsize=(12, 6))
        plt.plot(drawdown, label=f"Drawdown de {ticker}")
        plt.title(f"Drawdown de {ticker}")
        plt.xlabel("Fecha")
        plt.ylabel("Drawdown")
        plt.grid(True)
        plt.show()

        return pd.DataFrame({'Close': adj_close, 'Benchmark Close': benchmark_data if benchmark_ticker and not benchmark_data.empty else None})
    except Exception as e:
        logger.error(f"Error al analizar {ticker}: {str(e)}")
        return None

def cargar_configuracion():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

config = {
    'activos': [
        {'ticker': 'AAPL', 'benchmark': 'SPY'},
        {'ticker': 'MSFT', 'benchmark': None},
    ],
    'fecha_inicio': '2023-01-01',
    'metricas_habilitadas': ['sharpe', 'sortino', 'drawdown'],
    'visualizaciones_habilitadas': ['precios', 'retornos', 'drawdown']
}

if __name__ == "__main__":
    activos_a_analizar = [
        ('AAPL', 'SPY'),      # Activo: AAPL, Benchmark: SPY
        ('MSFT', None),       # Activo: MSFT, Sin Benchmark
        ('GOOGL', '^IXIC'),   # Activo: GOOGL, Benchmark: NASDAQ
        ('AMZN', 'SPY')       # Puedes agregar más activos y sus benchmarks aquí
    ]

    start_date = '2000-01-01'  # Puedes ajustar la fecha de inicio
    end_date = None  # Usa la fecha actual por defecto

    for activo in activos_a_analizar:
        ticker = activo[0]
        benchmark = activo[1] if len(activo) > 1 else None
        analizar_activo(ticker, benchmark, start_date, end_date)

    print("\n--- Análisis completado ---")
