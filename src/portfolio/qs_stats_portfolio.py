import quantstats as qs
import pandas as pd

# 1. Configuración de la Cartera y Fechas
tickers = ['GGAL.BA', 'PAMP.BA', 'YPF.BA', 'EDN.BA', 'BMA.BA', 'METR.BA']
pesos = [0.166, 0.166, 0.166, 0.166, 0.166, 0.170]
fecha_inicio = "2023-10-01"
fecha_fin = "2026-03-12"  # Fecha actual

# 2. Descarga de Datos (Activos + Benchmark Merval)
data = qs.utils.download_returns(tickers + ['^MERV'])

# 3. Aplicación de Filtro de Fechas
data_filtrada = data.loc[fecha_inicio : fecha_fin]

# 4. Construcción de la Estrategia (Elite-6)
# Multiplicamos retornos por pesos y restamos el 0.05% de arancel BYMA
estrategia_rets = (data_filtrada[tickers] * pesos).sum(axis=1) - 0.0005
merval_rets = data_filtrada['^MERV']

# 5. Generación del Reporte QuantStats
qs.extend_pandas()

# Creamos el reporte HTML 'Full' comparativo
qs.reports.html(estrategia_rets, benchmark=merval_rets, title= 'Porfolio Performance | ({fecha_inicio} - {fecha_fin})')