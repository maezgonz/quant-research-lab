import base64
from io import BytesIO

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from matplotlib.ticker import FuncFormatter

# Intentamos importar módulos externos, si no existen, seguimos sin ellos
try:
    from src.analytics.vix_analyzer import TradingVIX
except ImportError:
    TradingVIX = None

# ==========================================
# NUEVAS FUNCIONES DE VISUALIZACIÓN
# ==========================================


def plot_drawdown(df_total, save_path=None):
    """Grafica la evolución del drawdown a lo largo del tiempo."""
    plt.figure(figsize=(12, 6))

    # Calcular drawdown
    valores = df_total["Total_Value"]
    pico_maximo = valores.cummax()
    drawdown = (valores - pico_maximo) / pico_maximo * 100

    # Graficar
    plt.plot(drawdown.index, drawdown, color="red", linewidth=1.5)
    plt.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.15)

    # Marcar máximo drawdown
    idx_max_dd = drawdown.idxmin()
    max_dd = drawdown.min()
    plt.scatter(idx_max_dd, max_dd, color="red", s=50, zorder=5)
    plt.annotate(
        f"Max DD: {max_dd:.2f}%",
        xy=(idx_max_dd, max_dd),
        xytext=(20, -30),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color="black"),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
    )

    plt.axhline(0, color="black", linestyle="--", alpha=0.3)
    plt.title("Drawdown Histórico de la Cartera", fontsize=14)
    plt.ylabel("Drawdown (%)")
    plt.xlabel("Fecha")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_retornos_distribucion(df_total, save_path=None):
    """Grafica la distribución de los retornos diarios."""
    # Calcular retornos diarios
    retornos = df_total["Total_Value"].pct_change().dropna() * 100

    # Configurar figura
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 10), gridspec_kw={"height_ratios": [1, 2]}
    )

    # Gráfico superior: serie temporal de retornos
    ax1.plot(retornos.index, retornos, color="royalblue", alpha=0.7, linewidth=0.8)
    ax1.bar(
        retornos.index,
        retornos,
        color=np.where(retornos >= 0, "green", "red"),
        alpha=0.4,
        width=1.5,
    )
    ax1.axhline(0, color="black", linestyle="-", linewidth=0.8, alpha=0.3)
    ax1.set_title("Retornos Diarios (%)", fontsize=14)
    ax1.set_ylabel("Retorno Diario (%)")
    ax1.grid(True, alpha=0.3)

    # Gráfico inferior: histograma de distribución
    num_bins = min(50, int(np.sqrt(len(retornos))))
    n, bins, patches = ax2.hist(
        retornos, bins=num_bins, alpha=0.7, color="royalblue", density=True
    )

    # Colorear las barras del histograma según el valor
    for i in range(len(patches)):
        if bins[i] < 0:
            patches[i].set_facecolor("red")
        else:
            patches[i].set_facecolor("green")

    # Añadir curva de distribución normal para comparar
    mu = retornos.mean()
    sigma = retornos.std()
    x = np.linspace(min(bins), max(bins), 100)
    ax2.plot(
        x,
        1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-((x - mu) ** 2) / (2 * sigma**2)),
        linewidth=2,
        color="black",
        label="Normal",
    )

    # Añadir líneas verticales para estadísticas clave
    ax2.axvline(
        mu, color="black", linestyle="--", linewidth=1.5, label=f"Media: {mu:.2f}%"
    )
    ax2.axvline(0, color="gray", linestyle="-", linewidth=1, alpha=0.8)

    # Mejorar estética
    ax2.set_title("Distribución de Retornos Diarios", fontsize=14)
    ax2.set_xlabel("Retorno Diario (%)")
    ax2.set_ylabel("Densidad")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_correlacion_activos(df_val, save_path=None):
    """Grafica un mapa de calor de correlación entre activos."""
    # Calcular retornos para cada activo
    retornos = df_val.pct_change().dropna()

    # Calcular matriz de correlación
    corr_matrix = retornos.corr()

    # Generar máscara para triángulo superior (opcional)
    mascara = np.triu(np.ones_like(corr_matrix, dtype=bool))

    # Configurar figura
    plt.figure(figsize=(14, 12))

    # Generar heatmap
    cmap = plt.cm.RdYlGn  # Rojo para correlaciones negativas, Verde para positivas
    im = plt.imshow(corr_matrix, cmap=cmap, vmin=-1, vmax=1)

    # Añadir etiquetas
    plt.colorbar(im, label="Coeficiente de Correlación")
    plt.title("Mapa de Correlación entre Activos", fontsize=16)

    # Configurar ejes con nombres de tickers
    tickers = corr_matrix.columns
    plt.xticks(range(len(tickers)), tickers, rotation=90)
    plt.yticks(range(len(tickers)), tickers)

    # Añadir valores en cada celda
    for i in range(len(tickers)):
        for j in range(len(tickers)):
            if not mascara[i, j]:  # Si no está en el triángulo superior
                texto = f"{corr_matrix.iloc[i, j]:.2f}"
                color_texto = "white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black"
                plt.text(
                    j, i, texto, ha="center", va="center", color=color_texto, fontsize=8
                )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_rendimiento_por_tipo(df_val, df_cost, save_path=None):
    """Grafica la evolución del valor de cada tipo de activo en el tiempo."""
    # Configurar figura
    plt.figure(figsize=(12, 8))

    # Definir categorías según el campo 'tipo' en MI_CARTERA
    categorias = {}
    for op in MI_CARTERA:
        tipo = op.get("tipo", "otros")
        ticker = op["ticker"]
        if tipo not in categorias:
            categorias[tipo] = []
        categorias[tipo].append(ticker)

    # Colores para cada tipo
    colores = {
        "stocks": "royalblue",
        "bonds": "gold",
        "notes": "green",
        "cedears": "purple",
        "otros": "gray",
    }

    # Calcular valor total de cada tipo a lo largo del tiempo
    for tipo, tickers in categorias.items():
        # Filtramos los tickers presentes en los DataFrames
        tickers_presentes = [t for t in tickers if t in df_val.columns]

        if not tickers_presentes:
            continue

        # Calcular valor total de este tipo
        valor_serie = df_val[tickers_presentes].sum(axis=1)

        # Graficar
        plt.plot(
            valor_serie.index,
            valor_serie,
            label=f"{tipo.capitalize()}",
            color=colores.get(tipo, "gray"),
            linewidth=2,
        )

    # Mejorar estética
    plt.title("Evolución del Valor por Tipo de Activo", fontsize=16)
    plt.ylabel("Valor ($)")
    plt.grid(True, alpha=0.3)
    plt.legend()

    # Formatear eje Y para mostrar valores en millones
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"${x / 1e6:.1f}M"))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_rendimiento_normalizado(df_val, df_cost, save_path=None):
    """Grafica el rendimiento normalizado (base 100) para comparar distintos activos."""
    # Configurar figura
    plt.figure(figsize=(12, 8))

    # Obtener primeros valores para normalización
    primeros_valores = {}

    # Para cada tipo de activo, obtener los mejores 3 performers
    categorias = {}
    for op in MI_CARTERA:
        tipo = op.get("tipo", "otros")
        ticker = op["ticker"]
        if tipo not in categorias:
            categorias[tipo] = []
        categorias[tipo].append(ticker)

    # Colores para cada tipo
    colores = {
        "stocks": ["royalblue", "lightblue", "darkblue"],
        "bonds": ["gold", "orange", "darkgoldenrod"],
        "notes": ["green", "lightgreen", "darkgreen"],
        "cedears": ["purple", "magenta", "darkviolet"],
        "otros": ["gray", "lightgray", "darkgray"],
    }

    # Para cada tipo, seleccionar los 3 activos con mejor rendimiento
    todos_rendimientos = {}

    for tipo, tickers in categorias.items():
        # Filtrar tickers presentes
        tickers_presentes = [t for t in tickers if t in df_val.columns]

        # Calcular rendimientos
        for ticker in tickers_presentes:
            # Obtener primera fecha con valor
            valores = df_val[ticker]
            fechas_con_valor = valores[valores > 0].index
            if len(fechas_con_valor) == 0:
                continue

            primera_fecha = fechas_con_valor[0]
            primer_valor = valores[primera_fecha]

            # Obtener último valor
            ultimo_valor = valores.iloc[-1]

            # Calcular rendimiento
            rendimiento = (ultimo_valor / primer_valor - 1) * 100
            todos_rendimientos[(tipo, ticker)] = rendimiento

    # Ordenar por rendimiento y tomar los 3 mejores de cada tipo
    mejores_por_tipo = {}
    for (tipo, ticker), rendimiento in sorted(
        todos_rendimientos.items(), key=lambda x: x[1], reverse=True
    ):
        if tipo not in mejores_por_tipo:
            mejores_por_tipo[tipo] = []
        if len(mejores_por_tipo[tipo]) < 3:
            mejores_por_tipo[tipo].append(ticker)

    # Graficar rendimientos normalizados
    for tipo, mejores_tickers in mejores_por_tipo.items():
        for i, ticker in enumerate(mejores_tickers):
            # Obtener valores
            valores = df_val[ticker]

            # Encontrar primera fecha con valor
            fechas_con_valor = valores[valores > 0].index
            if len(fechas_con_valor) == 0:
                continue

            primera_fecha = fechas_con_valor[0]
            primer_valor = valores[primera_fecha]

            # Normalizar
            valores_norm = valores / primer_valor * 100

            # Solo graficar desde la fecha de inversión
            valores_norm = valores_norm[primera_fecha:]

            # Graficar
            plt.plot(
                valores_norm.index,
                valores_norm,
                label=f"{ticker} ({tipo})",
                color=colores.get(tipo, ["gray"])[
                    min(i, len(colores.get(tipo, ["gray"])) - 1)
                ],
                linewidth=2,
            )

    # Graficar también el valor total normalizado
    valor_total = df_val.sum(axis=1)
    # Encontrar primera fecha con valor
    fechas_con_valor = valor_total[valor_total > 0].index
    if len(fechas_con_valor) > 0:
        primera_fecha = fechas_con_valor[0]
        primer_valor = valor_total[primera_fecha]
        valor_total_norm = valor_total / primer_valor * 100
        plt.plot(
            valor_total_norm.index,
            valor_total_norm,
            label="Cartera Total",
            color="black",
            linewidth=3,
            linestyle="--",
        )

    # Mejorar estética
    plt.title("Rendimiento Normalizado (Base 100) por Activo", fontsize=16)
    plt.ylabel("Rendimiento (%)")
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper left")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def plot_kpis_tiempo(df_total, window=30, save_path=None):
    """Grafica la evolución de KPIs clave a lo largo del tiempo."""
    # Configurar figura
    fig, axs = plt.subplots(3, 1, figsize=(12, 14), sharex=True)

    # Calcular KPIs móviles
    retornos = df_total["Total_Value"].pct_change().fillna(0)

    # 1. Rolling Sharpe Ratio (anualizado)
    rolling_mean = retornos.rolling(window).mean() * 252
    rolling_std = retornos.rolling(window).std() * np.sqrt(252)
    rolling_sharpe = rolling_mean / rolling_std

    # 2. Rolling Profit Factor
    rolling_ganancia = retornos[retornos > 0].rolling(window).sum()
    rolling_perdida = retornos[retornos < 0].rolling(window).sum()
    rolling_profit_factor = abs(rolling_ganancia / rolling_perdida)

    # 3. Rolling Win Rate
    rolling_wins = (retornos > 0).rolling(window).sum() / window * 100

    # Graficar
    # Sharpe Ratio
    axs[0].plot(rolling_sharpe.index, rolling_sharpe, color="royalblue", linewidth=2)
    axs[0].axhline(0, color="gray", linestyle="--", alpha=0.5)
    axs[0].axhline(1, color="green", linestyle="--", alpha=0.5, label="Bueno (>1)")
    axs[0].axhline(-1, color="red", linestyle="--", alpha=0.5, label="Malo (<-1)")
    axs[0].set_title(f"Sharpe Ratio (Ventana {window} días)", fontsize=14)
    axs[0].set_ylabel("Sharpe Ratio")
    axs[0].grid(True, alpha=0.3)
    axs[0].legend()

    # Profit Factor
    axs[1].plot(
        rolling_profit_factor.index, rolling_profit_factor, color="green", linewidth=2
    )
    axs[1].axhline(1, color="red", linestyle="--", alpha=0.5, label="Breakeven (=1)")
    axs[1].axhline(2, color="green", linestyle="--", alpha=0.5, label="Bueno (>2)")
    axs[1].set_title(f"Profit Factor (Ventana {window} días)", fontsize=14)
    axs[1].set_ylabel("Profit Factor")
    axs[1].grid(True, alpha=0.3)
    axs[1].legend()

    # Win Rate
    axs[2].plot(rolling_wins.index, rolling_wins, color="orange", linewidth=2)
    axs[2].axhline(50, color="red", linestyle="--", alpha=0.5, label="Breakeven (50%)")
    axs[2].axhline(60, color="green", linestyle="--", alpha=0.5, label="Bueno (>60%)")
    axs[2].set_title(f"Win Rate % (Ventana {window} días)", fontsize=14)
    axs[2].set_ylabel("Win Rate (%)")
    axs[2].set_xlabel("Fecha")
    axs[2].grid(True, alpha=0.3)
    axs[2].legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


