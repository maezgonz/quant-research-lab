import os
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import requests
import warnings

warnings.filterwarnings("ignore")

# === CONFIGURACIÓN ===
TICKER = 'DUOL'
COMPANY_NAME = 'Duolingo'
# NewsAPI key via environment variable (https://newsapi.org/account)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

start_date = '2004-01-01'
end_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

forecast_days = 30
lookback = 1000
zoom_period = 180


# === FUNCIONES AUXILIARES ===
def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_news_sentiment(company_name, api_key, days_back=7):
    from_date = (datetime.today() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={company_name}&"
        f"from={from_date}&"
        f"sortBy=publishedAt&"
        f"language=en&"
        f"apiKey={api_key}"
    )
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ NewsAPI error: {response.json().get('message', 'Unknown')}")
            return 0.0
        articles = response.json().get('articles', [])
        print(f"✅ Noticias obtenidas: {len(articles)} (últimos {days_back} días)")
    except Exception as e:
        print(f"⚠️ Error al conectar con NewsAPI: {e}")
        return 0.0

    if not articles:
        return 0.0

    positive_words = {'up', 'surge', 'gain', 'beat', 'growth', 'profit', 'strong', 'buy', 'outperform', 'rise', 'jump',
                      'soar'}
    negative_words = {'down', 'drop', 'fall', 'loss', 'decline', 'miss', 'weak', 'sell', 'crash', 'risk', 'plunge',
                      'tumble', 'collapse'}

    total_score = 0
    for article in articles[:20]:
        title = (article.get('title') or '').lower()
        description = (article.get('description') or '').lower()
        text = f"{title} {description}"
        words = set(text.replace('.', ' ').replace(',', ' ').replace('!', ' ').replace('?', ' ').split())

        pos = len(words & positive_words)
        neg = len(words & negative_words)
        total_score += (pos - neg)

    sentiment = np.clip(total_score / max(len(articles), 1), -1.0, 1.0)
    return float(sentiment)


# === 1. DESCARGAR DATOS ===
print(".Descargando datos de Yahoo Finance...")
data = yf.download(TICKER, start=start_date, end=end_date)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(1)

if data.empty or len(data) < 30:
    raise ValueError(f"⚠️ No hay suficientes datos para {TICKER}. ¿Está listado o suspendido?")

# === 2. OBTENER SENTIMIENTO ===
sentiment_score = get_news_sentiment(COMPANY_NAME, NEWS_API_KEY)

# === 3. INGENIERÍA DE FEATURES ===
df = data[['Close', 'High', 'Low', 'Volume']].copy()
df['Return'] = df['Close'].pct_change()
df['Volatility_20'] = df['Return'].rolling(window=20).std() * np.sqrt(252)
df['SMA_50'] = df['Close'].rolling(50).mean()
df['RSI'] = compute_rsi(df['Close'], window=14)
df['News_Sentiment'] = sentiment_score
df = df.dropna()

if len(df) < 100:
    raise ValueError(f"⚠️ Demasiados NaN: solo {len(df)} filas válidas.")

# === 4. MODELO GPR CON TENDENCIA LINEAL ===
close_prices = df['Close'].values
dates = df.index
window_gpr = min(50, len(close_prices))
if window_gpr < 20:
    raise ValueError("Insuficientes datos para GPR.")

x_trend = np.arange(window_gpr)
coeffs = np.polyfit(x_trend, close_prices[-window_gpr:], deg=1)
trend_slope, trend_intercept = coeffs
trend_line = np.polyval(coeffs, x_trend)
ytrain_gpr = close_prices[-window_gpr:] - trend_line

xtrain = np.arange(window_gpr, dtype=float)
xtest = np.arange(window_gpr + forecast_days, dtype=float)


def rbf_kernel_matrix(X1, X2, l):
    X1 = X1[:, None]
    X2 = X2[None, :]
    return np.exp(-0.5 * ((X1 - X2) / l) ** 2)


def nll(params, X, y):
    l, sn = params
    if l <= 0 or sn <= 0:
        return np.inf
    K = rbf_kernel_matrix(X, X, l) + np.eye(len(X)) * sn ** 2
    try:
        L = np.linalg.cholesky(K)
        alpha = np.linalg.solve(L.T, np.linalg.solve(L, y))
        return 0.5 * y @ alpha + np.sum(np.log(np.diag(L))) + 0.5 * len(y) * np.log(2 * np.pi)
    except np.linalg.LinAlgError:
        return np.inf


res = minimize(nll, [5.0, 0.02], args=(xtrain, ytrain_gpr), bounds=[(0.1, 50), (1e-4, 1)], method='L-BFGS-B')
l_opt, sn_opt = res.x if res.success else (5.0, 0.02)

