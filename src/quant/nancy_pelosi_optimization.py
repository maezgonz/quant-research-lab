### Optimización de Portafolio usando RiskFolio ###
import riskfolio as rp
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

class PortfolioOptimizer:
    def __init__(self, assets, start_date=None, end_date=None, benchmark="^GSPC"):
        self.assets = assets
        self.benchmark = benchmark
        
        # Si no se especifican fechas, usar último año
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        self.start_date = start_date
        self.end_date = end_date
        self.assets_with_bench = self.assets + [self.benchmark]
        
        # Inicializar atributos
        self.data = None
        self.returns = None
        self.returns_bench = None
        self.portfolio = None
        self.weights = None

    def fetch_data(self):
        try:
            self.data = yf.download(self.assets_with_bench, 
                                  start=self.start_date, 
                                  end=self.end_date,
                                  progress=True)
            
            # Usar 'Close' si 'Adj Close' no está disponible
            if 'Adj Close' in self.data.columns:
                price_data = self.data['Adj Close']
            else:
                price_data = self.data['Close']
                print("Usando precios de cierre en lugar de precios ajustados")
            
            if price_data.empty:
                raise ValueError("No se obtuvieron datos de precios")
            
            returns_all = price_data.pct_change().dropna()
            
            if self.benchmark not in returns_all.columns:
                raise ValueError(f"No se encontraron datos para el benchmark {self.benchmark}")
            
            self.returns_bench = returns_all.pop(self.benchmark).to_frame()
            self.returns = returns_all
            
            if len(self.returns) < 2:
                raise ValueError("Insuficientes datos para el análisis")
                
            print(f"Datos obtenidos exitosamente: {len(self.returns)} días de trading")
            return True
            
        except Exception as e:
            print(f"Error al obtener datos: {str(e)}")
            return False

    def optimize_portfolio(self, model="Classic", risk_measure="CVaR", 
                         objective="Sharpe", risk_free_rate=0, l=0):
        try:
            # Crear y configurar el portafolio
            self.portfolio = rp.Portfolio(returns=self.returns)
            
            # Calcular estadísticas de los activos
            self.portfolio.assets_stats(method_mu='hist', method_cov='hist')
            
            # Establecer benchmark
            self.portfolio.benchindex = self.returns_bench
            
            # Optimizar
            self.weights = self.portfolio.optimization(
                model=model,
                rm=risk_measure,
                obj=objective,
                hist=True,
                rf=risk_free_rate,
                l=l
            )
            
            print("\nPesos óptimos del portafolio:")
            print(self.weights)
            return True
            
        except Exception as e:
            print(f"Error en la optimización: {e}")
            return False

    def plot_portfolio_composition(self):
        if self.weights is None:
            print("Primero debe optimizar el portafolio")
            return
            
        # Crear figura
        plt.figure(figsize=(10, 6))
        
        # Ordenar pesos para mejor visualización
        weights_sorted = self.weights.sort_values(ascending=True)
        
        # Crear gráfico de barras horizontal
        bars = plt.barh(range(len(weights_sorted)), weights_sorted.values * 100)
        
        # Añadir etiquetas
        plt.yticks(range(len(weights_sorted)), weights_sorted.index)
        plt.xlabel('Peso en el Portafolio (%)')
        plt.title('Composición Óptima del Portafolio')
        
        # Añadir valores en las barras
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2,
                    f'{width:.1f}%',
                    ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.show()

    def plot_portfolio_performance(self):
        if self.weights is None or self.returns is None:
            print("Primero debe optimizar el portafolio")
            return
        
        try:
            # Calcular retornos del portafolio
            portfolio_returns = (self.returns @ self.weights).values
            portfolio_returns = portfolio_returns.reshape(-1)
            cumulative_returns = (1 + portfolio_returns).cumprod()
            
            # Calcular retornos del benchmark
            benchmark_returns = self.returns_bench.values.flatten()
            cumulative_benchmark = (1 + benchmark_returns).cumprod()
            
            # Crear gráfico
            plt.figure(figsize=(12, 6))
            
            # Graficar rendimientos acumulados
            plt.plot(self.returns.index, cumulative_returns, 
                    label='Portafolio', linewidth=2, color='blue')
            plt.plot(self.returns.index, cumulative_benchmark, 
                    label='Benchmark (S&P 500)', linewidth=2, 
                    color='red', alpha=0.7)
            
            # Personalizar gráfico
            plt.title('Rendimiento del Portafolio vs S&P 500', fontsize=12, pad=15)
            plt.xlabel('Fecha', fontsize=10)
            plt.ylabel('Retorno Acumulado', fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.legend(fontsize=10)
            
            # Añadir anotaciones con métricas clave
            metrics = self.get_portfolio_metrics()
            if metrics is not None:
                info_text = (
                    f'Retorno Anual: {metrics["Retorno Anual (%)"]:.1f}%\n'
                    f'Volatilidad: {metrics["Volatilidad Anual (%)"]:.1f}%\n'
                    f'Sharpe Ratio: {metrics["Ratio de Sharpe"]:.2f}\n'
                    f'Beta: {metrics["Beta"]:.2f}'
                )
                plt.annotate(info_text, xy=(0.02, 0.95), xycoords='axes fraction',
                            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'),
                            fontsize=9, va='top')
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Error al generar gráfico: {str(e)}")

    def get_portfolio_metrics(self):
        if self.weights is None or self.returns is None:
            return None
            
        try:
            # Calcular retornos del portafolio
            portfolio_returns = (self.returns @ self.weights).values
            benchmark_returns = self.returns_bench.values.flatten()
            
            # Asegurar que los arrays tienen la misma forma
            portfolio_returns = portfolio_returns.reshape(-1)
            benchmark_returns = benchmark_returns.reshape(-1)
            
            # Métricas básicas
            annual_return = np.mean(portfolio_returns) * 252 * 100
            annual_vol = np.std(portfolio_returns) * np.sqrt(252) * 100
            sharpe_ratio = annual_return / annual_vol if annual_vol != 0 else 0
            
            # Máximo drawdown
            cum_returns = (1 + portfolio_returns).cumprod()
            running_max = np.maximum.accumulate(cum_returns)
            drawdown = (cum_returns - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
            
            # Beta y Alpha
            returns_matrix = np.vstack([portfolio_returns, benchmark_returns])
            covariance_matrix = np.cov(returns_matrix)
            beta = covariance_matrix[0,1] / np.var(benchmark_returns)
            
            # Alpha (anualizado)
            benchmark_return = np.mean(benchmark_returns) * 252
            portfolio_return = np.mean(portfolio_returns) * 252
            alpha = portfolio_return - (beta * benchmark_return)
            
            # Tracking Error
            tracking_error = np.std(portfolio_returns - benchmark_returns) * np.sqrt(252) * 100
            
            # Información Ratio
            active_return = (annual_return - (np.mean(benchmark_returns) * 252 * 100))
            info_ratio = active_return / tracking_error if tracking_error != 0 else 0
            
            metrics = pd.Series({
                'Retorno Anual (%)': round(annual_return, 2),
                'Volatilidad Anual (%)': round(annual_vol, 2),
                'Ratio de Sharpe': round(sharpe_ratio, 2),
                'Máximo Drawdown (%)': round(max_drawdown, 2),
                'Beta': round(beta, 3),
                'Alpha (%)': round(alpha * 100, 2),
                'Tracking Error (%)': round(tracking_error, 2),
                'Information Ratio': round(info_ratio, 2)
            })
            
            return metrics
            
        except Exception as e:
            print(f"Error al calcular métricas: {str(e)}")
            return None

def main():
    # Lista de activos
    assets = [
        "PAM",
        "GGAL",
        "TGS",
        "YPF",
        "BMA",
        "EDN"
    ]
    
    # Crear instancia del optimizador
    optimizer = PortfolioOptimizer(
        assets=assets,
        start_date="2023-01-01",
        end_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    # Obtener datos
    if not optimizer.fetch_data():
        print("Error al obtener datos. Finalizando programa.")
        return
    
    # Optimizar portafolio
    if not optimizer.optimize_portfolio(
        model="Classic",
        risk_measure="CVaR",
        objective="Sharpe"
    ):
        print("Error en la optimización. Finalizando programa.")
        return
    
    # Mostrar métricas
    print("\nMétricas del Portafolio:")
    metrics = optimizer.get_portfolio_metrics()
    if metrics is not None:
        print(metrics)
    
    # Visualizar resultados
    optimizer.plot_portfolio_composition()
    optimizer.plot_portfolio_performance()

if __name__ == "__main__":
    main()