# ==========================================
# 1. CONFIGURACIÓN DE TU CARTERA (ACTUALIZADA)
# ==========================================
# Se agregó el campo 'tipo' para distinguir el endpoint de la API.
# Tipos válidos según API: 'stocks', 'bonds', 'cedears', 'notes'

MI_CARTERA = [
    # --- ACCIONES / CEDEARS (Endpoint: /stocks/ o /cedears/) ---
    {"ticker": "PAMP", "cantidad": 999, "fecha_compra": "2023-10-10", "tipo": "stocks"},
    {"ticker": "EDN", "cantidad": 1378, "fecha_compra": "2023-10-10", "tipo": "stocks"},
    {
        "ticker": "TGSU2",
        "cantidad": 646,
        "fecha_compra": "2023-10-10",
        "tipo": "stocks",
    },
    {
        "ticker": "TGNO4",
        "cantidad": 837,
        "fecha_compra": "2023-10-10",
        "tipo": "stocks",
    },
    {"ticker": "YPFD", "cantidad": 111, "fecha_compra": "2023-10-10", "tipo": "stocks"},
    {
        "ticker": "METR",
        "cantidad": 2545,
        "fecha_compra": "2023-10-10",
        "tipo": "stocks",
    },
    {"ticker": "GGAL", "cantidad": 558, "fecha_compra": "2023-10-10", "tipo": "stocks"},
    {"ticker": "BMA", "cantidad": 68, "fecha_compra": "2023-10-10", "tipo": "stocks"},
    {"ticker": "TRAN", "cantidad": 182, "fecha_compra": "2023-10-10", "tipo": "stocks"},
    {"ticker": "MOLI", "cantidad": 63, "fecha_compra": "2023-10-10", "tipo": "stocks"},
    {
        "ticker": "MORI",
        "cantidad": 26867,
        "fecha_compra": "2023-10-10",
        "tipo": "stocks",
    },
    # --- BONOS (Endpoint: /bonds/) ---
    {"ticker": "BPOA7", "cantidad": 872, "fecha_compra": "2024-04-01", "tipo": "bonds"},
    {"ticker": "BPOB7", "cantidad": 883, "fecha_compra": "2024-04-01", "tipo": "bonds"},
    {
        "ticker": "BPOC7",
        "cantidad": 1308,
        "fecha_compra": "2024-04-01",
        "tipo": "bonds",
    },
    {
        "ticker": "BPOD7",
        "cantidad": 1327,
        "fecha_compra": "2024-04-01",
        "tipo": "bonds",
    },
    {"ticker": "AE38", "cantidad": 3136, "fecha_compra": "2026-01-30", "tipo": "bonds"},
    {"ticker": "AL41", "cantidad": 4069, "fecha_compra": "2023-10-10", "tipo": "bonds"},
    {"ticker": "GD41", "cantidad": 885, "fecha_compra": "2023-10-10", "tipo": "bonds"},
    {"ticker": "AL30", "cantidad": 6019, "fecha_compra": "2023-10-10", "tipo": "bonds"},
    {"ticker": "GD30", "cantidad": 6403, "fecha_compra": "2023-10-10", "tipo": "bonds"},
    # --- Letras (Actualizar)
    {
        "ticker": "S30N6",
        "cantidad": 92539332,
        "fecha_compra": "2026-08-12",
        "tipo": "notes",
    },
]

