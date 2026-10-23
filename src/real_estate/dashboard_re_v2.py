"""
Real estate macro analysis — CABA (Buenos Aires) housing cycles.

Generates a self-contained HTML report covering 50 years of USD/m2 prices,
the UVA/CCL dollar ratio, a salary-based affordability (effort) index, and a
Monte Carlo projection of the UVA ratio. Data sources: consolidated CABA m2
history (Reporte Inmobiliario, UCEMA - RE/MAX, DeInmobiliarios), live public
APIs (ArgentinaDatos: UVA + CCL; SSPM/Datos.gob.ar: RIPTE salaries).

The report is regenerated and published to GitHub Pages by CI, so the live
version always reflects fresh market data.

Usage: python src/real_estate/dashboard_re_v2.py
"""
import base64
import io
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import zscore

# Forzar UTF-8 en consola de Windows para evitar errores con caracteres especiales
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# Bootstrap sys.path BEFORE importing 'src' — otherwise the import below only
# resolves when the project root is already on the path (as on the dev machine)
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils import network  # noqa: E402

# --- CONFIGURACIÓN DE USUARIO ---
TNA_BANCO = 6
DIAS_PROYECCION = 365
NUM_SIMULACIONES = 200  # shortcut: unseeded RNG — the cloud differs run to run; seed it if you need reproducible reports
GENERAR_INFORME_HTML = True
OPEN_IN_BROWSER = False  # CI/Pages runs headless; flip locally to preview
MOSTRAR_PLOTS_INTERACTIVOS = False  # True para abrir ventanas GUI de matplotlib

# Configuración visual
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.dpi"] = 100

# Colores y Estilos Profesionales
C_AZUL = "#1f77b4"
C_ROJO = "#d62728"
C_VERDE = "#2ca02c"
C_NARANJA = "#E26B0A"
C_ESFUERZO = "#8c564b"  # Marrón/Bronce
C_GRIS_BANDA = "#D9D9D9"  # Color para el rango 25-75%


# --- 1. CARGA DE DATOS ---
def obtener_datos_propiedades():
    """
    Datos históricos m2 CABA (1977-2026).
    Fuentes consolidadas: Reporte Inmobiliario, UCEMA - RE/MAX y red deInmobiliarios.
    """
    data = {
        "Año": [
            1977,
            1978,
            1979,
            1980,
            1981,
            1982,
            1983,
            1984,
            1985,
            1989,
            1990,
            1991,
            1992,
            1993,
            1994,
            1995,
            1996,
            1997,
            1998,
            1999,
            2000,
            2001,
            2002,
            2003,
            2004,
            2005,
            2006,
            2007,
            2008,
            2009,
            2010,
            2011,
            2012,
            2013,
            2014,
            2015,
            2016,
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
            2026,
        ],
        "Precio_m2": [
            1700,
            2011,
            2203,
            2321,
            4574,
            2850,
            1349,
            1231,
            1100,
            1083,
            1615,
            2113,
            2222,
            2300,
            2250,
            2200,
            2150,
            2100,
            2050,
            1950,
            1807,
            1500,
            1066,
            1425,
            1637,
            1800,
            2000,
            2100,
            2052,
            2150,
            2207,
            2348,
            2502,
            2477,
            2799,
            3131,
            3387,
            3605,
            3120,
            2752,
            2578,
            2361,
            1931,
            1837,
            1988,
            2200,
            2150,
        ],
    }
    df = pd.DataFrame(data)
    df["Año"] = pd.to_datetime(df["Año"], format="%Y")
    df.set_index("Año", inplace=True)
    df.sort_index(inplace=True)
    return df


def descargar_financieros_full():
    print(">>> Descargando datos financieros y salariales...")
    try:
        # 1. Cotizaciones
        df_uva = pd.DataFrame(
            network.get(
                "https://api.argentinadatos.com/v1/finanzas/indices/uva", timeout=15
            ).json()
        )
        df_ccl = pd.DataFrame(
            network.get(
                "https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui",
                timeout=15,
            ).json()
        )

        df_uva["fecha"] = pd.to_datetime(df_uva["fecha"])
        df_uva.set_index("fecha", inplace=True)
        df_ccl["fecha"] = pd.to_datetime(df_ccl["fecha"])
        df_ccl.set_index("fecha", inplace=True)

        # 2. Salarios (RIPTE)
        urls_ripte = [
            "https://infra.datos.gob.ar/catalog/sspm/dataset/158/distribution/158.1/download/remuneracion-imponible-promedio-trabajadores-estables-ripte-total-pais-pesos-serie-mensual.csv",
            "https://infra.datos.gob.ar/catalog/sspm/dataset/172/distribution/172.1/download/remuneracion-imponible-promedio-trabajadores-estables-ripte-total-pais-pesos-serie-mensual.csv",
        ]
        df_ripte = pd.DataFrame()
        for url in urls_ripte:
            try:
                r = network.get(url, timeout=5)
                if r.status_code == 200:
                    df_ripte = pd.read_csv(
                        io.StringIO(r.text), parse_dates=["indice_tiempo"]
                    )
                    df_ripte = df_ripte.set_index("indice_tiempo").sort_index()
                    col = [
                        c
                        for c in df_ripte.columns
                        if "monto" in c or "ripte" in c.lower()
                    ][0]
                    df_ripte = df_ripte[[col]].rename(columns={col: "RIPTE"})
                    break
            except Exception:
                continue

        if df_ripte.empty:
            print("[WARN] RIPTE no disponible — el informe se publicará sin el índice de esfuerzo")

        # 3. Fusión de datos
        df = df_uva.join(df_ccl[["venta"]], how="inner").rename(
            columns={"valor": "UVA", "venta": "CCL"}
        )
        df = df[df.index >= "2016-01-01"].dropna()
        df["Ratio"] = df["UVA"] / df["CCL"]

        if not df_ripte.empty:
            # Resample mensual para cruzar con salarios
            df_m = df.resample("MS").mean()
            df_ripte_aligned = (
                df_ripte.reindex(df_ripte.index.union(df_m.index))
                .ffill()
                .reindex(df_m.index)
            )
            df_m = df_m.join(df_ripte_aligned)
            df_m["Var_UVA"] = df_m["UVA"].pct_change(12) * 100
            df_m["Var_RIPTE"] = df_m["RIPTE"].pct_change(12) * 100
            df_m["Salario_USD"] = df_m["RIPTE"] / df_m["CCL"]
            df_m.dropna(inplace=True)
            return df, df_m
        return df, pd.DataFrame()

    except Exception as e:
        print(f"Error de descarga: {e}")
        return pd.DataFrame(), pd.DataFrame()


