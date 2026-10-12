# Importacion de Librerias & Dependencias

import os
import seaborn as sns
from sklearn.mixture import GaussianMixture as mix
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, r2_score
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import mutual_info_classif
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from scipy.stats import norm
import ta

def add_lagged_price_features(df):
    """
    Añade al DataFrame las columnas 'high', 'low', y 'close' con los valores rezagados de 'High', 'Low', y 'Close'.
    """
    df['high_lag_1'] = df['High'].shift(1)
    df['low_lag_1'] = df['Low'].shift(1)
    df['close_lag_1'] = df['Close'].shift(1)
    df['high_lag_2'] = df['High'].shift(2)
    df['low_lag_2'] = df['Low'].shift(2)
    df['close_lag_2'] = df['Close'].shift(2)
    df['high_lag_3'] = df['High'].shift(3)
    df['low_lag_3'] = df['Low'].shift(3)
    df['close_lag_3'] = df['Close'].shift(3)
    df['high_lag_4'] = df['High'].shift(4)
    df['low_lag_4'] = df['Low'].shift(4)
    df['close_lag_4'] = df['Close'].shift(4)
    df['high_lag_5'] = df['High'].shift(5)
    df['low_lag_5'] = df['Low'].shift(5)
    df['close_lag_5'] = df['Close'].shift(5)
    return df


# Definiciones de funciones para calcular indicadores técnicos
def calculate_RSI(series, period=7):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    RS = gain / loss
    RSI = 100 - (100 / (1 + RS))
    return RSI

def calculate_ROC(series, period=5):
    return ((series - series.shift(period)) / series.shift(period)) * 100

def calculate_PPO(series, fast_period=5, slow_period=9, signal_period=5):
    ema_fast = series.ewm(span=fast_period, adjust=False).mean()
    ema_slow = series.ewm(span=slow_period, adjust=False).mean()
    ppo = (ema_fast - ema_slow) / ema_slow * 100
    signal_line = ppo.ewm(span=signal_period, adjust=False).mean()
    histogram = ppo - signal_line
    return ppo, signal_line, histogram

def calculate_volatility(series, window=20):
    return series.rolling(window).std()

def calculate_sma(series, period=5):
    # Calcular la media móvil simple (SMA) con el período dado para la serie dada
    return series.rolling(window=period).mean()

def calculate_sma21(series, period=21):
    # Calcular la media móvil simple (SMA) con el período dado para la serie dada
    return series.rolling(window=period).mean()

def calculate_sma30(series, period=7):
    # Calcular la media móvil simple (SMA) con el período dado para la serie dada
    return series.rolling(window=period).mean()

def calculate_christmas_rally(df):
    # Crear una columna para indicar si es noviembre o diciembre
    df['Is_November_December'] = df.index.month.isin([11, 12])
    # Crear una columna para indicar si es el rally navideño (desde noviembre hasta diciembre)
    df['Is_Christmas_Rally'] = df['Is_November_December']
    return df



# Función para calcular la época de balances
def calculate_earnings_season(df):

    df['Is_Earnings_Season'] = df.index.month.isin([1, 4, 7, 10])
    return df# Por ejemplo, podrías considerar los meses en los que la mayoría de las empresas reportan sus resultados trimestrales


# Función para obtener datos y crear características
def fetch_data(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date)
    return data

# Función para obtener datos y crear features
def create_features(df):
    # Añadir características rezagadas
    df = add_lagged_price_features(df)

    # Calcular el cambio porcentual y agregar características retrasadas basadas en ello
    df['Pct_change'] = df['Close'].pct_change()
    for lag in range(1, 6):
        df[f'lag_{lag}'] = df['Pct_change'].shift(lag)

    # Calcular los indicadores técnicos
    df['RSI'] = calculate_RSI(df['Close'])
    df['ROC'] = calculate_ROC(df['Close'])
    df['PPO'], df['PPO_Signal'], df['PPO_Histogram'] = calculate_PPO(df['Close'])


    # Calcular la media móvil simple y la volatilidad
    df["SMA"] = calculate_sma(df["Close"])
    df["SMA21"] = calculate_sma21(df["Close"])
    df["SMA30"] = calculate_sma30(df["Close"])

    df['Volatility'] = calculate_volatility(df['Close'])

    # Etiquetar los datos como subida o bajada (1 si es subida, 0 si es bajada)
    df['Label'] = (df['Pct_change'] > 0).astype(int)

    # Calcular el retorno
    df['Return'] = np.log(df['Close'] / df['Close'].shift())

    # Agregar características de la temporada de ganancias y el rally de Navidad
    df = calculate_earnings_season(df)
    df = calculate_christmas_rally(df)

    # Eliminar filas con valores faltantes resultantes de los cálculos anteriores
    df.dropna(inplace=True)

    return df


