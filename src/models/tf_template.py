import yfinance
import pandas_ta  #noqa

# Cambiamos a un ticker válido
TICKER = 'GGAL'  # Cambiado de 'ITRD' a un ticker válido y activo
TRAIN_START_DATE = '2024-02-09'  # Fechas más recientes para asegurar datos
TRAIN_END_DATE = '2024-09-30'
EVAL_START_DATE = '2024-10-01'
EVAL_END_DATE = '2024-11-12'

def procesar_datos(df):
    """Función auxiliar para procesar el DataFrame"""
    if df.empty:
        raise ValueError("No hay datos disponibles para el período especificado")
    
    # Eliminar columnas solo si existen
    for columna in ['Dividends', 'Stock Splits']:
        if columna in df.columns:
            df.drop(columna, axis=1, inplace=True)
    
    df["Volume"] = df["Volume"].astype(int)
    df.ta.log_return(append=True, length=16)
    df.ta.rsi(append=True, length=14)
    df.ta.macd(append=True, fast=12, slow=26)
    return df

try:
    print(f"Descargando datos para {TICKER}...")
    yf_ticker = yfinance.Ticker(ticker=TICKER)
    
    # Datos de entrenamiento
    print("Procesando datos de entrenamiento...")
    df_training = yf_ticker.history(start=TRAIN_START_DATE, end=TRAIN_END_DATE, interval='60m')
    df_training = procesar_datos(df_training)
    df_training.to_csv('training.csv', index=False)
    print(f"✓ Datos de entrenamiento guardados ({len(df_training)} registros)")
    
    # Datos de evaluación
    print("Procesando datos de evaluación...")
    df_evaluation = yf_ticker.history(start=EVAL_START_DATE, end=EVAL_END_DATE, interval='60m')
    df_evaluation = procesar_datos(df_evaluation)
    df_evaluation.to_csv('evaluation.csv', index=False)
    print(f"✓ Datos de evaluación guardados ({len(df_evaluation)} registros)")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print("\nPor favor, verifica que:")
    print("1. El ticker sea válido (ejemplo: 'AAPL', 'MSFT', 'GOOGL')")
    print("2. Las fechas estén en el formato correcto (YYYY-MM-DD)")
    print("3. Haya datos disponibles para el período seleccionado")
    print("4. Tengas conexión a internet")