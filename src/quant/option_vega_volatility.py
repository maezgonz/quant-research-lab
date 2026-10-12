import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib.pyplot as plt

# Inputs
S = 6220            # Precio spot
K = 6945            # Strike
r = 0.25            # Tasa libre de riesgo
T = 48 / 365        # Tiempo a vencimiento en años
precio_real = 244   # Precio real de la opción
vol_base = 0.4555  # Volatilidad base

# Volatilidades en bucle
vols = np.arange(0.30, 0.60 + 0.01, 0.01)


# Calcular Vega y Vomma en la base
d1_base = (np.log(S / K) + (r + 0.5 * vol_base ** 2) * T) / (vol_base * np.sqrt(T))
d2_base = d1_base - vol_base * np.sqrt(T)
vega_base = S * norm.pdf(d1_base) * np.sqrt(T)
vomma_base = vega_base * d1_base * d2_base / vol_base

print(f"Vega base: {vega_base:.2f}")
print(f"Vomma base: {vomma_base:.2f}")

# resultados
rows = []
for sigma in vols:
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T

    # Precio exacto Black-Scholes
    bs_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    # Recalcular Vega y Vomma en cada punto (locales)
    vega = S * norm.pdf(d1) * sqrt_T
    vomma = vega * d1 * d2 / sigma

    # Estimaciones
    delta_sigma = sigma - vol_base
    vega_est = precio_real + vega_base * delta_sigma
    vomma_est = precio_real + vega_base * delta_sigma + 0.5 * vomma_base * delta_sigma**2
    vega_local_est = precio_real + vega * delta_sigma

    rows.append({
        "Volatilidad": sigma,
        "BS_Price": round(bs_price, 2),
        "Vega_Estimado": round(vega_est, 2),
        "Vomma_Estimado": round(vomma_est, 2),
        "Vega_Local_Estimado": round(vega_local_est, 2),
        "Error_Vega": round(bs_price - vega_est, 2),
        "Error_Vomma": round(bs_price - vomma_est, 2),
        "Error_VegaLocal": round(bs_price - vega_local_est, 2)
    })

df = pd.DataFrame(rows)
print(df)


plt.figure(figsize=(12, 7))
plt.plot(df["Volatilidad"], df["BS_Price"], label="Black-Scholes (real)", linewidth=2)
plt.plot(df["Volatilidad"], df["Vega_Estimado"], '--', label="Estimado con Vega base")
plt.plot(df["Volatilidad"], df["Vomma_Estimado"], '--', label="Estimado con Vega + Vomma base")
plt.plot(df["Volatilidad"], df["Vega_Local_Estimado"], '--', label="Estimado con Vega local")
plt.axvline(x=vol_base, color='gray', linestyle=':', label=f"Vol base = {vol_base:.4f}")
plt.xlabel("Volatilidad Implícita")
plt.ylabel("Precio de la Opción")
plt.title("Comparación de precios estimados vs Black-Scholes")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()