# --- 2. CÁLCULOS AVANZADOS Y ESTADÍSTICA ---
def enriquecer_estadisticas(df, col):
    """
    Agrega Z-Score, Mediana, Percentiles y Drawdown al DataFrame.
    """
    if df.empty:
        return df

    # Z-Score (Desvíos estándar respecto a la media)
    df["Z_Score"] = zscore(df[col], nan_policy="omit")

    # Estadísticas Robusta
    df["Mediana"] = df[col].median()
    df["P25"] = df[col].quantile(0.25)
    df["P75"] = df[col].quantile(0.75)

    # Drawdown (Caída desde el máximo histórico hasta el punto actual)
    rolling_max = df[col].cummax()
    df["Drawdown"] = ((df[col] - rolling_max) / rolling_max) * 100

    return df


def calcular_montecarlo(df_main):
    if df_main.empty:
        return None, None, None, None
    log_ret = np.log(df_main["Ratio"] / df_main["Ratio"].shift(1)).dropna()
    u, var = log_ret.mean(), log_ret.var()
    drift, stdev = u - (0.5 * var), log_ret.std()

    fechas_fut = pd.date_range(df_main.index[-1], periods=DIAS_PROYECCION, freq="D")

    if NUM_SIMULACIONES > 0:
        rutas = np.zeros((DIAS_PROYECCION, NUM_SIMULACIONES))
        rutas[0] = df_main["Ratio"].iloc[-1]
        for t in range(1, DIAS_PROYECCION):
            rutas[t] = rutas[t - 1] * np.exp(
                drift + stdev * np.random.normal(0, 1, NUM_SIMULACIONES)
            )
        return fechas_fut, rutas, rutas.mean(axis=1), np.median(rutas, axis=1)

    return fechas_fut, None, None, None


def calcular_indice_esfuerzo(df_m2, df_salarios):
    if df_salarios.empty:
        return pd.DataFrame()
    df_m2_mensual = (
        df_m2.reindex(df_m2.index.union(df_salarios.index))
        .ffill()
        .reindex(df_salarios.index)
    )
    df_esf = df_salarios[["Salario_USD"]].join(df_m2_mensual, how="inner")
    df_esf["Esfuerzo"] = df_esf["Precio_m2"] / df_esf["Salario_USD"]
    return df_esf


def solicitar_eventos():
    eventos = []
    # (Input simplificado para no bloquear la ejecución automática)
    return eventos


# --- 3. MOTORES DE PLOTEO (DECISION GRADE) ---
def agregar_caja_estadisticas(ax, df, col, etiqueta):
    """Agrega un cuadro flotante con métricas clave"""
    if df.empty:
        return

    curr_val = df[col].iloc[-1]
    z_score = df["Z_Score"].iloc[-1]
    drawdown = df["Drawdown"].iloc[-1]
    mediana = df[col].median()

    stats_text = (
        f"{etiqueta} Actual: {curr_val:.2f}\n"
        f"Z-Score: {z_score:.2f}σ\n"
        f"Drawdown: {drawdown:.1f}%\n"
        f"-----------------\n"
        f"Mediana Hist: {mediana:.2f}\n"
        f"Rango 25-75%: {df['P25'].iloc[-1]:.0f} - {df['P75'].iloc[-1]:.0f}"
    )

    # Color de borde según Z-Score (Alerta)
    edge_c = "red" if abs(z_score) > 2 else "gray"

    props = dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor=edge_c)
    ax.text(
        0.02,
        0.95,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=props,
        fontfamily="monospace",
    )


def plot_vertical_lines(ax, eventos, df_ref):
    if df_ref.empty:
        return
    ylim = ax.get_ylim()
    for ev in eventos:
        if df_ref.index.min() <= ev["fecha"] <= df_ref.index.max():
            ax.axvline(ev["fecha"], color=ev["color"], ls="--", lw=1.5)
            ax.text(
                ev["fecha"],
                ylim[1],
                f" {ev['label']}",
                rotation=90,
                va="top",
                fontweight="bold",
                color=ev["color"],
                fontsize=8,
                backgroundcolor="#ffffff99",
            )


