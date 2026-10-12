#%matplotlib inline
import quantstats as qs
import warnings
import urllib3
warnings.filterwarnings("ignore")

# Desactivar advertencias de seguridad para sitios .gob.ar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# extend pandas functionality with metrics, etc.
qs.extend_pandas()

# fetch the daily returns for a stock
stock = qs.utils.download_returns('GGAL.BA')
benchmark = qs.utils.download_returns('^MERV')

# show sharpe ratio
qs.stats.sharpe(stock)

# or using extend_pandas() :)
stock.sharpe()

# Snapshot rápido
# qs.plots.snapshot(stock, title='GGAL Performance', show=True)
# qs.plots.snapshot(stock, title='GGAL vs SPY - Performance', show=True)
qs.plots.snapshot(stock, title='GGAL vs Merval - Performance', show=True)

# reports basic - shows basic metrics and plots
qs.reports.basic(stock, mode="full")

# report metrics- shows basic/full metrics
qs.reports.metrics(stock, mode="full")

# reports full- shows full metrics and plots
qs.reports.full(stock, mode="full")

# report plots - shows basic/full plots
qs.reports.plots(stock, title="GGAL Metrics", mode="full")

# report plot html - generates a complete report as html
qs.reports.html(stock, benchmark=benchmark, title= "GGAL Performance Report")

# Generar PDF/HTML
# Esto crea un archivo físico que podés guardar como backup de tus decisiones
# qs.reports.html(stock, benchmark=benchmark, output='Reporte_GGAL.html', title='Reporte GGAL')
# print("\n[OK] Reporte HTML generado: Reporte_GGAL.html")