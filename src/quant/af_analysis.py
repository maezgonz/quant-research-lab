import pydantic_core
import pandas as pd
from openbb import obb
import warnings
import urllib3

# ingnorar los warnings
warnings.filterwarnings("ignore")

# Desactivar advertencias de seguridad para sitios .gob.ar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# 1. LISTA DE TICKERS DESDE TU PORTFOLIO REAL
# =====================================================================
# Usamos los tickers de tus acciones locales con el sufijo de Yahoo Finance
TICKERS = ["PAMP.BA", "GGAL.BA", "YPFD.BA", "TGSU2.BA", "TGNO4.BA",
    "EDN.BA", "METR.BA", "BMA.BA", "TRAN.BA", "MOLI.BA", "MORI.BA"]


def barrido_fundamental(ticker_list):
    print(f"🚀Iniciando barrido fundamental para {len(ticker_list)} empresas...")

    resultados = []

    for ticker in ticker_list:
        try:
            # Obtenemos métricas clave de Yahoo Finance a través de OpenBB
            # Nota: Puedes cambiar provider="yfinance" por "fmp" si tienes API Key
            data = obb.equity.fundamental.metrics(symbol=ticker, provider="yfinance").to_df()

            # Seleccionamos solo la última fila (datos más recientes)
            latest = data.iloc[-1:].copy()
            latest['ticker'] = ticker
            resultados.append(latest)
            print(f"✅ Datos obtenidos para {ticker}")
        except Exception as e:
            print(f"⚠️ Error en {ticker}: {e}")

    # Consolidamos todo en un solo DataFrame
    if resultados:
        df_final = pd.concat(resultados, ignore_index=True)
        # Reordenamos para que el ticker esté al principio
        cols = ['ticker'] + [c for c in df_final.columns if c != 'ticker']
        return df_final[cols]
    return pd.DataFrame()


# =====================================================================
# 2. EJECUCIÓN Y EXPORTACIÓN
# =====================================================================
if __name__ == "__main__":
    # Realizamos el barrido
    df_barrido = barrido_fundamental(TICKERS)

    if not df_barrido.empty:
        # Filtramos las columnas más importantes para tu auditoría
        columnas_interes = [
            'ticker', 'market_cap', 'pe_ratio', 'price_to_book',
            'return_on_equity', 'dividend_yield', 'debt_to_equity'
        ]

        # Verificamos qué columnas están disponibles y mostramos
        cols_presentes = [c for c in columnas_interes if c in df_barrido.columns]
        summary = df_barrido[cols_presentes]

        print("\n📊 RESUMEN FUNDAMENTAL DE TU CARTERA:")
        print("-" * 80)
        print(summary.to_string(index=False))

        # Exportamos a Excel para que lo abras en tu Ryzen 9
        summary.to_excel("Barrido_Fundamental_Mati.xlsx", index=False)
        print(f"\n✅ Archivo 'Barrido_Fundamental_Mati.xlsx' generado con éxito.")