def plot_inmuebles(ax, df, eventos):
    df = enriquecer_estadisticas(df, "Precio_m2")

    # Banda de Normalidad (25-75%)
    ax.fill_between(
        df.index,
        df["P25"],
        df["P75"],
        color=C_GRIS_BANDA,
        alpha=0.4,
        label="Zona Normalidad (25-75%)",
    )

    ax.plot(
        df.index,
        df["Precio_m2"],
        marker="o",
        markersize=4,
        lw=2,
        color=C_AZUL,
        label="Precio m2",
    )

    # Métricas Robustas
    ax.axhline(
        df["Mediana"].iloc[-1],
        color=C_NARANJA,
        ls="-.",
        lw=1.5,
        label="Mediana Histórica",
    )
    std = df["Precio_m2"].std()
    mean = df["Precio_m2"].mean()
    # (Opcional) Bandas de desviación estándar
    # ax.axhline(mean + std, color=C_ROJO, ls=':', lw=1, label='+1 SD')
    # ax.axhline(mean - std, color=C_VERDE, ls=':', lw=1, label='-1 SD')

    for i in range(1, len(df)):
        val = df["Precio_m2"].iloc[i]
        pct = ((val / df["Precio_m2"].iloc[i - 1]) - 1) * 100
        offset = 180 if i % 2 == 0 else -180
        col = C_VERDE if pct >= 0 else C_ROJO
        ax.text(
            df.index[i],
            val + offset,
            f"{pct:+.0f}%",
            ha="center",
            fontsize=7,
            color=col,
            fontweight="bold",
        )

    # Ciclos Grandes (Badges)
    ciclos = [
        (1977, 1981),
        (1981, 1989),
        (1989, 1993),
        (2002, 2018),
        (2018, 2023),
        (2023, 2026),
    ]
    for ini, fin in ciclos:
        try:
            idx_i = df.index.get_indexer(
                [pd.to_datetime(f"{ini}-01-01")], method="nearest"
            )[0]
            idx_f = df.index.get_indexer(
                [pd.to_datetime(f"{fin}-01-01")], method="nearest"
            )[0]
            v_i, v_f = df["Precio_m2"].iloc[idx_i], df["Precio_m2"].iloc[idx_f]
            pct_tot = ((v_f / v_i) - 1) * 100
            mid_d = df.index[idx_i + (idx_f - idx_i) // 2]
            mid_v = (v_i + v_f) / 2
            col_bg = C_VERDE if pct_tot > 0 else C_ROJO
            ax.annotate(
                f"{pct_tot:+.0f}%",
                xy=(mid_d, mid_v),
                xytext=(mid_d, mid_v),
                fontsize=11,
                color="white",
                fontweight="bold",
                ha="center",
                bbox=dict(boxstyle="round,pad=0.3", fc=col_bg, alpha=0.8),
            )
        except Exception:
            pass

    agregar_caja_estadisticas(ax, df, "Precio_m2", "Precio")
    plot_vertical_lines(ax, eventos, df)

    # Mejorar capilaridad del eje X: Mostrar cada 2 años + el último año registrado
    años_ticks = df.index[::2].tolist()
    if df.index[-1] not in años_ticks:
        años_ticks.append(df.index[-1])
    ax.set_xticks(años_ticks)
    ax.set_xticklabels([x.strftime("%Y") for x in años_ticks], rotation=45, ha="right")

    ax.set_title(
        "1. VALUACIÓN: Precio Histórico Ajustado", fontsize=12, fontweight="bold"
    )
    ax.legend(loc="best", frameon=True)
    ax.grid(True, alpha=0.3)


def plot_ratio(ax, df, fut, rutas, media_mc, med_mc, eventos):
    df = enriquecer_estadisticas(df, "Ratio")

    if fut is not None:
        if rutas is not None:
            ax.plot(fut, rutas, color="gray", alpha=0.05)
        if media_mc is not None and med_mc is not None:
            ax.plot(fut, media_mc, "k:", lw=2, label="Proy. Media")
            ax.plot(fut, med_mc, color=C_NARANJA, ls="--", lw=2, label="Proy. Mediana")

    # Bandas de Normalidad
    ax.fill_between(
        df.index,
        df["P25"],
        df["P75"],
        color=C_GRIS_BANDA,
        alpha=0.4,
        label="Zona Normalidad (25-75%)",
    )

    ax.plot(df.index, df["Ratio"], color=C_AZUL, label="Ratio UVA/CCL")
    ax.axhline(
        df["Mediana"].iloc[-1],
        color=C_NARANJA,
        ls="-.",
        lw=1.5,
        label="Mediana Histórica",
    )

    # Umbrales Sigma (Z-Score implícito)
    std = df["Ratio"].std()
    mean = df["Ratio"].mean()
    ax.axhline(
        mean + std,
        c=C_ROJO,
        ls="--",
        lw=1,
        label="+1 Sigma (Caro) - Buen Momento para Tomar UVA, No para Cancelar",
    )
    ax.axhline(
        mean - std,
        c=C_VERDE,
        ls="--",
        lw=1,
        label="-1 Sigma (Barato) - Mal Momento para Tomar UVA, Excelente para Cancelar",
    )

    ax.fill_between(
        df.index,
        df["Ratio"],
        mean + std,
        where=df["Ratio"] > mean + std,
        color=C_ROJO,
        alpha=0.2,
    )
    ax.fill_between(
        df.index,
        df["Ratio"],
        mean - std,
        where=df["Ratio"] < mean - std,
        color=C_VERDE,
        alpha=0.2,
    )

    agregar_caja_estadisticas(ax, df, "Ratio", "Ratio")
    plot_vertical_lines(ax, eventos, df)
    ax.set_title("2. FINANCIERO: Ratio UVA / CCL", fontsize=12, fontweight="bold")
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)


def plot_solvencia(ax, df):
    ax.plot(df.index, df["Var_UVA"], color=C_ROJO, label="Inflación Deuda")
    ax.plot(df.index, df["Var_RIPTE"], color=C_VERDE, label="Aumento Sueldos")
    ax.plot(
        df.index,
        df["Var_UVA"] + TNA_BANCO,
        color="darkred",
        ls=":",
        alpha=0.5,
        label="Costo Total",
    )

    ax.fill_between(
        df.index,
        df["Var_UVA"],
        df["Var_RIPTE"],
        where=df["Var_UVA"] > df["Var_RIPTE"],
        color="red",
        alpha=0.3,
    )
    ax.fill_between(
        df.index,
        df["Var_UVA"],
        df["Var_RIPTE"],
        where=df["Var_UVA"] <= df["Var_RIPTE"],
        color="green",
        alpha=0.15,
    )

    ax.set_title("3. SOLVENCIA: Salarios vs Cuota", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)


def plot_buying_power(ax, df, eventos):
    df = enriquecer_estadisticas(df, "Salario_USD")

    # Bandas
    ax.fill_between(
        df.index,
        df["P25"],
        df["P75"],
        color=C_GRIS_BANDA,
        alpha=0.4,
        label="Zona Normalidad",
    )

    ax.plot(df.index, df["Salario_USD"], color="navy", label="Sueldo RIPTE (USD)")
    ax.axhline(
        df["Mediana"].iloc[-1],
        color=C_NARANJA,
        ls="-.",
        lw=1.5,
        label="Mediana Histórica",
    )

    # Umbrales Sigma
    std = df["Salario_USD"].std()
    mean = df["Salario_USD"].mean()
    ax.axhline(mean + std, c=C_VERDE, ls="--", lw=1, label="+1 Sigma (Alto)")
    ax.axhline(mean - std, c=C_ROJO, ls="--", lw=1, label="-1 Sigma (Bajo)")
    ax.fill_between(
        df.index,
        df["Salario_USD"],
        mean + std,
        where=df["Salario_USD"] > mean + std,
        color=C_VERDE,
        alpha=0.2,
    )
    ax.fill_between(
        df.index,
        df["Salario_USD"],
        mean - std,
        where=df["Salario_USD"] < mean - std,
        color=C_ROJO,
        alpha=0.2,
    )

    agregar_caja_estadisticas(ax, df, "Salario_USD", "Sueldo USD")
    plot_vertical_lines(ax, eventos, df)
    ax.set_title("4. PODER DE COMPRA: Ripte en Dólares", fontsize=12, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)


