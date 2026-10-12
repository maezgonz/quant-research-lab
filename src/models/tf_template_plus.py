import yfinance
import pandas_ta  #noqa
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os

# Calculamos fechas automáticamente para estar dentro del rango permitido
end_date = datetime.now()
start_date = end_date - timedelta(days=300)  # Tomamos 300 días para estar seguros
eval_split = end_date - timedelta(days=60)   # Últimos 60 días para evaluación

TICKER = 'AAPL'
TRAIN_START_DATE = start_date.strftime('%Y-%m-%d')
TRAIN_END_DATE = eval_split.strftime('%Y-%m-%d')
EVAL_START_DATE = eval_split.strftime('%Y-%m-%d')
EVAL_END_DATE = end_date.strftime('%Y-%m-%d')

print(f"Períodos de análisis:")
print(f"Entrenamiento: {TRAIN_START_DATE} hasta {TRAIN_END_DATE}")
print(f"Evaluación: {EVAL_START_DATE} hasta {EVAL_END_DATE}")

yf_ticker = yfinance.Ticker(ticker=TICKER)

try:
    df_training = yf_ticker.history(start=TRAIN_START_DATE, end=TRAIN_END_DATE, interval='60m')
    
    if df_training.empty:
        raise ValueError(f"No se encontraron datos para {TICKER} en el período especificado")
    
    # Eliminar columnas solo si existen
    columns_to_drop = ['Dividends', 'Stock Splits']
    existing_columns = [col for col in columns_to_drop if col in df_training.columns]
    if existing_columns:
        df_training.drop(existing_columns, axis=1, inplace=True)
    
    df_training["Volume"] = df_training["Volume"].astype(int)
    df_training.ta.log_return(append=True, length=16)
    df_training.ta.rsi(append=True, length=14)
    df_training.ta.macd(append=True, fast=12, slow=26)
    df_training.to_csv('training.csv', index=False)
    print(f"Datos de entrenamiento guardados: {len(df_training)} registros")

    # Datos de evaluación
    df_evaluation = yf_ticker.history(start=EVAL_START_DATE, end=EVAL_END_DATE, interval='60m')
    
    if df_evaluation.empty:
        raise ValueError(f"No se encontraron datos para {TICKER} en el período de evaluación")
    
    if existing_columns:
        df_evaluation.drop(existing_columns, axis=1, inplace=True)
    
    df_evaluation["Volume"] = df_evaluation["Volume"].astype(int)
    df_evaluation.ta.log_return(append=True, length=16)
    df_evaluation.ta.rsi(append=True, length=14)
    df_evaluation.ta.macd(append=True, fast=12, slow=26)
    df_evaluation.to_csv('evaluation.csv', index=False)
    print(f"Datos de evaluación guardados: {len(df_evaluation)} registros")

    # Crear directorio para gráficos si no existe
    if not os.path.exists('graficos'):
        os.makedirs('graficos')

    # Gráfico de Precios y Volumen
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        subplot_titles=('Precio de Cierre', 'Volumen'),
                        row_heights=[0.7, 0.3])

    fig.add_trace(go.Candlestick(x=df_training.index,
                                open=df_training['Open'],
                                high=df_training['High'],
                                low=df_training['Low'],
                                close=df_training['Close'],
                                name='OHLC'),
                                row=1, col=1)

    fig.add_trace(go.Bar(x=df_training.index, 
                        y=df_training['Volume'],
                        name='Volumen'),
                        row=2, col=1)

    # Añadir indicadores técnicos
    fig.add_trace(go.Scatter(x=df_training.index, 
                            y=df_training['RSI_14'],
                            name='RSI'),
                            row=1, col=1)

    fig.add_trace(go.Scatter(x=df_training.index,
                            y=df_training['MACD_12_26_9'],
                            name='MACD'),
                            row=1, col=1)

    # Personalizar el diseño
    fig.update_layout(
        title=f'Análisis Técnico de {TICKER}',
        yaxis_title='Precio',
        yaxis2_title='Volumen',
        xaxis_rangeslider_visible=False,
        height=800
    )

    # Guardar el gráfico
    fig.write_html(f'graficos/{TICKER}_analisis_tecnico.html')
    print(f"Gráfico guardado en: graficos/{TICKER}_analisis_tecnico.html")

    # Crear gráfico de correlación entre indicadores
    correlation_matrix = df_training[['Close', 'Volume', 'RSI_14', 'MACD_12_26_9']].corr()
    
    fig_corr = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.columns,
        colorscale='RdBu',
        zmin=-1,
        zmax=1
    ))

    fig_corr.update_layout(
        title='Matriz de Correlación de Indicadores',
        height=600,
        width=600
    )

    fig_corr.write_html('graficos/correlacion_indicadores.html')
    print("Matriz de correlación guardada en: graficos/correlacion_indicadores.html")

except Exception as e:
    print(f"Error: {str(e)}")
    print("\nPor favor, verifica que:")
    print("1. El ticker sea válido")
    print("2. Las fechas estén en el rango permitido")
    print("3. Haya conexión a internet")