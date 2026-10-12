import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
import matplotlib.pyplot as plt
from datetime import datetime

# ==========================================
# 1. MOTOR DE CÁLCULO DE MÉTRICAS (QUANT ENGINE)
# ==========================================
def calculate_metrics(trades_df, daily_returns, equity_curve, initial_capital):
    # Si no hay trades, calcular métricas con valores por defecto
    if len(trades_df) == 0:
        return pd.Series({
            "Return": "0.00%",
            "Annualized Return": "0.00%",
            "Sharpe": "0.00",
            "Sortino": "0.00",
            "Calmar": "0.00",
            "Omega Ratio": "0.00",
            "Max Drawdown": "0.00%",
            "Win Rate": "0.0%",
            "Profit Factor": "0.00",
            "EV per Trade": "0.000%",
            "Raw SQN": "0.00",
            "Skewness": "0.00",
            "Kurtosis": "0.00",
            "Exposure Time": "0.0%",
            "Total Trades": 0,
            "Avg Trade Duration": "0 days"
        })

    # --- Métricas de Retorno ---
    total_return = (equity_curve.iloc[-1] - initial_capital) / initial_capital
    days = (equity_curve.index[-1] - equity_curve.index[0]).days
    annualized_return = (1 + total_return) ** (365 / days) - 1
    
    # --- Métricas de Riesgo (Sharpe, Sortino) ---
    risk_free_rate = 0.0
    mean_ret = daily_returns.mean()
    std_ret = daily_returns.std()
    
    # Sharpe (Anualizado)
    sharpe = (mean_ret / std_ret) * np.sqrt(252) if std_ret != 0 else 0
    
    # Sortino (Solo volatilidad negativa)
    downside_returns = daily_returns[daily_returns < 0]
    std_downside = downside_returns.std()
    sortino = (mean_ret / std_downside) * np.sqrt(252) if std_downside != 0 else 0
    
    # Max Drawdown
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    # Calmar Ratio
    calmar = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # Omega Ratio (Threshold 0)
    gains = daily_returns[daily_returns > 0].sum()
    losses = abs(daily_returns[daily_returns < 0].sum())
    omega = gains / losses if losses != 0 else np.inf

    # --- Estadísticas de Trades ---
    wins = trades_df[trades_df['PnL'] > 0]
    losses_trades = trades_df[trades_df['PnL'] <= 0]
    
    win_rate = len(wins) / len(trades_df)
    
    gross_profit = wins['PnL_Currency'].sum()
    gross_loss = abs(losses_trades['PnL_Currency'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf
    
    # EV per Trade (Esperanza Matemática)
    avg_win = wins['PnL'].mean() if len(wins) > 0 else 0
    avg_loss = losses_trades['PnL'].mean() if len(losses_trades) > 0 else 0
    ev_per_trade = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
    
    # SQN (System Quality Number)
    # SQN = raiz(N) * (Expectativa / Desv.Est de R)
    trades_pnl = trades_df['PnL']
    sqn = np.sqrt(len(trades_df)) * (trades_pnl.mean() / trades_pnl.std()) if trades_pnl.std() != 0 else 0
    
    # Skewness & Kurtosis (De los retornos diarios)
    skew_val = skew(daily_returns.dropna())
    kurt_val = kurtosis(daily_returns.dropna())

    # Exposure Time (Tiempo en mercado)
    exposure_time = (equity_curve != initial_capital).sum() / len(equity_curve)  # Simplificado
    
    # Duración Promedio
    trades_df['Duration'] = trades_df['Exit_Date'] - trades_df['Entry_Date']
    avg_duration = trades_df['Duration'].mean()

    # --- Formateo de Salida ---
    metrics = {
        "Return": f"{total_return*100:.2f}%",
        "Annualized Return": f"{annualized_return*100:.2f}%",
        "Sharpe": f"{sharpe:.2f}",
        "Sortino": f"{sortino:.2f}",
        "Calmar": f"{calmar:.2f}",
        "Omega Ratio": f"{omega:.2f}",
        "Max Drawdown": f"{max_drawdown*100:.2f}%",
        "Win Rate": f"{win_rate*100:.1f}%",
        "Profit Factor": f"{profit_factor:.2f}",
        "EV per Trade": f"{ev_per_trade*100:.3f}%",
        "Raw SQN": f"{sqn:.2f}",
        "Skewness": f"{skew_val:.2f}",
        "Kurtosis": f"{kurt_val:.2f}",
        "Exposure Time": f"{exposure_time*100:.1f}%",
        "Total Trades": len(trades_df),
        "Avg Trade Duration": str(avg_duration).split('.')[0]
    }
    
    return pd.Series(metrics)

# ==========================================
# 2. SIMULADOR DE ESTRATEGIA (BACKTESTER)
# ==========================================
def run_strategy(ticker, start_date, end_date):
    print(f"🔄 Descargando datos para {ticker}...")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    except Exception as e:
        raise ValueError(f"Error al descargar datos para {ticker}: {e}")
    
    # Validar y procesar datos
    if data.empty:
        raise ValueError(f"No se encontraron datos para {ticker}. Verifica el ticker (ej. 'GLD' para oro, 'GC=F' para futuros) y las fechas.")
    
    try:
        close_prices = data['Close'].dropna()
        if close_prices.empty:
            raise ValueError(f"No hay precios de cierre válidos para {ticker}.")
        data = pd.DataFrame(close_prices, columns=['Price'])
    except KeyError:
        raise ValueError(f"La columna 'Close' no está disponible para {ticker}. Verifica el ticker.")
    
    # --- ESTRATEGIA: Cruce de Medias (AJUSTADA PARA MÁS SEÑALES) ---
    # Cambiado a SMA 5/10 para más cruces (prueba; ajusta según necesites)
    data['SMA_Fast'] = data['Price'].rolling(window=5).mean()
    data['SMA_Slow'] = data['Price'].rolling(window=10).mean()
    
    initial_capital = 100000.0
    capital = initial_capital
    position = 0  # 0 = Flat, 1 = Long
    trades = []
    equity_curve = []
    
    entry_price = 0
    entry_date = None
    
    # Loop de Backtest
    for i in range(1, len(data)):
        date = data.index[i]
        price = float(data['Price'].iloc[i])
        
        # Señales
        sma_fast_curr = data['SMA_Fast'].iloc[i]
        sma_slow_curr = data['SMA_Slow'].iloc[i]
        sma_fast_prev = data['SMA_Fast'].iloc[i-1]
        sma_slow_prev = data['SMA_Slow'].iloc[i-1]
        
        # BUY SIGNAL
        if position == 0 and sma_fast_prev < sma_slow_prev and sma_fast_curr > sma_slow_curr:
            position = 1
            entry_price = price
            entry_date = date
            shares = capital / price
            
        # SELL SIGNAL
        elif position == 1 and sma_fast_prev > sma_slow_prev and sma_fast_curr < sma_slow_curr:
            position = 0
            exit_price = price
            pnl_currency = (exit_price - entry_price) * shares
            pnl_pct = (exit_price / entry_price) - 1
            capital += pnl_currency
            
            trades.append({
                'Entry_Date': entry_date,
                'Exit_Date': date,
                'Entry_Price': entry_price,
                'Exit_Price': exit_price,
                'PnL': pnl_pct,
                'PnL_Currency': pnl_currency
            })
            
        # Mark to Market
        if position == 1:
            curr_equity = (capital - (entry_price * shares)) + (price * shares)
        else:
            curr_equity = capital
            
        equity_curve.append(curr_equity)

    # Crear DataFrames
    equity_series = pd.Series(equity_curve, index=data.index[1:])
    trades_df = pd.DataFrame(trades)
    daily_returns = equity_series.pct_change().dropna()
    
    print(f"Se generaron {len(trades_df)} operaciones.")  # Debug
    
    return trades_df, daily_returns, equity_series, initial_capital

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================
def main():
    print("========================================")
    print("🚀 QUANT STRATEGY ANALYZER (Python) 🚀")
    print("========================================")
    
    ticker = input("Ingrese el Ticker (ej. GLD, AAPL, BTC-USD): ").upper().strip()
    if not ticker:
        print("❌ Ticker no puede estar vacío.")
        return
    
    start_date = input("Fecha Inicio (YYYY-MM-DD) [Default: 2020-01-01]: ").strip()
    if not start_date:
        start_date = "2020-01-01"
    
    end_date = input("Fecha Fin (YYYY-MM-DD) [Default: Hoy]: ").strip()
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')

    try:
        # Ejecutar Estrategia
        trades, returns, equity, init_cap = run_strategy(ticker, start_date, end_date)
        
        # Calcular Métricas
        print("\n⚗️  Calculando métricas avanzadas...")
        results = calculate_metrics(trades, returns, equity, init_cap)
        
        # Mostrar Tabla
        print("\n" + "="*40)
        print(f"📊 REPORTE DE ESTRATEGIA: {ticker}")
        print("="*40)
        df_result = pd.DataFrame(results, columns=['Valor'])
        print(df_result)
        print("="*40)
        
        # Opcional: Graficar
        plot_opt = input("\n¿Graficar Curva de Equidad? (s/n): ").lower()
        if plot_opt == 's':
            plt.figure(figsize=(12,6))
            plt.plot(equity, label='Capital (Equity Curve)')
            plt.title(f"Curva de Rendimiento: {ticker}")
            plt.ylabel("Capital (USD)")
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.show()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()