def plot_esfuerzo(ax, df, eventos):
    df = enriquecer_estadisticas(df, "Esfuerzo")

    ax.plot(df.index, df["Esfuerzo"], color=C_ESFUERZO, lw=2, label="Salarios por m2")
    mu = df["Esfuerzo"].mean()
    ax.axhline(mu, color=C_NARANJA, ls="-.", label=f"Promedio Hist. ({mu:.1f})")
    ax.fill_between(
        df.index,
        df["Esfuerzo"],
        mu,
        where=df["Esfuerzo"] > mu,
        color="red",
        alpha=0.1,
        label="Inaccesible",
    )
    ax.fill_between(
        df.index,
        df["Esfuerzo"],
        mu,
        where=df["Esfuerzo"] < mu,
        color="green",
        alpha=0.1,
        label="Oportunidad",
    )

    agregar_caja_estadisticas(ax, df, "Esfuerzo", "Esfuerzo")
    plot_vertical_lines(ax, eventos, df)
    ax.set_title(
        "5. ACCESIBILIDAD: Índice de Esfuerzo (Sueldos para 1 m2)",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_ylabel("Sueldos Enteros")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)


# --- 4. GENERADOR DE INFORME HTML EJECUTIVO ---
def fig_to_base64_png(fig, dpi=120):
    """Convierte una figura de matplotlib en string base64 PNG para incrustar en HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_b64


def generar_informe_html(
    df_m2,
    df_fin,
    df_mensual,
    df_esfuerzo,
    fechas_fut,
    rutas_mc,
    media_mc,
    mediana_mc,
    eventos_usuario,
    output_filename="informe_inmobiliario_macro.html",
):
    """
    Genera un informe institucional autónomo en HTML sobre la situación
    inmobiliaria de CABA y el contexto macroeconómico argentino.
    """
    print("\n>>> Renderizando gráficos para el informe HTML...")

    # 1. Gráficos Individuales a Base64
    fig1, ax1 = plt.subplots(figsize=(14, 7))
    plot_inmuebles(ax1, df_m2, eventos_usuario)
    fig1.tight_layout()
    img_inmuebles = fig_to_base64_png(fig1)

    fig2, ax2 = plt.subplots(figsize=(14, 7))
    plot_ratio(ax2, df_fin, fechas_fut, rutas_mc, media_mc, mediana_mc, eventos_usuario)
    fig2.tight_layout()
    img_ratio = fig_to_base64_png(fig2)

    img_solvencia = ""
    img_buying_power = ""
    if not df_mensual.empty:
        fig3, ax3 = plt.subplots(figsize=(14, 7))
        plot_solvencia(ax3, df_mensual)
        fig3.tight_layout()
        img_solvencia = fig_to_base64_png(fig3)

        fig4, ax4 = plt.subplots(figsize=(14, 7))
        plot_buying_power(ax4, df_mensual, eventos_usuario)
        fig4.tight_layout()
        img_buying_power = fig_to_base64_png(fig4)

    img_esfuerzo = ""
    if not df_esfuerzo.empty:
        fig5, ax5 = plt.subplots(figsize=(14, 7))
        plot_esfuerzo(ax5, df_esfuerzo, eventos_usuario)
        fig5.tight_layout()
        img_esfuerzo = fig_to_base64_png(fig5)

    # 2. Dashboard Maestro
    print(">>> Renderizando Dashboard maestro...")
    fig_dash = plt.figure(figsize=(20, 18))
    gs = fig_dash.add_gridspec(3, 2)
    ax_m1 = fig_dash.add_subplot(gs[0, :])
    plot_inmuebles(ax_m1, df_m2, eventos_usuario)

    plot_ratio(
        fig_dash.add_subplot(gs[1, 0]),
        df_fin,
        fechas_fut,
        rutas_mc,
        media_mc,
        mediana_mc,
        eventos_usuario,
    )
    if not df_mensual.empty:
        plot_solvencia(fig_dash.add_subplot(gs[1, 1]), df_mensual)
        plot_buying_power(fig_dash.add_subplot(gs[2, 0]), df_mensual, eventos_usuario)
        if not df_esfuerzo.empty:
            plot_esfuerzo(fig_dash.add_subplot(gs[2, 1]), df_esfuerzo, eventos_usuario)

    fig_dash.suptitle(
        "Tablero Integral Inmobiliario y Macroeconómico CABA",
        fontsize=22,
        weight="bold",
    )
    fig_dash.tight_layout(rect=[0, 0.02, 1, 0.98])
    img_dashboard = fig_to_base64_png(fig_dash, dpi=110)

    # 3. Métricas cuantitativas
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # M2
    m2_act = df_m2["Precio_m2"].iloc[-1]
    m2_prev = df_m2["Precio_m2"].iloc[-2]
    m2_var_pct = ((m2_act / m2_prev) - 1) * 100
    m2_mediana = df_m2["Mediana"].iloc[-1]
    m2_zscore = df_m2["Z_Score"].iloc[-1]
    m2_dd = df_m2["Drawdown"].iloc[-1]
    m2_p25 = df_m2["P25"].iloc[-1]
    m2_p75 = df_m2["P75"].iloc[-1]
    m2_max_hist = df_m2["Precio_m2"].max()
    m2_min_piso_2023 = 1837
    m2_rebote = ((m2_act / m2_min_piso_2023) - 1) * 100

    # Ratio UVA/CCL
    ratio_act = df_fin["Ratio"].iloc[-1]
    ratio_mediana = df_fin["Mediana"].iloc[-1]
    ratio_media = df_fin["Ratio"].mean()
    ratio_std = df_fin["Ratio"].std()
    ratio_zscore = df_fin["Z_Score"].iloc[-1]
    ratio_sigma_sup = ratio_media + ratio_std
    ratio_sigma_inf = ratio_media - ratio_std

    if ratio_act >= ratio_sigma_sup:
        diag_ratio_badge = (
            "background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171;"
        )
        diag_ratio_txt = "BANDA ALTA (+1σ) — DEUDA EN USD CARA"
        diag_ratio_desc = "La deuda en UVA está en máximos en términos de dólares CCL. Favorable para tomar deuda si se espera devaluación futura; desfavorable para cancelar anticipadamente con dólares."
    elif ratio_act <= ratio_sigma_inf:
        diag_ratio_badge = (
            "background-color: #dcfce7; color: #166534; border: 1px solid #4ade80;"
        )
        diag_ratio_txt = "BANDA BAJA (-1σ) — DEUDA EN USD LICUADA"
        diag_ratio_desc = "La deuda en UVA está barata en dólares por salto cambiario. Excelente momento para prepagar cuotas o capital con dólares."
    else:
        diag_ratio_badge = (
            "background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d;"
        )
        diag_ratio_txt = "ZONA NEUTRAL / EQUILIBRIO"
        diag_ratio_desc = (
            "El ratio UVA/CCL opera dentro de la banda histórica de normalidad."
        )

    # Salarios
    sal_usd_act = df_mensual["Salario_USD"].iloc[-1] if not df_mensual.empty else 0
    sal_usd_med = df_mensual["Mediana"].iloc[-1] if not df_mensual.empty else 0
    sal_usd_zscore = df_mensual["Z_Score"].iloc[-1] if not df_mensual.empty else 0
    var_uva_act = df_mensual["Var_UVA"].iloc[-1] if not df_mensual.empty else 0
    var_ripte_act = df_mensual["Var_RIPTE"].iloc[-1] if not df_mensual.empty else 0
    costo_financiero_total = var_uva_act + TNA_BANCO
    brecha_solvencia = costo_financiero_total - var_ripte_act

    # Esfuerzo
    esf_act = df_esfuerzo["Esfuerzo"].iloc[-1] if not df_esfuerzo.empty else 0
    esf_media = df_esfuerzo["Esfuerzo"].mean() if not df_esfuerzo.empty else 0
    esf_zscore = df_esfuerzo["Z_Score"].iloc[-1] if not df_esfuerzo.empty else 0

    if esf_act < esf_media:
        diag_esf_badge = (
            "background-color: #dcfce7; color: #166534; border: 1px solid #4ade80;"
        )
        diag_esf_txt = "ZONA DE OPORTUNIDAD RELATIVA"
        diag_esf_desc = f"Se necesitan {esf_act:.2f} salarios formales por m2, inferior a la media histórica de {esf_media:.2f}."
    else:
        diag_esf_badge = (
            "background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171;"
        )
        diag_esf_txt = "ZONA DE ALTO ESFUERZO"
        diag_esf_desc = f"Se requieren {esf_act:.2f} salarios por m2, por encima de la media histórica de {esf_media:.2f}."

    # Brecha de solvencia
    if brecha_solvencia > 0:
        diag_solv_badge = (
            "background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171;"
        )
        diag_solv_txt = f"ALERTA DESCALCE ({brecha_solvencia:+.1f} p.p.)"
        diag_solv_desc = f"La cuota (UVA + {TNA_BANCO}% TNA: {costo_financiero_total:.1f}%) crece más rápido que los salarios formales (RIPTE: {var_ripte_act:.1f}%)."
    else:
        diag_solv_badge = (
            "background-color: #dcfce7; color: #166534; border: 1px solid #4ade80;"
        )
        diag_solv_txt = f"SOLVENCIA POSITIVA ({brecha_solvencia:+.1f} p.p.)"
        diag_solv_desc = (
            "Los salarios formales aumentan por encima del costo de la cuota bancaria."
        )

    # Ciclos de inmuebles
    ciclos_tabla = """
    <tr><td>1977 - 1981</td><td>Tablita Cambiaria Martínez de Hoz (Apreciación extrema)</td><td>$1,700</td><td>$4,574</td><td class="pos">+169%</td><td>Burbuja especulativa histórica</td></tr>
    <tr><td>1981 - 1989</td><td>Crisis de Deuda e Hiperinflación</td><td>$4,574</td><td>$1,083</td><td class="neg">-76%</td><td>Piso histórico en términos reales</td></tr>
    <tr><td>1989 - 1993</td><td>Estabilización inicial y Plan Bonex / Convertibilidad</td><td>$1,083</td><td>$2,300</td><td class="pos">+112%</td><td>Rebote veloz tras shock de confianza</td></tr>
    <tr><td>1993 - 2001</td><td>Convertibilidad 1 a 1</td><td>$2,300</td><td>$1,500</td><td class="neg">-35%</td><td>Efluvio deflacionario gradual</td></tr>
    <tr><td>2002 - 2018</td><td>Salida de Convertibilidad, Superciclo de Commodities y boom UVA Macri</td><td>$1,066</td><td>$3,605</td><td class="pos">+238%</td><td>Máximo moderno en CABA</td></tr>
    <tr><td>2018 - 2023</td><td>Crisis Cambiaria Macri, Pandemia, Cepo y Ley de Alquileres</td><td>$3,605</td><td>$1,837</td><td class="neg">-49%</td><td>Desplome de demanda y precios</td></tr>
    <tr><td>2023 - 2026</td><td>Desregulación DNU 70/23, Blanqueo y Reactivación Hipotecaria</td><td>$1,837</td><td>$2,150</td><td class="pos">+17%</td><td>Fase de recuperación y consolidación</td></tr>
    """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Informe Ejecutivo: Situación Inmobiliaria y Contexto Macro CABA</title>
<style>
    :root {{
        --bg-main: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --border-color: #e2e8f0;
        --accent-blue: #2563eb;
        --accent-emerald: #059669;
        --accent-rose: #dc2626;
        --accent-amber: #d97706;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        background-color: var(--bg-main);
        color: var(--text-primary);
        line-height: 1.6;
        padding: 30px 20px;
    }}
    .container {{
        max-width: 1300px;
        margin: 0 auto;
    }}
    .header {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 40px;
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }}
    .header-tag {{
        display: inline-block;
        background: rgba(37, 99, 235, 0.3);
        border: 1px solid rgba(59, 130, 246, 0.5);
        color: #93c5fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 15px;
    }}
    .header h1 {{
        font-size: 32px;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 12px;
    }}
    .header p {{
        font-size: 16px;
        color: #cbd5e1;
        max-width: 900px;
        margin-bottom: 20px;
    }}
    .meta-bar {{
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        font-size: 13px;
        color: #94a3b8;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 20px;
    }}
    .meta-item strong {{ color: #ffffff; }}

    /* KPI CARDS */
    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin-bottom: 35px;
    }}
    .kpi-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s, box-shadow 0.2s;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.06);
    }}
    .kpi-title {{
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-secondary);
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }}
    .kpi-value {{
        font-size: 30px;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1;
        margin-bottom: 8px;
    }}
    .kpi-sub {{
        font-size: 13px;
        color: var(--text-secondary);
        margin-bottom: 12px;
    }}
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }}

    /* DECISION MATRIX */
    .decision-section {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 30px;
        margin-bottom: 35px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    .section-title {{
        font-size: 22px;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .section-desc {{
        color: var(--text-secondary);
        font-size: 15px;
        margin-bottom: 25px;
    }}
    .decision-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px;
    }}
    .decision-box {{
        padding: 22px;
        border-radius: 10px;
        border-left: 5px solid;
    }}
    .decision-box.buy {{
        background: #f0fdf4;
        border-color: #16a34a;
    }}
    .decision-box.loan {{
        background: #fffbeb;
        border-color: #d97706;
    }}
    .decision-box.prep {{
        background: #fef2f2;
        border-color: #dc2626;
    }}
    .decision-box h3 {{
        font-size: 17px;
        font-weight: 700;
        margin-bottom: 10px;
    }}
    .decision-box.buy h3 {{ color: #15803d; }}
    .decision-box.loan h3 {{ color: #b45309; }}
    .decision-box.prep h3 {{ color: #b91c1c; }}
    .decision-box p {{
        font-size: 14px;
        color: var(--text-secondary);
        line-height: 1.5;
    }}

    /* REPORT BLOCKS */
    .report-card {{
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 30px;
        margin-bottom: 35px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    .report-card img {{
        width: 100%;
        height: auto;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin: 20px 0;
        display: block;
    }}
    .analysis-text {{
        font-size: 15px;
        color: var(--text-secondary);
        line-height: 1.7;
    }}
    .analysis-text p {{ margin-bottom: 14px; }}
    .analysis-text strong {{ color: var(--text-primary); }}

    /* TABLES */
    .table-container {{
        overflow-x: auto;
        margin: 20px 0;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        text-align: left;
    }}
    th {{
        background: #f1f5f9;
        color: var(--text-primary);
        font-weight: 700;
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
    }}
    td {{
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
        color: var(--text-secondary);
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    .pos {{ color: #16a34a; font-weight: 700; }}
    .neg {{ color: #dc2626; font-weight: 700; }}

    /* FOOTER */
    .footer {{
        text-align: center;
        padding: 40px 0 20px;
        color: var(--text-muted);
        font-size: 13px;
        border-top: 1px solid var(--border-color);
    }}
</style>
</head>
<body>
<div class="container">

    <!-- HEADER -->
    <header class="header">
        <span class="header-tag">Informe Estratégico y Cuantitativo</span>
        <h1>Situación Inmobiliaria CABA y Contexto Macroeconómico</h1>
        <p>Evaluación econométrica del metro cuadrado residencial, arbitraje cambiario de la deuda indexada (UVA vs CCL), poder de compra salarial en divisa (RIPTE) y accesibilidad patrimonial.</p>
        <div class="meta-bar">
            <div class="meta-item">Fecha de emisión: <strong>{now_str}</strong></div>
            <div class="meta-item">Horizonte analizado: <strong>1977 - 2026</strong></div>
            <div class="meta-item">Tasa Préstamo Simulación: <strong>UVA + {TNA_BANCO}% TNA</strong></div>
            <div class="meta-item">Fuentes: <strong>Reporte Inmobiliario | UCEMA - RE/MAX | DeInmobiliarios | ArgentinaDatos | SSPM | BCRA</strong></div>
        </div>
    </header>

    <!-- KPI CARDS -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-title">Valuación m² CABA</div>
            <div class="kpi-value">${m2_act:,.0f} USD</div>
            <div class="kpi-sub">
                Var. Reciente: <strong>{m2_var_pct:+.1f}%</strong> | Rebote piso 2023: <strong class="pos">+{m2_rebote:.1f}%</strong><br>
                Drawdown vs 2018: <strong class="neg">{m2_dd:.1f}%</strong>
            </div>
            <span class="badge" style="background:#e0f2fe; color:#0369a1; border:1px solid #7dd3fc;">Fase de Recuperación</span>
        </div>

        <div class="kpi-card">
            <div class="kpi-title">Ratio Deuda UVA / CCL</div>
            <div class="kpi-value">{ratio_act:.3f}</div>
            <div class="kpi-sub">
                Media: <strong>{ratio_media:.3f}</strong> | Z-Score: <strong>{ratio_zscore:+.2f}σ</strong><br>
                Banda normalidad: <strong>{ratio_sigma_inf:.2f} a {ratio_sigma_sup:.2f}</strong>
            </div>
            <span class="badge" style="{diag_ratio_badge}">{diag_ratio_txt}</span>
        </div>

        <div class="kpi-card">
            <div class="kpi-title">Salario RIPTE en Dólares</div>
            <div class="kpi-value">${sal_usd_act:,.0f} USD</div>
            <div class="kpi-sub">
                Mediana Hist.: <strong>${sal_usd_med:,.0f} USD</strong><br>
                Z-Score: <strong>{sal_usd_zscore:+.2f}σ</strong> (sobre piso de $400)
            </div>
            <span class="badge" style="background:#dcfce7; color:#166534; border:1px solid #4ade80;">Recuperación Fuerte</span>
        </div>

        <div class="kpi-card">
            <div class="kpi-title">Índice de Esfuerzo</div>
            <div class="kpi-value">{esf_act:.2f} sueldos</div>
            <div class="kpi-sub">
                Salarios formales por 1 m².<br>
                Promedio Histórico: <strong>{esf_media:.2f} sueldos</strong>
            </div>
            <span class="badge" style="{diag_esf_badge}">{diag_esf_txt}</span>
        </div>

        <div class="kpi-card">
            <div class="kpi-title">Brecha de Solvencia</div>
            <div class="kpi-value">{brecha_solvencia:+.1f}%</div>
            <div class="kpi-sub">
                Cuota UVA+TNA: <strong>{costo_financiero_total:.1f}%</strong><br>
                Salarios RIPTE: <strong>{var_ripte_act:.1f}%</strong>
            </div>
            <span class="badge" style="{diag_solv_badge}">{diag_solv_txt}</span>
        </div>
    </div>

    <!-- MATRIZ DE DECISIÓN ESTRATÉGICA -->
    <section class="decision-section">
        <h2 class="section-title">🧭 Matriz de Decisión para Actores del Mercado</h2>
        <p class="section-desc">Interpretación práctica de las señales cuantitativas actuales para guiar decisiones de inversión, financiamiento y patrimonio.</p>
        <div class="decision-grid">
            <div class="decision-box buy">
                <h3>1. Comprador de Contado / Inversor</h3>
                <p><strong>Escenario: Muy Favorable.</strong> El metro cuadrado (${m2_act:,.0f} USD) aún cotiza con un <strong>{abs(m2_dd):.1f}% de descuento</strong> respecto al récord de 2018 ($3,605). La desregulación contractual, el fin del cepo progresivo y el regreso del crédito sustentan un piso sólido con potencial de apreciación de mediano plazo.</p>
            </div>
            <div class="decision-box loan">
                <h3>2. Tomador de Crédito UVA</h3>
                <p><strong>Escenario: Oportunidad con Precaución.</strong> Tomar deuda indexada con el ratio UVA/CCL en banda alta (+1σ) es un arbitraje ventajoso si se proyecta una convergencia cambiaria. Sin embargo, en el corto plazo la cuota sube por encima de los sueldos ({costo_financiero_total:.1f}% vs {var_ripte_act:.1f}%), exigiendo holgura en la relación cuota-ingreso inicial.</p>
            </div>
            <div class="decision-box prep">
                <h3>3. Deudor UVA con Dólares</h3>
                <p><strong>Escenario: Desfavorable para Precancelar.</strong> Dado que 1 UVA cuesta hoy cerca de {ratio_act:.2f} USD (máximos relativos), cancelar cuotas o capital con dólares ahorrados hoy significa entregar más divisas por cada unidad de deuda. Conviene aguardar saltos cambiarios (CCL) que devuelvan el ratio a la banda baja (-1σ).</p>
            </div>
        </div>
    </section>

    <!-- SECCIÓN 1: INMUEBLES HISTÓRICOS -->
    <section class="report-card">
        <h2 class="section-title">1. Valuación Histórica del Metro Cuadrado en CABA (1977 - 2026)</h2>
        <div class="analysis-text">
            <p>El mercado residencial de la Ciudad de Buenos Aires presenta un comportamiento marcadamente cíclico, estrechamente atado a la política cambiaria, la estabilidad monetaria y la disponibilidad de financiamiento hipotecario.</p>
        </div>
        <img src="data:image/png;base64,{img_inmuebles}" alt="Valuación Histórica CABA">
        <div class="analysis-text">
            <p><strong>Lectura Cuantitativa:</strong> El valor actual de <strong>${m2_act:,.0f} USD/m²</strong> se sitúa en torno a la mediana histórica ($2,150 USD) y dentro de la banda de normalidad intercuartílica (P25-P75: ${m2_p25:,.0f} - ${m2_p75:,.0f} USD). Tras alcanzar un piso deprimido de $1,837 USD en 2023, el mercado consolidó un <strong>rebote del {m2_rebote:.1f}%</strong> impulsado por el blanqueo de capitales y la derogación de la Ley de Alquileres.</p>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Período</th>
                        <th>Contexto Macroeconómico</th>
                        <th>Precio Inicio</th>
                        <th>Precio Fin</th>
                        <th>Variación</th>
                        <th>Diagnóstico de Ciclo</th>
                    </tr>
                </thead>
                <tbody>
                    {ciclos_tabla}
                </tbody>
            </table>
        </div>
    </section>

    <!-- SECCIÓN 2: RATIO UVA / CCL -->
    <section class="report-card">
        <h2 class="section-title">2. Arbitraje Financiero: Dinámica del Ratio UVA / CCL</h2>
        <div class="analysis-text">
            <p>El ratio <strong>UVA / CCL</strong> sintetiza la relación entre la inflación en pesos (que indexa la unidad UVA según CER) y la cotización del dólar libre (Contado con Liquidación). Mide de forma transparente el <strong>costo de la deuda en dólares</strong>.</p>
        </div>
        <img src="data:image/png;base64,{img_ratio}" alt="Ratio UVA vs CCL">
        <div class="analysis-text">
            <p><strong>Implicancia de Arbitraje:</strong> {diag_ratio_desc}</p>
            <p>Cuando la inflación supera sostenidamente al ritmo de devaluación (atraso cambiario o apreciación real del peso), el ratio escala hacia la banda roja (+1 Sigma). Históricamente, estos puntos marcan momentos donde el deudor se encuentra con cuotas en dólares encarecidas, pero representan el momento más ventajoso para tomar nuevo crédito si el tomador proyecta que a futuro el dólar equiparará o superará al IPC.</p>
        </div>
    </section>

    <!-- SECCIÓN 3: SOLVENCIA -->
    <section class="report-card">
        <h2 class="section-title">3. Solvencia Crediticia: Ajuste de Cuota vs Sueldos RIPTE</h2>
        <div class="analysis-text">
            <p>El principal riesgo de los créditos hipotecarios UVA radica en el descalce entre la tasa de inflación que actualiza la cuota y la evolución de los salarios reales de los trabajadores formales estables (RIPTE).</p>
        </div>
        <img src="data:image/png;base64,{img_solvencia}" alt="Solvencia Salarial">
        <div class="analysis-text">
            <p><strong>Diagnóstico de Solvencia:</strong> {diag_solv_desc}</p>
            <p>Actualmente, el costo total anual de la cuota (UVA interanual {var_uva_act:.1f}% + {TNA_BANCO}% TNA = {costo_financiero_total:.1f}%) se posiciona {abs(brecha_solvencia):.1f} puntos por encima del incremento salarial registrado ({var_ripte_act:.1f}%). Esto indica que la porción del ingreso familiar destinada a atender el crédito ha experimentado una presión alcista temporal.</p>
        </div>
    </section>

    <!-- SECCIÓN 4: PODER DE COMPRA -->
    <section class="report-card">
        <h2 class="section-title">4. Poder Adquisitivo en Moneda Dura: Salario RIPTE en Dólares</h2>
        <div class="analysis-text">
            <p>La capacidad de pago y absorción de propiedades residenciales está directamente condicionada por el valor del salario formal expresado en dólares billete.</p>
        </div>
        <img src="data:image/png;base64,{img_buying_power}" alt="Salarios en USD">
        <div class="analysis-text">
            <p><strong>Recuperación Salarial:</strong> El salario RIPTE promedio escaló desde mínimos de $400-$500 USD (finales de 2023) hasta situarse en <strong>${sal_usd_act:,.0f} USD</strong>. Esta recomposición salarial en moneda dura es la responsable de reactivar la demanda de metros cuadrados y validar los nuevos precios de oferta en la Ciudad de Buenos Aires.</p>
        </div>
    </section>

    <!-- SECCIÓN 5: ÍNDICE DE ESFUERZO -->
    <section class="report-card">
        <h2 class="section-title">5. Accesibilidad: Índice de Esfuerzo (Sueldos enteros por m²)</h2>
        <div class="analysis-text">
            <p>El Índice de Esfuerzo mide cuántos meses de salario RIPTE promedio íntegro se requieren para comprar un solo metro cuadrado de inmueble en CABA.</p>
        </div>
        <img src="data:image/png;base64,{img_esfuerzo}" alt="Índice de Esfuerzo">
        <div class="analysis-text">
            <p><strong>Evaluación de Oportunidad:</strong> {diag_esf_desc}</p>
            <p>Con un ratio de <strong>{esf_act:.2f} salarios por m²</strong> frente a picos históricos de más de 3.5 salarios (durante los momentos de devaluación y shock salarial), el acceso al metro cuadrado se encuentra en una franja históricamente favorable para quien cuenta con capacidad de ahorro o financiamiento.</p>
        </div>
    </section>

    <!-- SECCIÓN 6: DASHBOARD CONSOLIDADO -->
    <section class="report-card">
        <h2 class="section-title">6. Tablero Consolidado: Vista Integral de Decisión</h2>
        <p class="analysis-text">Integración simultánea de los cinco vectores analíticos para una perspectiva panorámica del ciclo macroeconómico e inmobiliario.</p>
        <img src="data:image/png;base64,{img_dashboard}" alt="Tablero Consolidado">
    </section>

    <!-- CONCLUSIONES -->
    <section class="report-card" style="border-left: 5px solid var(--accent-blue);">
        <h2 class="section-title">📌 Conclusiones Ejecutivas</h2>
        <div class="analysis-text">
            <p><strong>1. Ventana de Entrada Inmobiliaria:</strong> Las propiedades en CABA transitan la fase inicial de un nuevo ciclo alcista tras haber testeado pisos históricos en 2023. La combinación de un m² aún con 40% de descuento vs 2018 y un salario en dólares en recuperación confirma un punto de entrada favorable para compradores e inversores patrimoniales.</p>
            <p><strong>2. Gestión de Deuda Indexada (UVA):</strong> El deudor hipotecario debe contemplar la volatilidad del ratio UVA/CCL. Quienes se endeudan hoy lo hacen con un tipo de cambio real apreciado, lo cual es ventajoso si a futuro la devaluación supera a la inflación; no obstante, el riesgo de descalce cuota-ingreso de corto plazo impone mantener una relación cuota-ingreso prudente (no superior al 20-25%).</p>
            <p><strong>3. Estrategia de Cancelación Anticipada:</strong> Quienes cuenten con ahorros en dólares billete deben evitar prepagar deudas UVA en momentos de ratio elevado como el actual (+1σ), reservando la liquidez para episodios de corrección cambiaria donde la deuda se licúa transitoriamente en dólares.</p>
        </div>
    </section>

    <footer class="footer">
        <p><strong>Elaboración del informe:</strong> Lic. Matías Ezequiel González, MSc Candidate.</p>
        <p>Informe cuantitativo generado mediante el motor analítico de <strong>Dashboard Real Estate CABA</strong>.</p>
        <p>© {datetime.now().year} — Fuentes ground-truth: Reporte Inmobiliario, UCEMA - RE/MAX, DeInmobiliarios, ArgentinaDatos, SSPM (Datos.gob.ar) y BCRA.</p>
    </footer>

</div>
</body>
</html>
"""

    # Guardar archivo
    reports_dir = Path(__file__).resolve().parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / output_filename

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n[OK] Informe HTML generado correctamente en:")
    print(f"   -> {report_path}")

    if OPEN_IN_BROWSER:
        print(">>> Abriendo informe en el navegador...")
        webbrowser.open(report_path.as_uri())

    return report_path