# Configuración visual
plt.style.use("seaborn-v0_8-darkgrid")
plt.rcParams["figure.facecolor"] = "#EAEAF2"
plt.rcParams["axes.facecolor"] = "#EAEAF2"


# ==========================================
# 2. OBTENCIÓN DE DATOS (MEJORADA)
# ==========================================
def obtener_historial_precio(ticker, tipo_activo, fecha_inicio_global):
    """
    Obtiene datos históricos usando el endpoint correcto según el tipo de activo.
    """
    # Determinar el endpoint según el tipo de activo
    if tipo_activo == "notes":
        endpoint = "live_arg_notes"
    else:
        endpoint = f"historical/{tipo_activo}"

    # Construcción dinámica de la URL
    url = f"https://data912.com/{endpoint}/{ticker}"
    print(f"📡 Consultando {ticker} en {url}...")

    try:
        # Timeout de 10s para evitar bloqueos
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Verificamos si tenemos datos válidos
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)

                # Normalización de fecha (soporta formato Unix o String)
                if "t" in df.columns:
                    df["Date"] = pd.to_datetime(df["t"], unit="s")
                elif "date" in df.columns:
                    df["Date"] = pd.to_datetime(df["date"])
                else:
                    raise ValueError("Formato de fecha desconocido")

                df.set_index("Date", inplace=True)

                # Buscar columna de precio de cierre
                col_cierre = "c" if "c" in df.columns else "close"
                if col_cierre in df.columns:
                    # Devolvemos precios sin dividir (la división se hará en el cálculo del valor)
                    return df[col_cierre]
            else:
                raise ValueError("Datos vacíos o inválidos")

    except Exception as e:
        print(f"⚠️ Error obteniendo {ticker}: {e}. Intentando fuente alternativa.")
        # Aquí se podría implementar una fuente alternativa si existe
        # Si falla, lanzamos la excepción para manejarla en el nivel superior
        raise


