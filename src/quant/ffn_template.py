import ffn
import matplotlib.pyplot as plt

# Configurar tema oscuro
plt.style.use('dark_background')  # Cambiar a tema oscuro
plt.rcParams.update({
    'axes.facecolor': '#121212',  # Fondo de los ejes
    'figure.facecolor': '#121212',  # Fondo de la figura
    'axes.edgecolor': '#FFFFFF',  # Color de los bordes de los ejes
    'axes.labelcolor': '#FFFFFF',  # Color de las etiquetas de los ejes
    'xtick.color': '#FFFFFF',  # Color de las etiquetas del eje X
    'ytick.color': '#FFFFFF',  # Color de las etiquetas del eje Y
    'grid.color': '#444444',  # Color de la cuadrícula
    'text.color': '#FFFFFF',  # Color del texto
    'legend.frameon': True,  # Fondo de la leyenda
    'legend.framealpha': 0.3,  # Transparencia de la leyenda
    'legend.facecolor': '#121212',  # Fondo de la leyenda
    'legend.edgecolor': '#FFFFFF'  # Bordes de la leyenda
})

# Descargar datos históricos de los activos
data = ffn.get('ggal', start='2010-01-01', end='2025-04-29')

# Mostrar los primeros datos descargados
print("Datos históricos (primeros 5 registros):")
print(data.head())

# Calcular estadísticas clave
stats = data.calc_stats()

# Mostrar estadísticas en la terminal
print("\nEstadísticas calculadas:")
print(stats.display())

# Crear gráficos para mejorar el análisis
# 1. Gráfico de precios históricos
plt.figure(figsize=(10, 6))
data.plot(title="Precio Histórico", legend=True)
plt.xlabel("Fecha")
plt.ylabel("Precio")
plt.grid(alpha=0.5)  # Transparencia de la cuadrícula
plt.show()

# 2. Gráfico de retornos acumulados
plt.figure(figsize=(10, 6))
stats.plot(title="Retornos Acumulados")
plt.xlabel("Fecha")
plt.ylabel("Retorno Acumulado")
plt.grid(alpha=0.5)
plt.show()

# 3. Gráfico de drawdown
plt.figure(figsize=(10, 6))
drawdown = data.to_drawdown_series()  # Calcular la serie de drawdowns
drawdown.plot(title="Drawdown de Activos", legend=True)
plt.xlabel("Fecha")
plt.ylabel("Drawdown")
plt.grid(alpha=0.5)
plt.show()

# 4. Gráfico de distribución de retornos
plt.figure(figsize=(10, 6))
data.to_returns().dropna().hist(bins=50, alpha=0.75, figsize=(10, 6), color='#1f77b4')
plt.title("Distribución de Retornos Diarios")
plt.xlabel("Retorno Diario")
plt.ylabel("Frecuencia")
plt.grid(alpha=0.5)
plt.show()
