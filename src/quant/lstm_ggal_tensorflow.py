import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import plotly.graph_objs as go
from sklearn.neighbors import KNeighborsRegressor
from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM
import matplotlib.pyplot as plt
from keras.callbacks import EarlyStopping
import seaborn as sns

##LONG SHORT TERM MEMORY
## =========================================================

# Define stock data retrieval parametrs
start_date = '2005-01-01'
end_date = '2026-01-02'
stock_symbol = 'GGAL'

# Descargar los datos
data = yf.download(stock_symbol, start=start_date, end=end_date)

# Reset index and drop missing values
data.reset_index(inplace=True)
data.dropna(inplace=True)

# Data escalada
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data[['Close']])

# Define la función create_dataset para crear conjuntos de datos de entrenamieto
def create_dataset(data, look_back=500):
    X, Y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:(i + look_back), 0])
        Y.append(data[i + look_back, 0])
    return np.array(X), np.array(Y)



# Prepare training set using all available data
look_back = 500  # Esto se puede ajustar tanto como sea necesario
x_train, y_train = create_dataset(scaled_data, look_back)



## Construcción del modelo

from keras.callbacks import EarlyStopping, ReduceLROnPlateau


def build_model():
    model = Sequential()
    model.add(LSTM(100, activation='relu', input_shape=(x_train.shape[1], 1)))
    model.add(Dropout(0.2))  # Ajustar la tasa de Dropout si es necesario
    model.add(Dense(300, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(50, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(1))

    model.compile(loss='mean_squared_error', optimizer='adam', metrics=["mse", "mae"])
    model.summary()

    # Callbacks
    early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-6)

    # Entrenamiento del modelo
    history = model.fit(
        x_train.reshape((x_train.shape[0], x_train.shape[1], 1)),
        y_train,
        batch_size=16,
        epochs=100,
        verbose=1,
        validation_split=0.2,
        callbacks=[early_stopping, reduce_lr]
    )

    # Graficar la pérdida
    plt.plot(history.history['loss'], label='train_loss')
    plt.plot(history.history['val_loss'], label='val_loss')
    plt.xlabel('Época')
    plt.ylabel('Pérdida')
    plt.title('Pérdida durante el entrenamiento')
    plt.legend()
    plt.show()

    return model

model = build_model()


## ============================================================
## PREPARAMOS LOS INPUTS PARA PREDECIR PRECIOS FUTUROS



## ====================================================
## ====================================================
## ====================================================

# Predecir precios futuros para toda la serie de datos
all_predictions = []
for i in range(len(scaled_data) - look_back):
    window = scaled_data[i:i + look_back]
    prediction = model.predict(np.array([window]))
    all_predictions.append(prediction.flatten())

# Invertir la escala para todas las predicciones
all_predictions = scaler.inverse_transform(all_predictions)

# Crear un DataFrame con las fechas y las predicciones
predicted_dates = data['Date'].iloc[look_back:]
predictions_df = pd.DataFrame(all_predictions, columns=['Predicted_Price'], index=predicted_dates)

print(predictions_df)


## ===========================================

actual_prices = data[['Date', 'Close']].iloc[look_back:]  # Recortar los datos para alinear con las predicciones

# Crear un DataFrame con las fechas y las predicciones
predicted_dates = actual_prices['Date']
predictions_df = pd.DataFrame(all_predictions, columns=['Predicted_Price'], index=predicted_dates)

# Imprimir información de los DataFrames antes de unir
print("Estructura de actual_prices:")
print(actual_prices.info())
print(actual_prices.head())

print("\nEstructura de predictions_df:")
print(predictions_df.info())
print(predictions_df.head())

# Aplanar el MultiIndex de las columnas si es necesario
if isinstance(actual_prices.columns, pd.MultiIndex):
    actual_prices.columns = ['_'.join(col).strip() for col in actual_prices.columns.values]

# Renombrar las columnas para que coincidan con los nombres esperados
actual_prices.rename(columns={'Date_': 'Date', 'Close_GGAL': 'Close'}, inplace=True)

# Asegurarse de que 'Date' esté como índice en ambos DataFrames
if 'Date' in actual_prices.columns:
    actual_prices.set_index('Date', inplace=True)

if 'Date' in predictions_df.columns:
    predictions_df.set_index('Date', inplace=True)

# Verificar los tipos de índices
print("\nÍndice de actual_prices:")
print(actual_prices.index)

print("\nÍndice de predictions_df:")
print(predictions_df.index)

# Realizar la unión de los DataFrames
try:
    comparison_df = actual_prices.join(predictions_df, how='inner')
    print("\nDataFrame comparativo resultante:")
    print(comparison_df.tail())
except Exception as e:
    print("\nError al unir los DataFrames:")
    print(e)





# Calcular el índice de división basado en el entrenamiento y la validación
total_length = len(predictions_df)
train_length = int(total_length * 0.8)  # 80% para entrenamiento
validation_length = total_length - train_length  # 20% para validación

# Datos para entrenamiento y validación
train_data = comparison_df.iloc[:train_length]
validation_data = comparison_df.iloc[train_length:]

# Graficar los resultados con diferentes colores para entrenamiento y validación
plt.figure(figsize=(25, 10))
plt.plot(train_data['Predicted_Price'], label='Precio Predicho - Entrenamiento', color='blue', linewidth=3)
plt.plot(validation_data['Predicted_Price'], label='Precio Predicho - Validación', color='red', linewidth=3)
plt.plot(comparison_df['Close'], label='Precio de cierre', color='green', linestyle='--', linewidth=2)

plt.title('Comparación del Precio de Cierre Real y Predicho con Entrenamiento y Validación')
plt.xlabel('Fecha')
plt.ylabel('Precio de Cierre ($)')
plt.legend()
plt.grid(True)
plt.show()


## ========================================================
## DEFINIR PREDICCIONES PARA LOS PRÓXIMOS n DÍAS


## Función para extender la predicción en el tiempo
def extend_prediction(model, last_window, days=1):
    x_pred = np.array([last_window])
    future_pred_scaled = []
    for _ in range(days):
        future_pred_scaled.append(model.predict(x_pred)[-1][0])
        future_pred_scaled_np = np.array([future_pred_scaled[-1]])  # Convertir a array bidimensional
        future_pred_scaled_np = future_pred_scaled_np.reshape(1, 1, 1)  # Cambiar la forma del array
        x_pred = np.append(x_pred[:, 1:], future_pred_scaled_np, axis=1)
    future_pred_scaled = np.array(future_pred_scaled).reshape(-1, 1)
    future_pred = scaler.inverse_transform(future_pred_scaled)
    return future_pred

# Preparar la entrada para predecir precios futuros
last_window = scaled_data[-look_back:]
future_pred = extend_prediction(model, last_window, days=1)

print("Precios futuros predichos para los próximos días:")
print(future_pred)

# Graficar las predicciones junto a los precios de cierres originales
closing_prices = data['Close'][-len(predictions_df):]
predicted_dates = predictions_df.index
plt.style.use('dark_background')
plt.figure(figsize=(14, 7))
plt.plot(predicted_dates, closing_prices, label='Precio de Cierre', color='blue')
for column in predictions_df.columns:
    plt.plot(predicted_dates, predictions_df[column], label=column, color="red", linestyle='--')
plt.xlabel('Fecha')
plt.ylabel('Precio')
plt.title('LSTM Precio de Cierre y Predicciones')
plt.legend()
plt.show()

# Graficar las últimas 30 predicciones y precios de cierre reales
last_30_predicted = predictions_df.tail(30)
last_30_closing = data['Close'].tail(30)
last_30_dates = last_30_predicted.index

sns.set(style="darkgrid")
plt.figure(figsize=(20, 7))

# Línea del precio de cierre real
plt.plot(last_30_dates, last_30_closing, label='Precio de Cierre', color='blue')

# Línea del precio predicho
plt.plot(last_30_dates, last_30_predicted['Predicted_Price'], label='Precio Predicho', color='red', linestyle='--')

# Agregar punto rojo en la última predicción
ultimo_precio_predicho = last_30_predicted['Predicted_Price'].iloc[-1]
ultima_fecha = last_30_dates[-1]
plt.plot(ultima_fecha, ultimo_precio_predicho, 'ro', markersize=10, label='Última Predicción')

plt.xlabel('Fecha')
plt.ylabel('Precio')
plt.title('Zoom a los últimos 30 días - Precio de Cierre y Predicciones')
plt.legend()
plt.grid(True)
plt.show()


import datetime

# Obtener la fecha del último dato y sumarle un día
fecha_maniana = last_30_dates[-1] + datetime.timedelta(days=1)

# Obtener el precio predicho para mañana (ya lo tenés en `future_pred`)
precio_maniana = future_pred[0][0]  # futuro predicho desescalado

# Graficar las últimas 30 predicciones y precios de cierre reales
plt.style.use('dark_background')
plt.figure(figsize=(20, 15))

# Línea del precio de cierre real
plt.plot(last_30_dates, last_30_closing, label='Precio de Cierre', color='blue')

# Línea del precio predicho (hasta hoy)
plt.plot(last_30_dates, last_30_predicted['Predicted_Price'], label='Precio Predicho', color='red', linestyle='--')

# Punto rojo para la predicción de mañana
plt.plot(fecha_maniana, precio_maniana, 'ro', markersize=10, label='Predicción Mañana')

# Opcional: mostrar el valor sobre el punto
plt.text(fecha_maniana, precio_maniana, f'{precio_maniana:.2f}', color='red', fontsize=12, ha='left', va='bottom')

plt.xlabel('Fecha')
plt.ylabel('Precio')
plt.title('Zoom a los últimos 30 días - Precio de Cierre y Predicciones')
plt.legend()
plt.grid(True)
plt.show()