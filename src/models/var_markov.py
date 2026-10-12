# %% [markdown]
# # VAR Markov Engine - Asset Allocation
# %% [markdown]
# Estrategia: Motor_VAR_Markov (Version 1.0)
# 
# Basada en: Modelos de cambio de regimen (Markov Switching) y analisis multivariado (VAR)
# 
# Objetivo: Evaluar si los modelos ayudan a mejorar el rendimiento ajustado por riesgo
# 
# 
# Dinamica:
# 
#     (1) Detectar cambios en los regi­menes del mercado
#     (2) Usar VAR para modelar la evolucion conjunta de activos, buscando entender como el pasado de las variables
#         impacta en el futuro de cada una
#     (3) Identificar regi­menes:
#         Se identifican por media y varianza
#             Bull: Mayor exposicion a RV y baja cobertura (Ej. 40_RF/60_RV) [Media > 0; Varianza baja]
#             Bear: Mayor exposicion a RF y alta cobertura (Ej. 60_RF/40_RV) [Media < 0; Varianza alta]
#     (4) Rebalanceo: Semanal/Mensual
# 
# 
# Ideas:
# 
#     (1) Un modelo de aprendizaje no supervisado seri­a mejor que markov ?
#     (2) Hay que hacer la validacion con walk fw optimization, esto asi no sirve (OJO!!!!!!!)
# 
# 
# Que hay que mejorar en el Markov Switching:
# 
#     (M_1) Regimenes con duracion esperada de 1 dia ---> Modelo inestable y nervioso (+ panqueque que masa)
#     Solucion 1: Darle mejores features/predictores (El precio no sirve loco, era obvio)
#     Solucion 2: Probar con 3 regimenes
#     Solucion 3: Hacer que cambie por varianza (xq acordate que no cambiaba), se puede forzar con switching_variance = True
#     Solucion 4: Cambiar de modelo. Un GMM, KNN o HiddenMM
# %% [markdown]
# Obtener los datos e importar librerias
# %%
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from scipy.stats import ttest_ind

#GET data
symbols = ['^GSPC', 'IEF']
prices = yf.download(symbols, start='2010-01-01', end='2025-12-31')['Close']
returns = np.log(prices / prices.shift(1)).dropna()
# %% [markdown]
# Test de estacionariedad en retornos
# %%
for col in returns.columns:
    result = adfuller(returns[col])
    print(f'ADF para {col}:')
    print(f'Estadistico: {result[0]:.4f}, p-valor: {result[1]:.4f}')
# %% [markdown]
# Estimacion VAR
# %%
model = VAR(returns)
lag_order = model.select_order(
    maxlags = 15
)
print('Criterios de seleccion de lags:')
print(lag_order.summary())

selected_lag = lag_order.aic
var_result = model.fit(selected_lag)
print('Resumen del modelo VAR:')
print(var_result.summary())
# %% [markdown]
# Test de autocorrelacion en residuos (Way: Ljung Box)
# %%
for col in var_result.resid.columns:
    print(f'Ljung Box para {col}:')
    ljung_test = acorr_ljungbox(var_result.resid[col], lags=[10], return_df=True)
    print(ljung_test)
# %% [markdown]
# Modelo Markov Switching sobre S&P
# %%
mr_model = MarkovRegression(returns['^GSPC'], k_regimes=2, trend='c', switching_variance=True)
mr_result = mr_model.fit()
print('Resumen modelo Markov Switching:')
print(mr_result.summary())
# %% [markdown]
# Ver probabilidades de regimen
# %%
plt.figure(figsize=(12,6))
plt.plot(returns['^GSPC'], label='S&P Returns')
plt.plot(mr_result.smoothed_marginal_probabilities[0], label='Prob. Bear', alpha=0.7)
plt.plot(mr_result.smoothed_marginal_probabilities[1], label='Prob. Bull', alpha=0.7)
plt.legend()
plt.title('Probabilidades de Regimenes - Markov Switching')
plt.show()
# %% [markdown]
# Markov sobre residuos del VAR
# %%
resid_sp500 = var_result.resid['^GSPC'].dropna()
mr_resid_model = MarkovRegression(resid_sp500, k_regimes=2, trend='c', switching_variance=True)
mr_resid_result = mr_resid_model.fit()
print('Resumen modelo Markov Switching (Taylors Version):')
print(mr_resid_result.summary())

