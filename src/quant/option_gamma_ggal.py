import numpy as np
from scipy.stats import norm
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Parámetros base
S = 6200
K = 6945
T = 45 / 365
r = 0.25
sigma = 0.439
C0 = 180


# Cálculo de d1, delta, gamma
d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
delta = norm.cdf(d1)
gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

# Mostrar valores clave
print(f"d1 = {d1:.4f}")
print(f"Delta = {delta:.4f}")
print(f"Gamma = {gamma:.8f}")

# Variaciones de S (desde -10% a +10%)
porcentajes = np.arange(-0.10, 0.11, 0.01)
nuevos_precios = S * (1 + porcentajes)

# Tabla de sensibilidad
variaciones = []

for pct, new_S in zip(porcentajes, nuevos_precios):
    dS = new_S - S
    precio_estimado = C0 + delta * dS + 0.5 * gamma * dS**2

    # Variación % correctamente medida contra 174
    var_pct_opcion = ((precio_estimado - C0) / C0) * 100

    variaciones.append({
        "Variación suby (%)": f"{pct*100:.0f}%",
        "S": round(new_S, 2),
        "ΔS": round(dS, 2),
        "Precio estimado": round(precio_estimado, 2),
        "Var % precio opción": f"{var_pct_opcion:.2f}%"
    })


tabla = pd.DataFrame(variaciones)
print(tabla.to_string(index=False))

# === Gráfico de variación porcentual del precio estimado ===
plt.style.use('dark_background')
plt.figure(figsize=(10, 5))
x_vals = porcentajes * 100
y_vals = [((C0 + delta * (S * p) + 0.5 * gamma * (S * p)**2) - C0) / C0 * 100 for p in porcentajes]
plt.plot(x_vals, y_vals, marker='o', color='blue')
plt.axhline(0, color='gray', linestyle='--')
plt.title("Variación % del precio estimado vs cambio % en subyacente")
plt.xlabel("Variación del subyacente (%)")
plt.ylabel("Variación del precio de la opción (%)")
plt.grid(True)
plt.show()



# Rango de S y sigma para graficar Gamma
S_range = np.linspace(S * 0.7, S * 1.3, 50)
sigma_range = np.linspace(0.2, 0.8, 50)

S_grid, sigma_grid = np.meshgrid(S_range, sigma_range)

# Gamma para cada punto en la grilla
d1_grid = (np.log(S_grid / K) + (r + 0.5 * sigma_grid**2) * T) / (sigma_grid * np.sqrt(T))
gamma_grid = norm.pdf(d1_grid) / (S_grid * sigma_grid * np.sqrt(T))

# Gráfico 3D
fig = plt.figure(figsize=(20, 10))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(S_grid, sigma_grid, gamma_grid, cmap='viridis')

ax.set_title("Gamma vs Subyacente (S) y Volatilidad (σ)")
ax.set_xlabel("Precio del subyacente (S)")
ax.set_ylabel("Volatilidad (σ)")
ax.set_zlabel("Gamma")
plt.tight_layout()
plt.show()