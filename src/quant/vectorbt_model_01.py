import vectorbt as vbt
import numpy as np

# Bajamos datos
data = vbt.YFData.download("BTC-USD", period="3y")
price = data.get("Adj Close")

# EXPLOTACIÓN: Probamos 50 combinaciones de medias móviles distintas al mismo tiempo
fast_windows = np.arange(5, 50, 5)  # [5, 10, 15... 45]
slow_windows = np.arange(50, 200, 20) # [50, 70, 90... 190]

# Ejecución masiva
ma_fast, ma_slow = vbt.MA.run_combs(price, window=fast_windows, r=2)
entries = ma_fast.ma_crossed_above(ma_slow)
exits = ma_fast.ma_crossed_below(ma_slow)

# Backtest de todas las combinaciones
pf = vbt.Portfolio.from_signals(price, entries, exits, fees=0.001)

# ¿Cuál fue la mejor combinación?
# Esto genera un mapa de calor que te dice dónde está el "oro"
pf.total_return().vbt.heatmap().show()