# Definición de símbolo y fechas
symbol ="GGAL.BA"
start_date ="2001-01-01"
end_date_today="2025-07-14"
current_data = fetch_data(symbol, end_date_today, end_date_today)

# Obtener datos
df = fetch_data(symbol, start_date, end_date_today)

# Crear features
df = create_features(df)
print(df)

# Ordenar features y etiquetes
X = df[['RSI', 'ROC', 'PPO', 'PPO_Signal', 'PPO_Histogram', 'Volatility', 'SMA', "SMA21", "SMA30", 'Is_Christmas_Rally', 'Is_Earnings_Season'] + [f'lag_{i}' for i in range(1, 6)]]
y = df['Label']

# Calcular la información mutua entre las características X y la etiqueta y
mutual_info = mutual_info_classif(X, y)

# Mostrar la información mutua p cada característica
for feature, mi in zip(X.columns, mutual_info):
    print(f"Mutual Information for {feature}: {mi}")

# Definir el punto de división para el entrenamiento y la predicción
split = int(0.8*len(df))

# Preparar los datos excluyendo las columnas 'High', 'Low', 'Close'
df_features = df.drop(['High', 'Low', 'Open'], axis=1)


# Escalar los datos
scaler = StandardScaler()
ss = scaler
data_scaled = ss.fit_transform(df_features[:split])

# Escalar las características
X_scaled = scaler.fit_transform(X)

# Dividir los datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Definir el clasificador XGBoost con parámetros personalizados
xgb_clf = XGBClassifier(
    learning_rate=0.1,  # Tasa de aprendizaje (por defecto es 0.1)
    max_depth=3,        # Profundidad máxima del árbol (por defecto es 3)
    n_estimators=900,
    objective='binary:logistic',
    subsample = 0.6
         # Número de árboles (por defecto es 100)

)

# Realizar validación cruzada
cv_scores = cross_val_score(xgb_clf, X_scaled, y, cv=5)

# Imprimir los puntajes de validación cruzada
print("CV Scores:", cv_scores)
print("Mean CV Score:", np.mean(cv_scores))
print("Std CV Score:", np.std(cv_scores))

# Entrenar el modelo XGBoost en el conjunto de entrenamiento
xgb_clf.fit(X_train, y_train)

# Calcular las predicciones en el conjunto de entrenamiento y prueba
y_train_pred_xgb = xgb_clf.predict(X_train)
y_test_pred_xgb = xgb_clf.predict(X_test)

# Predicciones de probabilidades en el conjunto de entrenamiento y prueba
y_train_prob_xgb = xgb_clf.predict_proba(X_train)
y_test_prob_xgb = xgb_clf.predict_proba(X_test)

sns.kdeplot(y_train_prob_xgb[:,1])

# Umbral para clasificar como 1
threshold = 0.5

# Recodificar las probabilidades en valores binarios
y_train_pred_bin_xgb = (y_train_prob_xgb[:, 1] > threshold).astype(int)
y_test_pred_bin_xgb = (y_test_prob_xgb[:, 1] > threshold).astype(int)

# Mostrar los primeros diez elementos resultantes
print("Predicciones binarias en el conjunto de entrenamiento (XGBoost):", y_train_pred_bin_xgb[:10])
print("Predicciones binarias en el conjunto de prueba (XGBoost):", y_test_pred_bin_xgb[:10])

# Imprimir las probabilidades
print("Probabilidades en el conjunto de entrenamiento (XGBoost):\n", y_train_prob_xgb)
print("Probabilidades en el conjunto de prueba (XGBoost):\n", y_test_prob_xgb)

# Calcular el R cuadrado en el conjunto de entrenamiento y de prueba
r2_train_xgb = xgb_clf.score(X_train, y_train)
r2_test_xgb = xgb_clf.score(X_test, y_test)

print("R cuadrado en el conjunto de entrenamiento (XGBoost):", r2_train_xgb)
print("R cuadrado en el conjunto de prueba (XGBoost):", r2_test_xgb)