plt.figure(figsize=(12,6))
plt.plot(resid_sp500, label='Residuos VAR')
plt.plot(mr_resid_result.smoothed_marginal_probabilities[0], label='Shock negativo', alpha=0.7)
plt.plot(mr_resid_result.smoothed_marginal_probabilities[1], label='Shock leve', alpha=0.7)
plt.legend()
plt.title("Markov sobre Residuos del VAR")
plt.show()
# %% [markdown]
# Estrategia basada en regimen
# %%
prob_bull_filtered = mr_resid_result.filtered_marginal_probabilities[1]
weight_sp500 = prob_bull_filtered.shift(1).reindex(returns.index).fillna(0)
returns = returns.merge(weight_sp500, left_index=True, right_index=True)
returns.columns = ['IEF', '^GSPC', 'Prob_bull_filtered']
returns['W'] = np.where(returns['Prob_bull_filtered'] > 0.5, 0.6, 0.4)
returns['strategy'] = returns['W'] * returns['^GSPC'] + (1-returns['W']) * returns['IEF']
# %% [markdown]
# Compute EQ
# %%
(1 + returns[['^GSPC', 'IEF', 'strategy']]).cumprod().plot(figsize=(12,6), title='Estrategia vs Benchmarks')
plt.show()
# %% [markdown]
# Test de medias
# %%
print('Media y desviacion estandar:')
print(f'S&P 500: {returns["^GSPC"].mean():.5f}, Std: {returns["^GSPC"].std():.5f}')
print(f'Estrategia: {returns["strategy"].mean():.5f}, Std: {returns["strategy"].std():.5f}')
print(
      f'Diferencias S&P 500 - Estrategia: {returns["^GSPC"].mean() - returns["strategy"].mean():.5f}, Std: {returns["^GSPC"].std() - returns["strategy"].std():.5f}'
)
t_stat, p_val = ttest_ind(returns['strategy'], returns['^GSPC'])
print(f'Test t: t = {t_stat:.4f}, p-valor = {p_val:.4f}')
# %% [markdown]
# Estabilidad VAR y evaluacion Markov
# %%
print('Estabilidad del VAR:', var_result.is_stable(verbose = True))
transition_matrix = mr_resid_result.params[-4:].values.reshape(2,2)
expected_durations = 1 / (1 - np.diag(transition_matrix))


print('Matriz de transicion:', transition_matrix)
print(f'Duracion esperada regimen 0: {expected_durations[0]:.1f} di­as')
print(f'Duracion esperada regimen 1: {expected_durations[1]:.1f} dias')
# %% [markdown]
# Sharpe por regimen
# %%
returns['regime'] = (prob_bull_filtered > 0.5).astype(int)
sharpe_by_regime = returns.groupby('regime')['strategy'].mean() / returns.groupby('regime')['strategy'].std()
print('Sharpe por regimen:')
print(sharpe_by_regime)
# %% [markdown]
# Distribucion de retornos por regimen
# %%
plt.figure(figsize=(10,6))
for regime in [0, 1]:
    subset = returns[returns['regime'] == regime]['^GSPC']
    plt.hist(subset, bins=100, alpha=0.6, label=f'Regimen {regime}')
plt.legend()
plt.title('Distribucion de Retornos del S&P 500 por Regimen')
plt.xlabel('Retorno diario')
plt.ylabel('Frecuencia')
plt.show()

# %% [markdown]
# # Notas sobre el pryecto
# %%
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from scipy.stats import ttest_ind

#GET data
symbols = ['^GSPC', 'IEF']
prices = yf.download(symbols, start='2010-01-01', end='2024-12-31')['Close']
returns = np.log(prices / prices.shift(1)).dropna()