# --- 5. EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    print(">>> Iniciando Sistema Inmobiliario & Macroeconómico...")
    df_m2 = obtener_datos_propiedades()
    df_fin, df_mensual = descargar_financieros_full()
    df_esfuerzo = calcular_indice_esfuerzo(df_m2, df_mensual)
    fechas_fut, rutas_mc, media_mc, mediana_mc = calcular_montecarlo(df_fin)

    if df_fin.empty:
        print("[ERROR] No se pudieron obtener los datos financieros.")
    else:
        eventos_usuario = solicitar_eventos()

        # Generar informe HTML completo
        if GENERAR_INFORME_HTML:
            generar_informe_html(
                df_m2=df_m2,
                df_fin=df_fin,
                df_mensual=df_mensual,
                df_esfuerzo=df_esfuerzo,
                fechas_fut=fechas_fut,
                rutas_mc=rutas_mc,
                media_mc=media_mc,
                mediana_mc=mediana_mc,
                eventos_usuario=eventos_usuario,
            )

        # Mostrar plots interactivos de matplotlib (opcional)
        if MOSTRAR_PLOTS_INTERACTIVOS:
            print("\n>>> Abriendo gráficos interactivos...")
            plt.figure(figsize=(14, 8))
            plot_inmuebles(plt.gca(), df_m2, eventos_usuario)
            plt.tight_layout()
            plt.show()

            plt.figure(figsize=(14, 8))
            plot_ratio(
                plt.gca(),
                df_fin,
                fechas_fut,
                rutas_mc,
                media_mc,
                mediana_mc,
                eventos_usuario,
            )
            plt.tight_layout()
            plt.show()

            if not df_mensual.empty:
                plt.figure(figsize=(14, 8))
                plot_solvencia(plt.gca(), df_mensual)
                plt.tight_layout()
                plt.show()

                plt.figure(figsize=(14, 8))
                plot_buying_power(plt.gca(), df_mensual, eventos_usuario)
                plt.tight_layout()
                plt.show()

                if not df_esfuerzo.empty:
                    plt.figure(figsize=(14, 8))
                    plot_esfuerzo(plt.gca(), df_esfuerzo, eventos_usuario)
                    plt.tight_layout()
                    plt.show()