# ==========================================
# 3. MOTOR DE CÁLCULO
# ==========================================
def procesar_cartera(cartera):
    print("\n🔄 Procesando cartera y calculando curvas de equidad...")

    # Fecha mínima de compra para iniciar la serie temporal
    fechas = [pd.to_datetime(op["fecha_compra"]) for op in cartera]
    fecha_minima = min(fechas) if fechas else pd.Timestamp.now()

    df_valor_diario = pd.DataFrame()
    df_costo_diario = pd.DataFrame()

    for operacion in cartera:
        ticker = operacion["ticker"]
        qty = operacion["cantidad"]
        tipo = operacion.get("tipo", "stocks")  # Default a stocks
        fecha_compra = pd.to_datetime(operacion["fecha_compra"])

        try:
            # 1. Obtener precios con la función mejorada
            precios = obtener_historial_precio(ticker, tipo, fecha_minima)

            # 2. Reindexar para tener un rango de fechas continuo
            rango_completo = pd.date_range(
                start=fecha_minima, end=pd.Timestamp.now(), freq="B"
            )
            precios = precios.reindex(rango_completo, method="ffill")

            # 3. Calcular valor solo desde la fecha de compra
            mascara_tenencia = precios.index >= fecha_compra

            # Valor de Mercado
            if tipo in ["bonds", "notes"]:
                # Para bonos y letras: (tenencia x valor) / 100
                valor_posicion = (precios * qty) / 100
            else:
                # Para acciones: tenencia x valor
                valor_posicion = precios * qty

            valor_posicion[~mascara_tenencia] = 0  # Antes de comprar vale 0
            valor_posicion.name = ticker

            # Costo Base (Dinero invertido)
            try:
                # Precio del día de compra
                precio_compra_u = precios[precios.index >= fecha_compra].iloc[0]
            except IndexError:
                precio_compra_u = precios.iloc[-1]  # Fallback

            if tipo in ["bonds", "notes"]:
                costo_total_pos = (precio_compra_u * qty) / 100
            else:
                costo_total_pos = precio_compra_u * qty

            serie_costo = pd.Series(0.0, index=precios.index, name=ticker)
            serie_costo[mascara_tenencia] = costo_total_pos

            # 5. Consolidar en el DataFrame principal
            if df_valor_diario.empty:
                df_valor_diario = pd.DataFrame(valor_posicion)
                df_costo_diario = pd.DataFrame(serie_costo)
            else:
                df_valor_diario = df_valor_diario.join(
                    valor_posicion, rsuffix=f"_{ticker}"
                )
                df_costo_diario = df_costo_diario.join(
                    serie_costo, rsuffix=f"_{ticker}"
                )

        except Exception as e:
            print(f"⚠️ No se pudieron obtener datos para {ticker}: {e}")
            print("   Se omitirá este activo del análisis.")

    # Limpieza
    df_valor_diario.fillna(0, inplace=True)
    df_costo_diario.fillna(0, inplace=True)

    # --- CÁLCULOS TOTALES ---
    df_total = pd.DataFrame()
    df_total["Total_Invested"] = df_costo_diario.sum(axis=1)
    df_total["Total_Value"] = df_valor_diario.sum(axis=1)

    # P&L y ROI
    df_total["PnL_Acumulado"] = df_total["Total_Value"] - df_total["Total_Invested"]
    df_total["PnL_Diario"] = df_total["PnL_Acumulado"].diff().fillna(0)

    # Evitar división por cero
    df_total["ROI_Pct"] = np.where(
        df_total["Total_Invested"] > 0,
        (df_total["PnL_Diario"] / df_total["Total_Invested"]) * 100,
        0,
    )

    df_total["Color_PnL"] = np.where(
        df_total["PnL_Diario"] >= 0, "forestgreen", "firebrick"
    )

    # Retornamos los 3 DFs para usarlos en los análisis avanzados
    return df_total, df_valor_diario, df_costo_diario


# ==========================================
# 4. FUNCIONES DE ANÁLISIS Y VISUALIZACIÓN
# ==========================================


def plot_dashboard(df_total, save_path=None):
    tickers_cnt = len(MI_CARTERA)
    titulo = f"Portafolio Consolidado ({tickers_cnt} Activos)"

    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1, figsize=(12, 14), sharex=True, gridspec_kw={"height_ratios": [2, 1, 1]}
    )

    fig.suptitle(titulo, fontsize=16, y=0.94)

    # P&L Acumulado
    ax1.plot(
        df_total.index,
        df_total["PnL_Acumulado"],
        color="royalblue",
        lw=2,
        label="Ganancia Neta ($)",
    )
    ax1.fill_between(
        df_total.index, df_total["PnL_Acumulado"], 0, alpha=0.1, color="royalblue"
    )
    ax1.bar(
        df_total.index,
        df_total["PnL_Diario"],
        color=df_total["Color_PnL"],
        alpha=0.5,
        label="Var. Diaria",
        width=1.0,
    )
    ax1.set_ylabel("P&L ($)")
    ax1.legend(loc="upper left")
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"${x:,.0f}"))
    ax1.grid(True, alpha=0.3)

    # Capital Invertido vs Valor
    ax2.stackplot(
        df_total.index,
        df_total["Total_Invested"],
        labels=["Costo Base"],
        colors=["orange"],
        alpha=0.4,
    )
    ax2.plot(
        df_total.index,
        df_total["Total_Value"],
        color="darkgreen",
        lw=1.5,
        label="Valor Mercado",
    )
    ax2.set_ylabel("Capital ($)")
    ax2.legend(loc="upper left")
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"${x / 1e6:.1f}M"))
    ax2.grid(True, alpha=0.3)

    # ROI Diario
    colores_roi = np.where(df_total["ROI_Pct"] >= 0, "green", "red")
    ax3.bar(df_total.index, df_total["ROI_Pct"], color=colores_roi, width=1.0)
    ax3.set_ylabel("ROI Diario (%)")
    ax3.axhline(0, c="black", lw=0.5)
    ax3.grid(True, alpha=0.3)

    # Footer Stats
    if df_total["Total_Invested"].iloc[-1] > 0:
        roi_total = (
            (df_total["Total_Value"].iloc[-1] / df_total["Total_Invested"].iloc[-1]) - 1
        ) * 100
    else:
        roi_total = 0
    pnl_neto = df_total["PnL_Acumulado"].iloc[-1]

    stats = (
        f"ESTADO ACTUAL ({df_total.index[-1].strftime('%Y-%m-%d')}):\n"
        f"Valor Cartera: ${df_total['Total_Value'].iloc[-1]:,.0f} | "
        f"Inversión: ${df_total['Total_Invested'].iloc[-1]:,.0f}\n"
        f"Resultado Neto: ${pnl_neto:+,.0f} ({roi_total:+.2f}%)"
    )

    ax3.text(
        0.5,
        -0.5,
        stats,
        transform=ax3.transAxes,
        ha="center",
        bbox=dict(boxstyle="round", fc="white", ec="gray"),
    )

    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    plt.subplots_adjust(bottom=0.15)

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def calcular_metricas_riesgo(df_valor, df_total):
    """Calcula volatilidad, drawdown y sharpe."""
    if df_valor.empty:
        return {}

    # Retornos diarios
    retornos = df_valor.pct_change().fillna(0)

    # Volatilidad Anualizada
    vol_cartera = df_total["Total_Value"].pct_change().std() * np.sqrt(252)

    # Max Drawdown
    roll_max = df_total["Total_Value"].cummax()
    drawdown = (df_total["Total_Value"] - roll_max) / roll_max
    max_dd = drawdown.min()

    # Sharpe Ratio (Simplificado, tasa libre riesgo = 0)
    retorno_anual = df_total["Total_Value"].pct_change().mean() * 252
    sharpe = retorno_anual / vol_cartera if vol_cartera > 0 else 0

    return {"volatilidad": vol_cartera, "max_drawdown": max_dd, "sharpe": sharpe}


