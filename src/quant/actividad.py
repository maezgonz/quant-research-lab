# 1. Importación de librerías
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# 2. Carga del dataset: descargamos datos de Apple (AAPL)
df = yf.download("AAPL", start="2022-01-01", end="2023-12-31")

# 3. Generación de variable objetivo: ¿sube o baja al día siguiente?
df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)  # 1 = sube, 0 = baja

# 4. Selección de features simples (pueden mejorarse)
df['Return_1d'] = df['Close'].pct_change()
df['MA_5'] = df['Close'].rolling(window=5).mean()
df['MA_10'] = df['Close'].rolling(window=10).mean()
df = df.dropna()

# 5. Separar en variables predictoras y objetivo
X = df[['Return_1d', 'MA_5', 'MA_10']]
y = df['Target']

# 6. División en conjunto de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 7. Entrenamiento del modelo
clf = DecisionTreeClassifier(max_depth=4, random_state=42)
clf.fit(X_train, y_train)

# 8. Predicción y evaluación
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Precisión del modelo: {accuracy:.2f}")

# 9. Visualización del árbol de decisión
plt.figure(figsize=(20, 10))
plot_tree(clf, feature_names=X.columns, class_names=['Baja', 'Sube'], filled=True)
plt.title("Árbol de Decisión - Predicción de Movimiento Diario de AAPL")
plt.show()
