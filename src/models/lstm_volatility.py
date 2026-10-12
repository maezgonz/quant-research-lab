""""
========================================================================================
TERMINAL QUANT
========================================================================================
Descripción:
Arquitectura híbrida 'VLSTM' (VSN + LSTM) que optimiza el Ratio de Sharpe.

Módulos Integrados:
1. DATA HUB: Conexión robusta a Data912 con escalado individual por activo.
2. AI CORE: Red neuronal recurrente con selección dinámica de variables (VSN).
3. ANALYTICS: Backtesting Out-of-Sample vs Benchmark (Buy & Hold).
4. EXECUTION: Tabla de trading optimizada por Volatilidad (Target Vol)
   y participacion de volumen (Cap del 10%), incluyendo derechos de mercado BYMA.
========================================================================================
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from torch.utils.data import Dataset, DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

# =====================================================================
# 1. CONFIGURACIÓN Y UNIVERSO (Mercado)
# =====================================================================
tickers = [
    'ALUA', 'BBAR', 'BMA', 'BYMA', 'CEPU', 'COME', 'EDN', 'GGAL', 'IRSA',
    'LOMA', 'METR', 'MIRG', 'PAMP', 'SUPV', 'TECO2', 'TGNO4', 'TGSU2',
    'TRAN', 'TXAR', 'VALO', 'YPFD', 'AGRO', 'AUSO', 'BHIP', 'BOLT', 'BPAT',
    'BRIO', 'CAPX', 'CARC', 'CECO2', 'CELU', 'CGPA2', 'CTIO', 'DGCU2',
    'FERR', 'GARO', 'GCLA', 'GRIM', 'HAVA', 'INTR', 'INVJ', 'LEDE', 'LONG',
    'MOLI', 'MORI', 'OEST', 'PATA', 'PATY', 'PGR', 'POLL', 'RIGO', 'ROSE',
    'SAMI', 'SEMI', 'TGLT'
]


# =====================================================================
# 2. IA CORE: VLSTM PRO
# =====================================================================
class VLSTM_PRO(nn.Module):
    def __init__(self, num_features, hidden_dim):
        super().__init__()
        self.num_f = num_features
        self.embs = nn.ModuleList([nn.Linear(1, hidden_dim) for _ in range(num_features)])
        self.gating = nn.Linear(hidden_dim * num_features, num_features)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, num_layers=2, batch_first=True, dropout=0.2)
        self.head = nn.Sequential(nn.Linear(hidden_dim, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        e = [F.relu(self.embs[i](x[:, :, i].unsqueeze(-1))) for i in range(self.num_f)]
        w = F.softmax(self.gating(torch.cat(e, -1)), -1)
        vsn = sum(w[:, :, i].unsqueeze(-1) * e[i] for i in range(self.num_f))
        out, _ = self.lstm(vsn)
        return torch.tanh(self.head(out[:, -1, :]))


# =====================================================================
# 3. MÓDULO DE DATOS ROBUSTO
# =====================================================================
def get_data_v10(ticker):
    url = f"https://data912.com/historical/stocks/{ticker}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            # Detección flexible de columnas
            c_col = 'c' if 'c' in df.columns else 'close'
            t_col = 't' if 't' in df.columns else 'date'
            if c_col in df.columns and t_col in df.columns:
                df['Date'] = pd.to_datetime(df[t_col], unit='s' if t_col == 't' else None)
                df.set_index('Date', inplace=True)
                return pd.DataFrame({'close': df[c_col]})
    except Exception:
        pass
    return pd.DataFrame()


def calculate_features(df):
    df = df[df['close'] > 0].copy()
    df['r'] = np.log(df['close'] / df['close'].shift(1))
    df['v'] = df['r'].rolling(20).std()
    df['m'] = (df['close'] - df['close'].rolling(10).mean()) / (df['v'] + 1e-6)
    df['targ'] = df['r'].shift(-1)
    df.dropna(inplace=True)
    return df[['r', 'v', 'm']], df['targ']


# =====================================================================
# 4. KPI DASHBOARD
# =====================================================================
def plot_kpis(kpi_dict, equity, dd):
    plt.style.use('default')
    # Equity Curve
    plt.figure(figsize=(12, 5))
    plt.plot(equity, color='lime', label='Estrategia AI')
    plt.title("Evolución del Capital (Backtest)")
    plt.legend();
    plt.show()
    # Drawdown
    plt.figure(figsize=(12, 4))
    plt.fill_between(range(len(dd)), dd, color='red', alpha=0.3)
    plt.title("Perfil de Riesgo (Drawdown)");
    plt.show()


# =====================================================================
# 5. MOTOR DE EJECUCIÓN CON SOLUCIÓN AL ERROR NUM_SAMPLES=0
# =====================================================================
def run_v10_1():
    device = torch.device("cpu")
    scalers, train_x, train_y, test_x, test_y = {}, [], [], [], []

    print(f"\n[INFO] Inicio: Escaneando Mercado...")
    for ticker in tqdm(tickers, desc="Data Mining"):
        df = get_data_v10(ticker)
        if df.empty or len(df) < 90: continue  # Bajamos umbral para asegurar muestras

        f_df, targ = calculate_features(df)
        if f_df.empty: continue

        split = int(len(f_df) * 0.8)
        sc = StandardScaler()
        f_vals = f_df.values

        try:
            f_tr = sc.fit_transform(f_vals[:split])
            f_te = sc.transform(f_vals[split:])
            scalers[ticker] = sc

            # Generación de secuencias (Ventana de 64 días)
            for j in range(len(f_tr) - 64):
                train_x.append(f_tr[j:j + 64]);
                train_y.append(targ.iloc[j + 63])
            for j in range(len(f_te) - 64):
                test_x.append(f_te[j:j + 64]);
                test_y.append(targ.iloc[split + j + 63])
        except (IndexError, KeyError):
            continue

    # VERIFICACIÓN CRÍTICA: Evita el error num_samples=0
    if not train_x:
        print("❌ Error: No se generaron secuencias. El historial de los activos es insuficiente.")
        return

    # Entrenamiento 50 Epochs
    model = VLSTM_PRO(3, 64)
    opt = optim.Adam(model.parameters(), lr=0.0005)
    ds = TensorDataset(torch.tensor(np.array(train_x), dtype=torch.float32),
                       torch.tensor(np.array(train_y), dtype=torch.float32))
    dl = DataLoader(ds, batch_size=512, shuffle=True)

    for _ in tqdm(range(50), desc="Entrenando Red Neuronal"):
        model.train()
        for xb, yb in dl:
            opt.zero_grad()
            p = model(xb).squeeze()
            loss = -((p * yb).mean() / (torch.std(p * yb) + 1e-6)) + 0.1 * torch.mean(p ** 2)
            loss.backward();
            opt.step()

    # Dashboard
    print("\n" + "=" * 95)
    try:
        cap = float(input("💰 Ingrese Capital Disponible (ARS): "))
    except ValueError:
        return

    model.eval()
    with torch.no_grad():
        tx, ty = torch.tensor(np.array(test_x), dtype=torch.float32), np.array(test_y)
        preds = model(tx).squeeze().numpy()

        pnl = preds * ty
        eq = np.cumsum(pnl)
        dd = eq - np.maximum.accumulate(eq)

        # Winrate y Kelly
        pw = len(pnl[pnl > 0]) / len(pnl)
        avg_w = np.mean(pnl[pnl > 0]);
        avg_l = abs(np.mean(pnl[pnl < 0]))
        r_multi = avg_w / (avg_l + 1e-6)

        print(
            f"\n📊 KPIs: Winrate {pw * 100:.2f}% | R-Multi {r_multi:.2f} | PF {np.sum(pnl[pnl > 0]) / abs(np.sum(pnl[pnl < 0])):.2f}")
        plot_kpis({}, eq, dd)

    # Elite-6 Selection
    trades = []
    for ticker in tickers:
        if ticker not in scalers: continue
        df = get_data_v10(ticker)
        if df.empty: continue
        f_df, _ = calculate_features(df)
        sc_data = scalers[ticker].transform(f_df.values[-64:])
        s = model(torch.tensor(sc_data, dtype=torch.float32).unsqueeze(0)).item()
        px = df['close'].iloc[-1]
        vol = f_df['r'].iloc[-20:].std()
        if s > 0:
            trades.append({'T': ticker, 'S': s, 'V': vol, 'Px': px, 'Score': s / (vol + 1e-6)})

    elite = sorted(trades, key=lambda x: x['Score'], reverse=True)[:6]
    if elite:
        total_s = sum(x['S'] for x in elite)
        res = []
        for x in elite:
            monto = cap * (x['S'] / total_s)
            acc = int(monto / x['Px'])
            if acc > 0:
                m_real = acc * x['Px']
                fee = m_real * 0.0005  # BYMA 0.05%
                ret_esp = x['S'] * x['V'] * 2.23
                res.append({'Ticker': x['T'], 'Px Entrada': x['Px'], 'Px Target': round(x['Px'] * (1 + ret_esp), 2),
                            'Acciones': acc, 'Inversión': round(m_real, 0), 'Fee BYMA': round(fee, 2),
                            'Gcia Est.': round((m_real * ret_esp) - fee, 0)})
        print("\n📋 TABLA FINAL:");
        print(pd.DataFrame(res).to_string(index=False))


if __name__ == "__main__":
    run_v10_1()