def evaluacion_modelo(modelo, X_train, y_train, X_test, y_test):
    # Predicciones en el conjunto de entrenamiento y prueba
    y_train_pred = modelo.predict(X_train)
    y_test_pred = modelo.predict(X_test)

    # Calcular las métricas para el conjunto de entrenamiento
    print("Métricas para el conjunto de entrenamiento:")
    print("------------------------------------------------------")
    print("Matriz de Confusión:")
    print(confusion_matrix(y_train, y_train_pred))

    print("Precisión (Accuracy):", accuracy_score(y_train, y_train_pred))
    print("Informe de Clasificación:")
    print(classification_report(y_train, y_train_pred))

    # Calcular las métricas para el conjunto de prueba
    print("\nMétricas para el conjunto de prueba:")
    print("------------------------------------------------------")
    print("Matriz de Confusión:")
    print(confusion_matrix(y_test, y_test_pred))

    print("Precisión (Accuracy):", accuracy_score(y_test, y_test_pred))
    print("Informe de Clasificación:")
    print(classification_report(y_test, y_test_pred))

# Uso de la función evaluacion_modelo
print("Evaluación del modelo en el conjunto de entrenamiento y prueba:")
print("------------------------------------------------------")
evaluacion_modelo(xgb_clf, X_train, y_train, X_test, y_test)


############################# PREDICCIONES #############################

# Obtener las características para el último día disponible
current_data = df.iloc[-1:]
latest_features = current_data[['RSI', 'ROC', 'PPO', 'PPO_Signal', 'PPO_Histogram', 'Volatility', 'SMA', "SMA21", "SMA30", 'Is_Christmas_Rally', 'Is_Earnings_Season'] + [f'lag_{i}' for i in range(1, 6)]]
latest_features_scaled = scaler.transform(latest_features)

# Predecir la probabilidad de que el precio suba o baje en el siguiente día
predicted_prob = xgb_clf.predict_proba(latest_features_scaled)

# Determinar si el modelo predice una subida o bajada del precio basado en el umbral
predicted_direction = 1 if predicted_prob[0][1] > threshold else -1

# Precio actual
current_price = current_data['Close'].values[0]

# Definir el número de días en el futuro para predecir el precio
n_days_future = 1  # Puedes ajustar este valor según tus necesidades


from scipy.stats import norm

# Definir el tamaño de la ventana para ajustar la distribución gaussiana
window_size = 300

# Obtener los precios de cierre históricos de la ventana de tiempo seleccionada
historical_prices_window = df['Close'][-window_size:]

# Calcular la diferencia de precios entre días consecutivos
price_diff = historical_prices_window.diff().dropna()

# Calcular la media y la desviación estándar de las diferencias de precios
mu_diff = np.mean(price_diff)
sigma_diff = np.std(price_diff)

# Generar una muestra aleatoria de la distribución gaussiana de las diferencias de precios
future_price_diff_gaussian = np.random.normal(mu_diff, sigma_diff)

# Calcular el precio esperado para el siguiente día basado en la diferencia de precios predicha por la distribución gaussiana
future_price = current_price + future_price_diff_gaussian

# Calcular la probabilidad de que el precio predicho sea correcto
probability_predicted_price = 1 - norm.cdf((future_price - current_price) / sigma_diff)

# Graficar la distribución de las diferencias de precios históricas y la muestra aleatoria
plt.figure(figsize=(10, 6))
plt.hist(price_diff, bins=20, density=True, alpha=0.6, color='g', label='Distribución de diferencias de precios históricas')
plt.hist(future_price_diff_gaussian, bins=20, density=True, alpha=0.6, color='b', label='Muestra aleatoria de distribución gaussiana')
plt.axvline(x=future_price_diff_gaussian, color='r', linestyle='--', label='Precio predicho para el siguiente día')
plt.xlabel('Diferencia de precios')
plt.ylabel('Densidad de probabilidad')
plt.title('Distribución de diferencias de precios y predicción para el siguiente día')
plt.legend()
plt.show()

# Imprimir el precio esperado para el siguiente día y la probabilidad correspondiente
print("Precio esperado para el siguiente día (distribución gaussiana con derivadas):", future_price)
print("Probabilidad de que el precio predicho sea correcto:", probability_predicted_price)
print(f"Precio actual: {current_price}")
print(f"Pronóstico de dirección del activo (1: subida, -1: bajada): {predicted_direction}")