def analizar_bonos(df_valor, df_costo):
    """Analiza específicamente los activos tipo Bono."""
    res = {}
    print("\n===== ANÁLISIS DE RENTA FIJA (BONOS) =====")
    # Filtramos tickers que sabemos que son bonos por la lista MI_CARTERA
    tickers_bonos = [op["ticker"] for op in MI_CARTERA if op.get("tipo") == "bonds"]

    # Filtramos solo los que están en el DF (por si alguno falló en la descarga)
    tickers_bonos = [t for t in tickers_bonos if t in df_valor.columns]

    if not tickers_bonos:
        print("No se encontraron datos de bonos.")
        return res

    val_bonos = df_valor[tickers_bonos].sum(axis=1).iloc[-1]
    cost_bonos = df_costo[tickers_bonos].sum(axis=1).iloc[-1]
    rend = ((val_bonos / cost_bonos) - 1) * 100 if cost_bonos > 0 else 0

    # Cálculo del valor nominal total (suma de todas las cantidades)
    valor_nominal_total = sum(
        op["cantidad"] for op in MI_CARTERA if op.get("tipo") == "bonds"
    )

    print(f"Total en Bonos (Valor Mercado): ${val_bonos:,.0f}")
    print(f"Rendimiento Bonos: {rend:.2f}%")
    print(f"Valor Nominal Total: ${valor_nominal_total:,.0f}")

    res["total_valor"] = val_bonos
    res["rendimiento"] = rend
    res["valor_nominal"] = valor_nominal_total
    res["detalle"] = []

    # Mostrar detalle por bono
    print("\nDetalle por Bono:")
    print(
        f"{'Ticker':<10} {'Cantidad':>10} {'Precio':>10} {'Valor ($)':>15} {'% Paridad':>10}"
    )
    print("-" * 60)

    for ticker in tickers_bonos:
        cantidad = next(
            (op["cantidad"] for op in MI_CARTERA if op["ticker"] == ticker), 0
        )
        ultimo_valor = df_valor[ticker].iloc[-1]

        # Para obtener el precio por unidad, dividimos el valor total de mercado de esta posición
        # por la cantidad y multiplicamos por 100 (para revertir la división por 100 aplicada antes)
        precio = (ultimo_valor / cantidad) * 100 if cantidad > 0 else 0

        print(
            f"{ticker:<10} {cantidad:>10,d} {precio:>10.2f} ${ultimo_valor:>14,.0f} {precio:>9.2f}%"
        )
        res["detalle"].append(
            {
                "ticker": ticker,
                "cantidad": cantidad,
                "precio": precio,
                "valor": ultimo_valor,
                "paridad": precio,
            }
        )
    return res


def analizar_letras_tesoro(df_valor, df_costo):
    """Analiza específicamente los activos tipo Letra del Tesoro."""
    res = {}
    print("\n===== ANÁLISIS DE LETRAS DEL TESORO =====")
    # Filtramos tickers que son letras del tesoro
    tickers_letras = [op["ticker"] for op in MI_CARTERA if op.get("tipo") == "notes"]

    # Filtramos solo los que están en el DF (por si alguno falló en la descarga)
    tickers_letras = [t for t in tickers_letras if t in df_valor.columns]

    if not tickers_letras:
        print("No se encontraron datos de letras del tesoro.")
        return res

    val_letras = df_valor[tickers_letras].sum(axis=1).iloc[-1]
    cost_letras = df_costo[tickers_letras].sum(axis=1).iloc[-1]
    rend = ((val_letras / cost_letras) - 1) * 100 if cost_letras > 0 else 0

    # Valor nominal (cantidad)
    valor_nominal_total = sum(
        op["cantidad"] for op in MI_CARTERA if op.get("tipo") == "notes"
    )

    print(f"Total en Letras (Valor Mercado): ${val_letras:,.0f}")
    print(f"Rendimiento Letras: {rend:.2f}%")
    print(f"Valor Nominal Total: ${valor_nominal_total:,.0f}")

    res["total_valor"] = val_letras
    res["rendimiento"] = rend
    res["valor_nominal"] = valor_nominal_total
    res["detalle"] = []

    # Mostrar detalle por letra
    print("\nDetalle por Letra del Tesoro:")
    print(
        f"{'Ticker':<10} {'Cantidad':>15} {'Precio':>10} {'Valor ($)':>15} {'% Paridad':>10}"
    )
    print("-" * 65)

    for ticker in tickers_letras:
        cantidad = next(
            (op["cantidad"] for op in MI_CARTERA if op["ticker"] == ticker), 0
        )
        ultimo_valor = df_valor[ticker].iloc[-1]

        # Para obtener el precio por unidad, dividimos el valor total de mercado de esta posición
        # por la cantidad y multiplicamos por 100 (para revertir la división por 100 aplicada antes)
        precio = (ultimo_valor / cantidad) * 100 if cantidad > 0 else 0

        print(
            f"{ticker:<10} {cantidad:>15,d} {precio:>10.4f} ${ultimo_valor:>14,.0f} {precio:>9.2f}%"
        )
        res["detalle"].append(
            {
                "ticker": ticker,
                "cantidad": cantidad,
                "precio": precio,
                "valor": ultimo_valor,
                "paridad": precio,
            }
        )
    return res


def plot_composicion_cartera(df_valor, save_path=None):
    """Gráfico de torta de la composición actual."""
    if df_valor.empty:
        return

    ultimos_valores = df_valor.iloc[-1]
    total = ultimos_valores.sum()

    # Agrupar pequeños para limpiar el gráfico
    porcentajes = ultimos_valores / total
    grandes = porcentajes[porcentajes >= 0.02]  # Solo mostrar > 2%
    otros = porcentajes[porcentajes < 0.02].sum()

    datos_grafico = grandes.copy()
    if otros > 0:
        datos_grafico["Otros"] = otros

    plt.figure(figsize=(10, 6))
    plt.pie(
        datos_grafico, labels=datos_grafico.index, autopct="%1.1f%%", startangle=140
    )
    plt.title("Composición de la Cartera (Activos > 2%)")

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