#Test de estacionariedad en retornos
"""
Nota 1: Segun la bibliografi­a se los suele asumir estacionales
Nota 2: El usarlos por regi­menes puede ayudar a que se vuelvan mas estacionales ?
Nota 3: Busco p-valor < 0.05
"""
for col in returns.columns:
    result = adfuller(returns[col])
    print(f'ADF para {col}:')
    print(f'Estadistico: {result[0]:.4f}, p-valor: {result[1]:.4f}')


#Estimacion VAR
"""
Nota 4: Con todos los lags conseguis un score similar, ojo ---> realmente es optimo 9?
Nota 5: Log likelihood, AIC, BIC, usar para comprar modelos con = parametros
Nota 6:
    Coeficient: Como afectan los lags
    prob: Para que sean significativos tienen que ser < 0.05 ---> Muchos NO lo son

Resultados sobre IEF:
    Nota 7: El S&P en T-1 es Ãºtil para ver la dinÃ¡mica del IEF en T0 (Afecta positivo: Si sube S&P en T-1, IEF sube en T0)
    Nota 8: La mayorÃ­a de los resultados del IEF no son significativos
Resultados sobre S&P:
    Nota 9: El S&P sirve para el S&P (Ej: en T-1 subio, En t0 bajarÃ­a)
Resultado de matriz de residuos:
    Nota 10: No quedÃ³ solo ruido blanco (DeberÃ­a haber sido mas cercana a 0 la corr.)
"""
model = VAR(returns)
lag_order = model.select_order(
    maxlags = 15
)
print('Criterios de seleccion de lags:')
print(lag_order.summary())

selected_lag = lag_order.aic
var_result = model.fit(selected_lag)
print('Resumen del modelo VAR:')
print(var_result.summary())


#Test de autocorrelacion en residuos (Way: Ljung Box)
"""
Nota 11: Quiero ver si me quedo ruido blanco, osea si los errores tienen memoria (autocorrelacion significativa)
- Quiero numero > 0.05 en lb_pvalue ---> No hay evidencia de autocorrelacion ---> Residuos = ruido blanco
Resultado de Ljung:
    Nota 12: No se muestra autocorr. en ninguno de los 2, (> 0.05 lb_pvalue)
"""
for col in var_result.resid.columns:
    print(f'Ljung Box para {col}:')
    ljung_test = acorr_ljungbox(var_result.resid[col], lags=[10], return_df=True)
    print(ljung_test)


#Modelo Markov Switching sobre S&P
"""
Resultado markov: 3 regi­menes
    (1) Bull: Media positiva, Volatildiad baja
    (2) Bear: Media negativa, Volatlidad alta
    (3) Cambio: -
Nota 13: El bear no tiene mucha mas volatilidad - Agregar mas regi­menes ?
Nota 14: La prob. de seguir en bull es 97% (B&H es inganable basicamente)
"""
mr_model = MarkovRegression(returns['^GSPC'], k_regimes=2, trend='c', switching_variance=True)
mr_result = mr_model.fit()
print('Resumen modelo Markov Switching:')
print(mr_result.summary())


#Ver probabilidades de regimen
"""
Nota 15: Cambios en regimenes demasiado rapido, falta consistencia, sobreajuste ?
"""
plt.figure(figsize=(12,6))
plt.plot(returns['^GSPC'], label='S&P Returns')
plt.plot(mr_result.smoothed_marginal_probabilities[0], label='Prob. Bear', alpha=0.7)
plt.plot(mr_result.smoothed_marginal_probabilities[1], label='Prob. Bull', alpha=0.7)
plt.legend()
plt.title('Probabilidades de Regi­menes - Markov Switching')
plt.show()