# Calcular el área bajo la Curva ROC (ROC-AUC) en el conjunto de entrenamiento y de prueba
roc_auc_train = roc_auc_score(y_train, y_train_prob_xgb[:, 1])
roc_auc_test = roc_auc_score(y_test, y_test_prob_xgb[:, 1])

print("ROC-AUC en el conjunto de entrenamiento:", roc_auc_train)
print("ROC-AUC en el conjunto de prueba:", roc_auc_test)

# Calcular la Curva ROC en el conjunto de entrenamiento y prueba
fpr_train, tpr_train, _ = roc_curve(y_train, y_train_prob_xgb[:, 1])
fpr_test, tpr_test, _ = roc_curve(y_test, y_test_prob_xgb[:, 1])


############################# STRATEGY ##################################

# Estrategia de Trading basada en predicciones del modelo XGBoost
def trading_strategy(model, threshold, X_features, current_price, previous_signal):
    # Predecir la probabilidad de que el precio suba o baje
    predicted_prob = model.predict_proba(X_features)

    # Determinar si la probabilidad supera el umbral
    predicted_direction = 1 if predicted_prob[0][1] > threshold else (-1 if predicted_prob[0][0] > threshold else 0)

    # Definir la acción sugerida por la estrategia de trading
    if predicted_direction == 1 and previous_signal != 'SELL':
        # Comprar acciones si se predice una subida del precio y no se tiene una posición de venta abierta
        action = 'BUY'
    elif predicted_direction == -1 and previous_signal == 'BUY':
        # Cerrar posición si se predice una bajada del precio y se tiene una posición de compra abierta
        action = 'SELL'
    else:
        # No hacer nada en otros casos
        action = previous_signal

    return action

# Aplicar la estrategia de trading
action = trading_strategy(xgb_clf, threshold, latest_features_scaled, current_data['Close'].values[0], previous_signal='BUY')  # Suponiendo una posición comprada inicialmente

# Imprimir la acción sugerida por la estrategia de trading
print("Acción sugerida por la estrategia de trading:", action)

plt.figure(figsize=(10, 6))
plt.plot(fpr_train, tpr_train, label=f'Train ROC (AUC = {roc_auc_train:.2f})', color='blue')
plt.plot(fpr_test, tpr_test, label=f'Test ROC (AUC = {roc_auc_test:.2f})', color='green')
plt.plot([0, 1], [0, 1], linestyle='--', color='gray')  # Línea diagonal (clasificación aleatoria)
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Curva ROC - XGBoost')
plt.legend(loc='lower right')
plt.grid(True)
plt.tight_layout()
plt.show()

def create_advanced_labels(df, threshold=0.02):
    # Retornos futuros
    df['future_returns'] = df['Close'].shift(-1) / df['Close'] - 1
    
    # Labels más sofisticados (1: strong buy, 0.5: buy, 0: neutral, -0.5: sell, -1: strong sell)
    df['Label'] = pd.cut(df['future_returns'], 
                        bins=[-np.inf, -threshold, -threshold/2, threshold/2, threshold, np.inf],
                        labels=[-1, -0.5, 0, 0.5, 1])

def calculate_position_size(prediction_probability, max_position=1.0):
    """
    Ajusta el tamaño de la posición según la confianza de la predicción
    """
    confidence = abs(prediction_probability - 0.5) * 2  # Normaliza entre 0 y 1
    position_size = max_position * confidence
    return position_size

def add_stop_loss(entry_price, direction, stop_percentage=0.02):
    """
    Calcula stop loss
    """
    if direction == 'BUY':
        stop_loss = entry_price * (1 - stop_percentage)
    else:
        stop_loss = entry_price * (1 + stop_percentage)
    return stop_loss

def backtest_strategy(df, predictions, initial_capital=100000):
    portfolio = pd.DataFrame(index=df.index)
    portfolio['holdings'] = 0
    portfolio['cash'] = initial_capital
    portfolio['position'] = 0
    
    for i in range(len(df)):
        if predictions[i] > 0.5:  # Señal de compra
            # Implementar lógica de entrada
            shares = calculate_position_size(predictions[i])
            portfolio.loc[df.index[i], 'position'] = shares
            
        # Agregar costos de transacción
        portfolio['transaction_costs'] = portfolio['position'].diff().abs() * 0.001
        
    return portfolio

def validate_model(model, X, y):
    tscv = TimeSeriesSplit(n_splits=5)
    scores = []
    
    for train_index, test_index in tscv.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        scores.append(score)