def analizar_rendimiento_por_tipo(df_valor, df_costo):
    """Analiza rendimiento agrupado por tipo de activo."""
    res = []
    print("\n===== ANÁLISIS POR TIPO DE ACTIVO =====")

    # Definir categorías según el campo 'tipo' en MI_CARTERA
    categorias = {}
    for op in MI_CARTERA:
        tipo = op.get("tipo", "otros")
        ticker = op["ticker"]
        if tipo not in categorias:
            categorias[tipo] = []
        categorias[tipo].append(ticker)

    # Analizar rendimiento por categoría
    total_valor = df_valor.sum(axis=1).iloc[-1]

    print(f"{'Tipo':<10} {'Valor ($)':<15} {'% Cartera':<10} {'Rendimiento':<10}")
    print("-" * 45)

    for tipo, tickers in categorias.items():
        # Filtramos los tickers presentes en los DataFrames
        tickers_presentes = [t for t in tickers if t in df_valor.columns]

        if not tickers_presentes:
            continue

        # Calcular valores para esta categoría
        valor_tipo = df_valor[tickers_presentes].sum(axis=1).iloc[-1]
        costo_tipo = df_costo[tickers_presentes].sum(axis=1).iloc[-1]

        # Calcular métricas
        peso_cartera = (valor_tipo / total_valor * 100) if total_valor > 0 else 0
        rendimiento = ((valor_tipo / costo_tipo) - 1) * 100 if costo_tipo > 0 else 0

        print(
            f"{tipo:<10} ${valor_tipo:<14,.0f} {peso_cartera:<9.2f}% {rendimiento:<9.2f}%"
        )
        res.append(
            {
                "tipo": tipo,
                "valor": valor_tipo,
                "peso": peso_cartera,
                "rendimiento": rendimiento,
            }
        )

    print("-" * 45)
    return res


def calcular_kpi_trading(df_total):
    """Calcula indicadores KPI de trading."""
    print("\n===== INDICADORES KPI DE TRADING =====")

    # Parámetros básicos
    capital_inicial = df_total["Total_Invested"].iloc[0] if not df_total.empty else 0
    capital_final = df_total["Total_Value"].iloc[-1] if not df_total.empty else 0
    beneficio_neto = df_total["PnL_Acumulado"].iloc[-1] if not df_total.empty else 0

    # Series para análisis
    retornos_diarios = df_total["Total_Value"].pct_change().fillna(0)
    trades_diarios = df_total["PnL_Diario"].fillna(0)

    # Separar operaciones ganadoras y perdedoras
    op_ganadoras = trades_diarios[trades_diarios > 0]
    op_perdedoras = trades_diarios[trades_diarios < 0]

    # Calcular winrate
    total_trades = len(trades_diarios[trades_diarios != 0])
    total_ganadores = len(op_ganadoras)
    total_perdedores = len(op_perdedoras)
    winrate = (total_ganadores / total_trades * 100) if total_trades > 0 else 0

    # Expectativa por operación
    ganancia_media = op_ganadoras.mean() if not op_ganadoras.empty else 0
    perdida_media = op_perdedoras.mean() if not op_perdedoras.empty else 0

    # Probabilidades
    p_win = total_ganadores / total_trades if total_trades > 0 else 0
    p_loss = total_perdedores / total_trades if total_trades > 0 else 0

    # R-Múltiplo (Relación ganancia media / pérdida media absoluta)
    r_multiple = (ganancia_media / abs(perdida_media)) if perdida_media < 0 else 0

    # Expectancy
    expectancy = (
        (p_win * ganancia_media) + (p_loss * perdida_media)
        if p_win > 0 and p_loss > 0
        else 0
    )

    # Kelly Criterion
    w = p_win
    r = abs(ganancia_media / perdida_media) if perdida_media < 0 else 0
    kelly = (w * (r + 1) - 1) / r if r > 0 else 0

    # Drawdown y Recovery factor
    valores_acumulados = df_total["Total_Value"]
    max_dd_value = 0
    if not valores_acumulados.empty:
        peak = valores_acumulados.cummax()
        drawdown = (valores_acumulados - peak) / peak
        max_dd_value = drawdown.min()

    recovery_factor = (
        abs(beneficio_neto / (max_dd_value * capital_inicial))
        if max_dd_value < 0 and capital_inicial > 0
        else 0
    )

    # Beneficio Bruto y Profit Factor
    beneficio_bruto = op_ganadoras.sum()
    perdida_bruta = op_perdedoras.sum()
    profit_factor = abs(beneficio_bruto / perdida_bruta) if perdida_bruta < 0 else 0

    # Riesgo de Ruina (cálculo simplificado)
    riesgo_ruina = (
        np.exp(-2 * capital_inicial * expectancy / (ganancia_media**2))
        if ganancia_media > 0
        else 1
    )
    riesgo_ruina = min(riesgo_ruina, 1.0)  # Limitar a 100%

    # Prob. de pérdidas consecutivas (asumiendo independencia)
    prob_perdidas_consecutivas = (
        p_loss**5 if p_loss > 0 else 0
    )  # Probabilidad de 5 pérdidas consecutivas

    # Asimetría de información y Nash Equilibrium
    asimetria = (
        (ganancia_media - abs(perdida_media)) / (ganancia_media + abs(perdida_media))
        if (ganancia_media + abs(perdida_media)) > 0
        else 0
    )
    nash_equilibrio = (
        p_win * p_loss * r_multiple
        if p_win > 0 and p_loss > 0 and r_multiple > 0
        else 0
    )

    # Relación Riesgo/Beneficio
    relacion_rb = (
        abs(perdida_media) / ganancia_media if ganancia_media > 0 else float("inf")
    )

    # Esperanza Matemática
    esperanza_matematica = (
        (p_win * ganancia_media) - (p_loss * abs(perdida_media))
        if p_win > 0 and p_loss > 0
        else 0
    )

    # Puntuación Final (score simplificado)
    score = (winrate / 100) * profit_factor * (1 + recovery_factor) * (1 - riesgo_ruina)

    # Media resultados operaciones
    media_resultados = (
        trades_diarios[trades_diarios != 0].mean()
        if len(trades_diarios[trades_diarios != 0]) > 0
        else 0
    )

    # Imprimir resultados en tablas organizadas
    print("\nPARÁMETROS BÁSICOS")
    print("=" * 60)
    print(f"{'Parámetro':<40} {'Valor':<20}")
    print("-" * 60)
    print(f"{'Capital Inicial':<40} ${capital_inicial:,.2f}")
    print(f"{'Winrate (%)':<40} {winrate:.2f}%")
    print(f"{'R-Multiplicador':<40} {r_multiple:.2f}")
    print(
        f"{'T. Posicion (%)':<40} {(capital_final / capital_inicial * 100) if capital_inicial > 0 else 0:.2f}%"
    )
    print(f"{'Trades':<40} {total_trades}")
    print(f"{'Expectancy':<40} ${expectancy:,.2f}")
    print(f"{'Kelly Criterion':<40} {kelly*100:.2f}%")
    print(f"{'Riesgo de Ruina':<40} {riesgo_ruina*100:.2f}%")
    print(
        f"{'Probabilidad de Pérdidas Consecutivas':<40} {prob_perdidas_consecutivas*100:.4f}%"
    )

    print("\nINDICADORES PROBABILÍSTICOS")
    print("=" * 60)
    print(f"{'Parámetro':<40} {'Valor':<20}")
    print("-" * 60)
    print(f"{'Probabilidad de éxito (P_win)':<40} {p_win:.4f}")
    print(f"{'Ganancia esperada por operación (R_win)':<40} ${ganancia_media:,.2f}")
    print(f"{'Probabilidad de pérdida (P_loss)':<40} {p_loss:.4f}")
    print(f"{'Pérdida esperada por operación (R_loss)':<40} ${perdida_media:,.2f}")
    print(f"{'Asimetría de información (A)':<40} {asimetria:.4f}")
    print(f"{'Equilibrio de Nash (N)':<40} {nash_equilibrio:.4f}")
    print(f"{'Relación Riesgo/Beneficio (R/B)':<40} {relacion_rb:.4f}")
    print(f"{'Esperanza Matemática (E)':<40} ${esperanza_matematica:,.2f}")
    print(f"{'Puntuación Final (S)':<40} {score:.4f}")

    print("\nRESULTADOS DE TRADING")
    print("=" * 60)
    print(f"{'Parámetro':<40} {'Valor':<20}")
    print("-" * 60)
    print(f"{'Beneficio Bruto':<40} ${beneficio_bruto:,.2f}")
    print(f"{'Beneficio neto':<40} ${beneficio_neto:,.2f}")
    print(f"{'Maximo Drawdown':<40} {max_dd_value*100:.2f}%")
    print(f"{'Recovery factor':<40} {recovery_factor:.2f}")
    print(f"{'Suma operaciones con ganancia':<40} ${beneficio_bruto:,.2f}")
    print(f"{'Suma operaciones con perdidas':<40} ${perdida_bruta:,.2f}")
    print(f"{'Profit factor':<40} {profit_factor:.2f}")
    print(f"{'Total de operaciones con ganancia':<40} {total_ganadores}")
    print(f"{'Total de operaciones con pérdidas':<40} {total_perdedores}")
    print(f"{'Porcentaje de aciertos':<40} {winrate:.2f}%")
    print(f"{'Media resultados operaciones':<40} ${media_resultados:,.2f}")

    return {
        "capital_inicial": capital_inicial,
        "winrate": winrate,
        "r_multiple": r_multiple,
        "t_posicion": (
            (capital_final / capital_inicial * 100) if capital_inicial > 0 else 0
        ),
        "trades": total_trades,
        "expectancy": expectancy,
        "kelly": kelly,
        "riesgo_ruina": riesgo_ruina,
        "prob_perdidas_consecutivas": prob_perdidas_consecutivas,
        "p_win": p_win,
        "ganancia_media": ganancia_media,
        "p_loss": p_loss,
        "perdida_media": perdida_media,
        "asimetria": asimetria,
        "nash_equilibrio": nash_equilibrio,
        "relacion_rb": relacion_rb,
        "esperanza_matematica": esperanza_matematica,
        "score": score,
        "beneficio_bruto": beneficio_bruto,
        "beneficio_neto": beneficio_neto,
        "max_dd": max_dd_value,
        "recovery_factor": recovery_factor,
        "profit_factor": profit_factor,
        "total_ganadores": total_ganadores,
        "total_perdedores": total_perdedores,
        "media_resultados": media_resultados,
    }