# --- Cálculo GPR ---
try:
    Ktrain = rbf_kernel_matrix(xtrain, xtrain, l_opt) + np.eye(window_gpr) * sn_opt ** 2
    K_star = rbf_kernel_matrix(xtrain, xtest, l_opt)
    K_inv_y = np.linalg.solve(Ktrain, ytrain_gpr)

    mu_residuals = K_star.T @ K_inv_y
    x_trend_future = np.arange(window_gpr, window_gpr + forecast_days)
    trend_future = np.polyval([trend_slope, trend_intercept], x_trend_future)

    mu_residuals_forecast = mu_residuals[-forecast_days:]
    mu_gpr = mu_residuals_forecast + trend_future

    v = np.linalg.solve(Ktrain, K_star)
    var = np.diag(rbf_kernel_matrix(xtest, xtest, l_opt) - K_star.T @ v)
    std_gpr = np.sqrt(np.clip(var, 0, None))

    mu_gpr = np.atleast_1d(mu_gpr).ravel()
    std_gpr = np.atleast_1d(std_gpr).ravel()

    forecast_gpr = mu_gpr
    conf_upper_gpr = forecast_gpr + 1.96 * std_gpr[-forecast_days:]
    conf_lower_gpr = forecast_gpr - 1.96 * std_gpr[-forecast_days:]

except Exception as e:
    print(f"⚠️ GPR falló ({e}), usando fallback.")
    last_price = close_prices[-1]
    forecast_gpr = np.full(forecast_days, last_price)
    conf_upper_gpr = np.full(forecast_days, last_price * 1.03)
    conf_lower_gpr = np.full(forecast_days, last_price * 0.97)

# === 5. MODELO RANDOM FOREST ===
feature_cols = ['Close', 'Volatility_20', 'RSI', 'SMA_50', 'Volume', 'News_Sentiment']
df_feats = df[feature_cols].copy()

X, y = [], []
seq_len = 30
for i in range(seq_len, len(df_feats) - forecast_days):
    X.append(df_feats.iloc[i - seq_len:i].values.flatten())
    y.append(df_feats['Close'].iloc[i + forecast_days - 1])

forecast_rf = None
if len(X) > 50:
    X, y = np.array(X), np.array(y)
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_scaled, y_scaled)

    last_window = df_feats.iloc[-seq_len:].values.flatten().reshape(1, -1)
    last_window_scaled = scaler_X.transform(last_window)
    pred_scaled = model.predict(last_window_scaled)
    forecast_rf = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).ravel()[0]

# === 6. BACKTESTING (post-forecast real) ===
real_future_dates, real_future_prices = [], []
try:
    future_end = datetime.today().strftime('%Y-%m-%d')
    future_data = yf.download(TICKER, start=dates[-1] + timedelta(days=1), end=future_end)

    if isinstance(future_data.columns, pd.MultiIndex):
        future_data.columns = future_data.columns.droplevel(1)

    if not future_data.empty and 'Close' in future_data.columns:
        close_series = future_data['Close'].dropna()
        if len(close_series) > 0:
            real_future_dates = close_series.index.tolist()
            real_future_prices = close_series.values.tolist()
except Exception as e:
    print(f"⚠️ Error al obtener datos futuros: {e}")
    pass

# === 7. GRAFICAR ===
plt.style.use('default')
fig, ax = plt.subplots(figsize=(14, 7))

# Histórico
ax.plot(dates[-zoom_period:], df['Close'].iloc[-zoom_period:],
        color='#2C3E50', linewidth=1.8, label='Precio histórico')

# GPR
forecast_dates = [dates[-1] + timedelta(days=i) for i in range(1, forecast_days + 1)]
ax.plot(forecast_dates, forecast_gpr,
        color='#E74C3C', linewidth=2.2, marker='o', markersize=4, label='GPR Forecast')

ax.fill_between(forecast_dates, conf_lower_gpr, conf_upper_gpr,
                color='#E74C3C', alpha=0.2, label='GPR 95% CI')

# RF
if forecast_rf is not None:
    ax.plot(forecast_dates, [forecast_rf] * forecast_days,
            color='#27AE60', linestyle='--', linewidth=2, label='RF + Noticias')

# Real
if real_future_dates and real_future_prices:
    ax.plot(real_future_dates, real_future_prices,
            color='#8E44AD', linewidth=2, marker='x', markersize=6, label='Precio real (post-forecast)')

# Línea de corte
ax.axvline(dates[-1], color='#7F8C8D', linestyle='--', linewidth=1, label='Último dato conocido')

# === TÍTULO Y LEYENDA COMO SUBTÍTULO ===
ax.set_title(f'{TICKER} ({COMPANY_NAME}) – Pronóstico con Noticias y Backtesting',
             fontsize=16, fontweight='bold', pad=15)

legend_text = (
    "█ Precio histórico   "
    "● GPR Forecast   "
    "█ GPR 95% CI   "
    "⸻ RF + Noticias   "
    "ˣ Precio real   "
    "⸻ Último dato"
)
fig.text(0.5, 0.92, legend_text, ha='center', fontsize=10, color='#555555', fontfamily='monospace')

