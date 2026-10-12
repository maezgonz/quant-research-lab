import yfinance as yf
import pandas as pd
import warnings
import urllib3

# ingnorar los warnings
warnings.filterwarnings("ignore")

# Desactivar advertencias de seguridad para sitios .gob.ar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def obtener_datos_financieros(tickers):
    """
    Extrae y calcula datos financieros clave para una lista de empresas dadas por sus símbolos de cotización.
    Los datos incluyen activos, pasivos, capital contable, dividendos, precio de cierre, ratios financieros y otros indicadores.

    :param tickers: Lista de símbolos (ej. ['AAPL', 'GOOGL', 'MSFT']).
    :return: Un DataFrame de pandas con los datos financieros calculados para cada empresa.
    """
    # Lista para almacenar los datos
    data = []

    # Iterar sobre la lista de símbolos bursátiles
    for ticker in tickers:
        try:
            # Obtener el objeto de datos del símbolo
            stock = yf.Ticker(ticker)

            # Extraer balance general trimestral
            balance_sheet = stock.quarterly_balance_sheet
            
            # Extraer los datos con manejo de excepciones si faltan
            activo_corriente = balance_sheet.loc['Current Assets', :].values[0] if 'Current Assets' in balance_sheet.index else None
            pasivo_corriente = balance_sheet.loc['Current Liabilities', :].values[0] if 'Current Liabilities' in balance_sheet.index else None
            deuda_total = balance_sheet.loc['Total Liabilities Net Minority Interest', :].values[0] if 'Total Liabilities Net Minority Interest' in balance_sheet.index else None
            activos_totales = balance_sheet.loc['Total Assets', :].values[0] if 'Total Assets' in balance_sheet.index else None
            
            # Calcular el capital contable
            capital_contable = activos_totales - deuda_total if activos_totales and deuda_total else None
            
            # Extraer dividendos anuales
            dividendos = stock.dividends
            dividendos_anuales = dividendos.groupby(dividendos.index.year).sum().get(2023, 0)
            
            # Obtener el precio de cierre
            historial = stock.history(period='1d')
            precio_de_cierre = historial['Close'].iloc[0] if not historial.empty else None
            
            # Calcular el capital contable promedio si hay suficientes datos
            capital_contable_promedio = None
            if "Total Equity Gross Minority Interest" in stock.quarterly_balance_sheet.index:
                equity = stock.quarterly_balance_sheet.loc["Total Equity Gross Minority Interest"]
                if len(equity) >= 2:
                    capital_contable_promedio = (equity.iloc[0] + equity.iloc[1]) / 2
            
            # Extraer capitalización bursátil y ventas
            capitalizacion_bursatil = stock.info.get('marketCap')
            ventas = stock.info.get('totalRevenue')
            
            # Extraer la utilidad neta
            quarterly_financials = stock.quarterly_financials.T
            utilidad_neta = quarterly_financials.loc[:, "Net Income"].iloc[0] if "Net Income" in quarterly_financials.columns else None
            
            # Obtener las acciones en circulación
            shares_outstanding = stock.info.get('sharesOutstanding')

            # Calcular el EPS (Ganancia por Acción) manualmente
            eps_hist = None
            if utilidad_neta and shares_outstanding:
                eps_hist = utilidad_neta / shares_outstanding

            # Calcular el PER promedio
            try:
                # Descargar datos históricos de precios
                precio_hist = stock.history(period='10y', interval="1mo")['Close'].resample('YE').mean()

                # Calcular el PER anual y su promedio
                per_anual = precio_hist[-10:] / eps_hist
                per_promedio = per_anual.mean()
            except Exception as e:
                per_promedio = None
                print(f"Error al calcular el PER promedio para {ticker}: {e}")

            # Calcular ratios financieros
            razon_circulante = activo_corriente / pasivo_corriente if activo_corriente and pasivo_corriente else None
            deudas_a_activos = deuda_total / activos_totales if deuda_total and activos_totales else None
            deuda_a_capital = deuda_total / capital_contable if deuda_total and capital_contable else None
            rendimiento_dividendos = dividendos_anuales / precio_de_cierre if dividendos_anuales and precio_de_cierre else None
            roe = utilidad_neta / capital_contable_promedio if utilidad_neta and capital_contable_promedio else None
            precio_a_ventas = capitalizacion_bursatil / ventas if capitalizacion_bursatil and ventas else None
            precio_ganancia = capitalizacion_bursatil / utilidad_neta if capitalizacion_bursatil and utilidad_neta else None
            roa = utilidad_neta / activos_totales if utilidad_neta and activos_totales else None
            per = stock.info['trailingPE']
            

            # Añadir los datos al diccionario
            data.append({
                'Ticker': ticker,
                'Activo Corriente': activo_corriente,
                'Pasivo Corriente': pasivo_corriente,
                'Deuda Total': deuda_total,
                'Activos Totales': activos_totales,
                'Capital Contable': capital_contable,
                'Dividendos Anuales': dividendos_anuales,
                'Precio de Cierre': precio_de_cierre,
                'Capital Contable Promedio': capital_contable_promedio,
                'Capitalización Bursátil': capitalizacion_bursatil,
                'Ventas': ventas,
                'Utilidad Neta': utilidad_neta,
                'Razón Circulante': razon_circulante,
                'Deudas a Activos': deudas_a_activos, 
                'Deuda a Capital': deuda_a_capital,
                'Rendimiento de Dividendos': rendimiento_dividendos,
                'ROA': roa,
                'ROE': roe,
                'Precio a Ventas': precio_a_ventas,
                'Precio a Ganancias': precio_ganancia,
                'PER': per,
                'PER prom. x10':per_promedio
            })

        except Exception as e:
            print(f"Error al procesar {ticker}: {e}")

    # Convertir la lista de datos en un DataFrame para retornar
    df = pd.DataFrame(data)
    return df

# Ejemplo de uso
tickers = ["PAMP.BA", "GGAL.BA", "YPFD.BA", "TGSU2.BA", "TGNO4.BA","EDN.BA", "METR.BA", "BMA.BA", "TRAN.BA", "MOLI.BA", "MORI.BA"]
datos_financieros = obtener_datos_financieros(tickers)

# Mostrar columnas seleccionadas del DataFrame resultante
print(datos_financieros[['Ticker','Razón Circulante', 'Deudas a Activos', 'Deuda a Capital', 'Rendimiento de Dividendos', 'ROA', 'ROE', 'Precio a Ventas', 'Precio a Ganancias','Precio de Cierre', 'PER', 'PER prom. x10']])