def generar_reporte_html(
    df_res,
    df_val,
    df_cost,
    metrics,
    kpis,
    bonos_data,
    letras_data,
    tipos_data,
    filename="reporte_cartera.html",
):
    """Genera un reporte HTML autocontenido con gráficos y tablas."""
    print(f"\n📄 Generando reporte en {filename}...")

    # 1. Generar gráficos y convertirlos a Base64
    def plot_to_base64(plot_func, *args, **kwargs):
        buffer = BytesIO()
        plot_func(*args, **kwargs, save_path=buffer)
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{img_str}"

    imgs = {}
    imgs["dashboard"] = plot_to_base64(plot_dashboard, df_res)
    imgs["composicion"] = plot_to_base64(plot_composicion_cartera, df_val)
    imgs["drawdown"] = plot_to_base64(plot_drawdown, df_res)
    imgs["retornos"] = plot_to_base64(plot_retornos_distribucion, df_res)
    if df_val.shape[1] > 1:
        imgs["correlacion"] = plot_to_base64(plot_correlacion_activos, df_val)
    imgs["por_tipo"] = plot_to_base64(plot_rendimiento_por_tipo, df_val, df_cost)
    imgs["normalizado"] = plot_to_base64(plot_rendimiento_normalizado, df_val, df_cost)
    imgs["kpis_tiempo"] = plot_to_base64(plot_kpis_tiempo, df_res)

    # 2. Template HTML (Simplificado para evitar dependencias externas pesadas si Jinja2 fallara)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Cartera - {df_res.index[-1].strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f4f7f9; color: #333; }}
            .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1, h2, h3 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .card {{ background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
            .metric {{ font-size: 24px; font-weight: bold; color: #2980b9; }}
            .metric-label {{ font-size: 14px; color: #7f8c8d; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; }}
            tr:hover {{ background-color: #f1f1f1; }}
            .img-container {{ text-align: center; margin: 20px 0; }}
            img {{ max-width: 100%; height: auto; border-radius: 8px; }}
            .pos-val {{ color: green; }}
            .neg-val {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Reporte de Análisis de Cartera</h1>
            <p>Generado el: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
            
            <h2>Resumen Ejecutivo</h2>
            <div class="grid">
                <div class="card">
                    <div class="metric-label">Valor Total Cartera</div>
                    <div class="metric">${df_res['Total_Value'].iloc[-1]:,.2f}</div>
                </div>
                <div class="card">
                    <div class="metric-label">Inversión Total</div>
                    <div class="metric">${df_res['Total_Invested'].iloc[-1]:,.2f}</div>
                </div>
                <div class="card">
                    <div class="metric-label">Resultado Neto</div>
                    <div class="metric {'pos-val' if kpis['beneficio_neto'] >= 0 else 'neg-val'}">
                        ${kpis['beneficio_neto']:,.2f} ({ (kpis['beneficio_neto']/df_res['Total_Invested'].iloc[-1]*100) if df_res['Total_Invested'].iloc[-1] > 0 else 0:+.2f}%)
                    </div>
                </div>
                <div class="card">
                    <div class="metric-label">Ratio de Sharpe</div>
                    <div class="metric">{metrics.get('sharpe', 0):.2f}</div>
                </div>
            </div>

            <div class="img-container">
                <h3>Dashboard de Rendimiento</h3>
                <img src="{imgs['dashboard']}" alt="Dashboard">
            </div>

            <h2>Métricas de Riesgo</h2>
            <div class="grid">
                <div class="card">
                    <ul>
                        <li><strong>Volatilidad Anual:</strong> {metrics.get('volatilidad', 0)*100:.2f}%</li>
                        <li><strong>Máximo Drawdown:</strong> {metrics.get('max_drawdown', 0)*100:.2f}%</li>
                        <li><strong>Profit Factor:</strong> {kpis['profit_factor']:.2f}</li>
                    </ul>
                </div>
                <div class="card">
                    <ul>
                        <li><strong>Win Rate:</strong> {kpis['winrate']:.2f}%</li>
                        <li><strong>Kelly Criterion:</strong> {kpis['kelly']*100:.2f}%</li>
                        <li><strong>Recovery Factor:</strong> {kpis['recovery_factor']:.2f}</li>
                    </ul>
                </div>
            </div>

            <div class="grid">
                <div class="img-container">
                    <h3>Composición de Cartera</h3>
                    <img src="{imgs['composicion']}" alt="Composicion">
                </div>
                <div class="img-container">
                    <h3>Drawdown Histórico</h3>
                    <img src="{imgs['drawdown']}" alt="Drawdown">
                </div>
            </div>

            <h2>Análisis por Tipo de Activo</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tipo</th>
                        <th>Valor Mercado</th>
                        <th>% Cartera</th>
                        <th>Rendimiento</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td>{t['tipo'].capitalize()}</td><td>${t['valor']:,.2f}</td><td>{t['peso']:.2f}%</td><td class='{'pos-val' if t['rendimiento'] >= 0 else 'neg-val'}'>{t['rendimiento']:.2f}%</td></tr>" for t in tipos_data])}
                </tbody>
            </table>

            <div class="img-container">
                <h3>Evolución por Tipo</h3>
                <img src="{imgs['por_tipo']}" alt="Evolucion por tipo">
            </div>

            <h2>Detalle de Activos</h2>
            
            {"<h3>Renta Fija (Bonos)</h3>" if bonos_data.get('detalle') else ""}
            {"<table><thead><tr><th>Ticker</th><th>Cantidad</th><th>Precio</th><th>Valor Mercado</th><th>Paridad</th></tr></thead><tbody>" if bonos_data.get('detalle') else ""}
            {"".join([f"<tr><td>{d['ticker']}</td><td>{d['cantidad']:,}</td><td>{d['precio']:.2f}</td><td>${d['valor']:,.2f}</td><td>{d['paridad']:.2f}%</td></tr>" for d in bonos_data.get('detalle', [])])}
            {"</tbody></table>" if bonos_data.get('detalle') else ""}

            {"<h3>Letras del Tesoro</h3>" if letras_data.get('detalle') else ""}
            {"<table><thead><tr><th>Ticker</th><th>Cantidad</th><th>Precio</th><th>Valor Mercado</th><th>Paridad</th></tr></thead><tbody>" if letras_data.get('detalle') else ""}
            {"".join([f"<tr><td>{d['ticker']}</td><td>{d['cantidad']:,}</td><td>{d['precio']:.4f}</td><td>${d['valor']:,.2f}</td><td>{d['paridad']:.2f}%</td></tr>" for d in letras_data.get('detalle', [])])}
            {"</tbody></table>" if letras_data.get('detalle') else ""}

            <h2>Análisis Probabilístico de Trading</h2>
            <table>
                <tr><td>Expectativa por Operación</td><td>${kpis['expectancy']:,.2f}</td><td>Asimetría</td><td>{kpis['asimetria']:.4f}</td></tr>
                <tr><td>Riesgo de Ruina</td><td>{kpis['riesgo_ruina']*100:.2f}%</td><td>Equilibrio de Nash</td><td>{kpis['nash_equilibrio']:.4f}</td></tr>
                <tr><td>Puntuación Final (Score)</td><td>{kpis['score']:.4f}</td><td>Relación R/B</td><td>{kpis['relacion_rb']:.4f}</td></tr>
            </table>

            <div class="img-container">
                <h3>Distribución de Retornos</h3>
                <img src="{imgs['retornos']}" alt="Retornos">
            </div>

            <div class="img-container">
                <h3>KPIs en el Tiempo</h3>
                <img src="{imgs['kpis_tiempo']}" alt="KPIs tiempo">
            </div>

            <div class="img-container">
                <h3>Rendimiento Normalizado</h3>
                <img src="{imgs['normalizado']}" alt="Normalizado">
            </div>
            
            {f'<div class="img-container"><h3>Mapa de Correlación</h3><img src="{imgs["correlacion"]}" alt="Correlacion"></div>' if 'correlacion' in imgs else ''}

        </div>
        <footer style="text-align: center; margin-top: 50px; color: #7f8c8d; font-size: 0.8em;">
            Reporte generado automáticamente por script de análisis de cartera.
        </footer>
    </body>
    </html>
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Reporte guardado exitosamente.")
    return filename


# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    # 1. Procesamiento
    df_res, df_val, df_cost = procesar_cartera(MI_CARTERA)

    if not df_res.empty:
        # 2. Visualización Principal (Consola)
        plot_dashboard(df_res)

        # 3. Métricas
        metrics = calcular_metricas_riesgo(df_val, df_res)
        print("\n===== MÉTRICAS DE RIESGO =====")
        print(f"Volatilidad Anualizada: {metrics.get('volatilidad', 0) * 100:.2f}%")
        print(f"Máximo Drawdown: {metrics.get('max_drawdown', 0) * 100:.2f}%")
        print(f"Ratio de Sharpe: {metrics.get('sharpe', 0):.2f}")

        # 4. KPIs de Trading
        kpis = calcular_kpi_trading(df_res)

        # 5. Análisis específicos
        bonos_info = analizar_bonos(df_val, df_cost)
        letras_info = analizar_letras_tesoro(df_val, df_cost)
        tipos_info = analizar_rendimiento_por_tipo(df_val, df_cost)
        plot_composicion_cartera(df_val)

        # 6. Nuevos gráficos avanzados (Consola)
        print("\n===== VISUALIZACIONES AVANZADAS =====")
        plot_drawdown(df_res)
        plot_retornos_distribucion(df_res)

        # Solo mostrar correlación si hay suficientes activos
        if df_val.shape[1] > 1:
            plot_correlacion_activos(df_val)

        plot_rendimiento_por_tipo(df_val, df_cost)
        plot_rendimiento_normalizado(df_val, df_cost)
        plot_kpis_tiempo(df_res)

        # 7. Generación de Reporte HTML
        generar_reporte_html(
            df_res, df_val, df_cost, metrics, kpis, bonos_info, letras_info, tipos_info
        )

        # 8. Contexto VIX (Si el módulo existe)
        if TradingVIX:
            print("\n===== CONTEXTO DE MERCADO (VIX) =====")
            try:
                vix = TradingVIX()
                print("Analizando volatilidad implícita...")
                # Aquí iría la llamada real a tu módulo VIX
            except Exception as e:
                print(f"Error en módulo VIX: {e}")
    else:
        print("❌ Error crítico: No se pudieron generar datos.")