ax.set_xlabel('Fecha')
ax.set_ylabel('Precio (USD)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.xticks(rotation=45)
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.show()

# === 8. RESUMEN EN TERMINAL ===
print("\n" + "=" * 60)
print("🔍 RESUMEN DEL ANÁLISIS")
print("=" * 60)
print(f"Ticker:          {TICKER}")
print(f"Empresa:         {COMPANY_NAME}")
print(f"Último precio:   ${df['Close'].iloc[-1]:.2f} ({dates[-1].strftime('%Y-%m-%d')})")
print(f"Sentimiento noticias: {sentiment_score:+.3f} (rango: -1 a +1)")
print(f"Pronóstico GPR (día {forecast_days}): ${forecast_gpr[-1]:.2f}")
if forecast_rf is not None:
    print(f"Pronóstico RF + noticias:     ${forecast_rf:.2f}")
if real_future_dates and real_future_prices:
    print(f"Precio real más reciente:     ${real_future_prices[-1]:.2f} ({real_future_dates[-1].strftime('%Y-%m-%d')})")
    if len(real_future_prices) <= len(forecast_gpr):
        error_gpr = abs(forecast_gpr[len(real_future_prices) - 1] - real_future_prices[-1])
        print(f"Error absoluto GPR:           ${error_gpr:.2f}")
print("=" * 60)

# === 9. BACKTESTING WALK-FORWARD RIGUROSO ===
print("\n🔍 Iniciando backtesting walk-forward (últimos 100 días)...")

oos_start = max(200, len(df) - 100)
oos_end = len(df)

directional_hits = 0
mae_sum = 0
returns_strategy = []
returns_random_walk = []
n_valid = 0

for t in range(oos_start, oos_end):
    try:
        train_close = df['Close'].iloc[t - 200:t].values
        if len(train_close) < 50:
            continue

        window_wf = min(50, len(train_close))
        x_trend_wf = np.arange(window_wf)
        coeffs_wf = np.polyfit(x_trend_wf, train_close[-window_wf:], deg=1)
        trend_line_wf = np.polyval(coeffs_wf, x_trend_wf)
        ytrain_wf = train_close[-window_wf:] - trend_line_wf

        xtrain_wf = np.arange(window_wf, dtype=float)
        xtest_wf = np.arange(window_wf + 1, dtype=float)

        Ktrain_wf = rbf_kernel_matrix(xtrain_wf, xtrain_wf, l_opt) + np.eye(window_wf) * sn_opt ** 2
        K_star_wf = rbf_kernel_matrix(xtrain_wf, xtest_wf, l_opt)
        K_inv_y_wf = np.linalg.solve(Ktrain_wf, ytrain_wf)
        mu_resid_wf = K_star_wf.T @ K_inv_y_wf
        trend_fut_wf = np.polyval(coeffs_wf, [window_wf])
        pred_gpr_wf = mu_resid_wf[-1] + trend_fut_wf[0]

        actual = df['Close'].iloc[t]
        prev = df['Close'].iloc[t - 1]
        pred_rw = prev

        # Dirección
        if np.sign(pred_gpr_wf - prev) == np.sign(actual - prev):
            directional_hits += 1

        mae_sum += abs(pred_gpr_wf - actual)

        # Rendimientos
        strat_ret = (actual / prev - 1) * np.sign(pred_gpr_wf - prev)
        rw_ret = (actual / prev - 1)

        returns_strategy.append(strat_ret)
        returns_random_walk.append(rw_ret)
        n_valid += 1

    except Exception:
        continue

# --- Resultados ---
if n_valid > 0:
    acc_dir = directional_hits / n_valid
    mae = mae_sum / n_valid
    returns_strategy = np.array(returns_strategy)
    returns_rw = np.array(returns_random_walk)

    sharpe_gpr = np.mean(returns_strategy) / np.std(returns_strategy) * np.sqrt(252) if np.std(
        returns_strategy) > 1e-8 else 0
    sharpe_rw = np.mean(returns_rw) / np.std(returns_rw) * np.sqrt(252) if np.std(returns_rw) > 1e-8 else 0

    net_gpr = (np.prod(1 + returns_strategy) - 1) * 100
    net_rw = (np.prod(1 + returns_rw) - 1) * 100

    print("\n" + "=" * 60)
    print("📊 RESULTADOS DEL BACKTESTING WALK-FORWARD (100 días)")
    print("=" * 60)
    print(f"Días evaluados:             {n_valid}")
    print(f"Acierto direccional:       {acc_dir:.1%}")
    print(f"MAE del pronóstico:        ${mae:.2f}")
    print(f"Retorno neto (estrategia): {net_gpr:+.2f}%")
    print(f"Retorno neto (buy & hold): {net_rw:+.2f}%")
    print(f"Sharpe ratio (estrategia): {sharpe_gpr:.2f}")
    print(f"Sharpe ratio (buy & hold): {sharpe_rw:.2f}")

    if acc_dir > 0.55 and sharpe_gpr > sharpe_rw:
        print("\n✅ El modelo muestra ventaja estadística marginal.")
        print("   Considerar solo con gestión de riesgo estricta.")
    else:
        print("\n❌ El modelo no supera consistentemente al Random Walk.")
        print("   No recomendado para operar en vivo.")

    print("=" * 60)
else:
    print("⚠️ Insuficientes datos para backtesting.")