#Markov sobre residuos del VAR
"""
Nota 16: Aca se solventa tema > volatilidad en bear - este es mas intereante
"""
resid_sp500 = var_result.resid['^GSPC'].dropna()
mr_resid_model = MarkovRegression(resid_sp500, k_regimes=2, trend='c', switching_variance=True)
mr_resid_result = mr_resid_model.fit()
print('Resumen modelo Markov Switching (Taylors Version):')
print(mr_resid_result.summary())

plt.figure(figsize=(12,6))
plt.plot(resid_sp500, label='Residuos VAR')
plt.plot(mr_resid_result.smoothed_marginal_probabilities[0], label='Shock negativo', alpha=0.7)
plt.plot(mr_resid_result.smoothed_marginal_probabilities[1], label='Shock leve', alpha=0.7)
plt.legend()
plt.title("Markov sobre Residuos del VAR")
plt.show()


#Estrategia basada en regimen
prob_bull_filtered = mr_resid_result.filtered_marginal_probabilities[1]
weight_sp500 = prob_bull_filtered.shift(1).reindex(returns.index).fillna(0)
returns = returns.merge(weight_sp500, left_index=True, right_index=True)
returns.columns = ['IEF', '^GSPC', 'Prob_bull_filtered']
returns['W'] = np.where(returns['Prob_bull_filtered'] > 0.5, 0.6, 0.4)
returns['strategy'] = returns['W'] * returns['^GSPC'] + (1-returns['W']) * returns['IEF']

#Compute EQ
(1 + returns[['^GSPC', 'IEF', 'strategy']]).cumprod().plot(figsize=(12,6), title='Estrategia vs Benchmarks')
plt.show()


#Test de medias
"""
Nota 17: La estrategia tiene una media de los retornos menor
Nota 18: La estrategia tiene un desvio mucho menor
Nota 19: La diferencia de medias no es significativa (P-Valor de test T > 0.05)
"""
print('Media y desviacion estandar:')
print(f'S&P 500: {returns["^GSPC"].mean():.5f}, Std: {returns["^GSPC"].std():.5f}')
print(f'Estrategia: {returns["strategy"].mean():.5f}, Std: {returns["strategy"].std():.5f}')
print(
      f'Diferencias S&P 500 - Estrategia: {returns["^GSPC"].mean() - returns["strategy"].mean():.5f}, Std: {returns["^GSPC"].std() - returns["strategy"].std():.5f}'
)
t_stat, p_val = ttest_ind(returns['strategy'], returns['^GSPC'])
print(f'Test t: t = {t_stat:.4f}, p-valor = {p_val:.4f}')


#Estabilidad VAR y evaluacion Markov
"""
Nota 20: El modelo VAR es estable ya que todos los autovalores son < 1 (VAR = Estable)
Nota 21: El valor esperado por regÃ­men es muy bajo, no muestra tendencias (Regimenes = Inestable)
"""
print('Estabilidad del VAR:', var_result.is_stable(verbose = True))
transition_matrix = mr_resid_result.params[-4:].values.reshape(2,2)
expected_durations = 1 / (1 - np.diag(transition_matrix))


print('Matriz de transicion:', transition_matrix)
print(f'Duracion esperada regimen 0: {expected_durations[0]:.1f} di­as')
print(f'Duracion esperada regimen 1: {expected_durations[1]:.1f} dias')


#Sharpe por regimen
"""
Nota 22: Suele ser mas bajo el sharpe en el regimen bear. Algo esperable
"""
returns['regime'] = (prob_bull_filtered > 0.5).astype(int)
sharpe_by_regime = returns.groupby('regime')['strategy'].mean() / returns.groupby('regime')['strategy'].std()
print('Sharpe por regimen:')
print(sharpe_by_regime)


#Distribucion de retornos por regimen
plt.figure(figsize=(10,6))
for regime in [0, 1]:
    subset = returns[returns['regime'] == regime]['^GSPC']
    plt.hist(subset, bins=100, alpha=0.6, label=f'Regimen {regime}')
plt.legend()
plt.title('Distribucion de Retornos del S&P 500 por Regimen')
plt.xlabel('Retorno diario')
plt.ylabel('Frecuencia')
plt.show()