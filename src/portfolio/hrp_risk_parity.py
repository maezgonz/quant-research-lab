# Riesgo Jerárquico (HRP - Hierarchical Risk Parity).

    # 1. Obtención de Datos de Mercado: Descarga los precios históricos de cierre de una lista específica de activos financieros (en este caso, parece que estabas analizando principalmente acciones argentinas como Grupo Galicia, YPF, Pampa Energía, etc.) utilizando la API de openbb y yfinance. Luego, calcula los retornos diarios de cada activo.
    # 2. Clustering Jerárquico (Machine Learning): Analiza la correlación histórica entre los diferentes activos y los agrupa en "clústeres" (grupos de activos que se mueven de forma similar en el mercado). Esto lo visualiza mediante un gráfico de árbol llamado dendrograma, lo que ayuda a entender la estructura y dependencias ocultas entre los activos.
    # 3. Optimización de la Cartera (HRP): Utiliza la librería riskfolio para calcular los pesos (porcentajes de inversión) óptimos para cada activo. En lugar de usar métodos tradicionales, emplea el modelo HRP enfocado en Mínima Varianza (MV). Su objetivo es construir una cartera altamente diversificada que minimice la volatilidad general del portafolio.
    # 4. Visualización de Pesos: Genera un gráfico circular (pie chart) que te muestra exactamente qué porcentaje de tu capital deberías invertir en cada acción para lograr la cartera óptima sugerida por el modelo.
    # 5. Análisis de Contribución al Riesgo: Finalmente, genera un gráfico de barras que desglosa cuánto riesgo (volatilidad) está aportando cada activo individualmente al riesgo total de la cartera optimizada.

# En resumen, el script toma una lista de acciones, estudia cómo interactúan entre sí, y te dice cómo distribuir tu dinero para minimizar el riesgo utilizando algoritmos de clustering.

import pandas as pd
from openbb import obb
import riskfolio as rp
import matplotlib.pyplot as plt

def main():
    # 1. Define the universe of sector-based ETFs, Stocks, Bonds
    assets = [
        "ALUA.BA", "BBAR.BA", "BMA.BA", "BYMA.BA", "CEPU.BA", "COME.BA", "EDN.BA", "GGAL.BA", "IRSA.BA",
        "LOMA.BA", "METR.BA", "MIRG.BA", "PAMP.BA", "SUPV.BA", "TECO2.BA", "TGNO4.BA", "TGSU2.BA",
        "TRAN.BA", "TXAR.BA", "VALO.BA", "YPFD.BA", "AGRO.BA", "AUSO.BA", "BHIP.BA", "BOLT.BA", "BPAT.BA",
        "BRIO.BA", "CAPX.BA", "CARC.BA", "CECO2.BA", "CELU.BA", "CGPA2.BA", "CTIO.BA", "DGCU2.BA",
        "FERR.BA", "GARO.BA", "GCLA.BA", "GRIM.BA", "HAVA.BA", "INTR.BA", "INVJ.BA", "LEDE.BA", "LONG.BA",
        "MOLI.BA", "MORI.BA", "OEST.BA", "PATA.BA", "POLL.BA", "RIGO.BA", "ROSE.BA","SAMI.BA", "SEMI.BA"

    # 1. Lista de ETF:
         #"XLE", "XLF", "XLU", "XLI", "GDX",
         #"XLK", "XLV", "XLY", "XLP", "XLB",
         #"XOP", "IYR", "XHB", "ITB", "VNQ",
         #"GDXJ", "IYE", "OIH", "XME", "XRT",
         #"SMH", "IBB", "KBE", "KRE", "XTL",
    ]

    # 2. Fetch historical data and calculate daily returns
    data = (
        obb.equity.price.historical(assets, provider="yfinance")
        .to_df()
        .pivot(columns="symbol", values="close")
    )
    # Drop assets that have missing data to ensure a consistent timeframe and avoid NaNs
    data = data.dropna(axis=1)
    returns = data.pct_change().dropna()

    # 3. Visualize hierarchical clustering of assets
    rp.plot_dendrogram(
        returns=returns,
        codependence="pearson",
        linkage="single",
        k=None,
        max_k=10,
        leaf_order=True,
    )
    plt.show()

    # 4. Build the optimal Hierarchical Risk Parity (HRP) portfolio
    port = rp.HCPortfolio(returns=returns)
    weights = port.optimization(
        model="HRP",
        codependence="pearson",
        rm="MV", # Minimum Variance
        rf=0.05,
        linkage="single",
        max_k=10,
        leaf_order=True,
    )

# 1. El Dendrograma (Gráfico de Árbol / Clustering)
    # Este es el primer gráfico que aparece.
    # Muestra cómo el algoritmo de Machine Learning agrupa las acciones basándose en su comportamiento histórico (correlación).
        # •Eje Horizontal (X): Verás los nombres de los activos (los tickers de las acciones).
        # •Eje Vertical (Y): Representa la "distancia" o diferencia en el comportamiento.
    # Cómo interpretarlo:
        # ◦Líneas cortas (uniones bajas): Las acciones que se unen muy abajo en el gráfico tienen un comportamiento casi idéntico. Si el mercado sube, ambas suben; si baja, ambas bajan. (Ej. Dos bancos muy similares).
        # ◦Líneas largas (uniones altas): Las acciones que se unen más arriba son independientes o tienen baja correlación.
        # •¿Para qué sirve? Te ayuda a entender la verdadera diversificación. Si compras 10 acciones diferentes, pero todas están en la misma "rama pequeña" del árbol, no estás diversificado. El algoritmo HRP usa este árbol para asegurarse de no sobreinvertir en ramas muy agrupadas, distribuyendo el dinero entre ramas distintas.

    # 5. Visualize the optimal portfolio weights
    rp.plot_pie(
        w=weights,
        title="HRP Naive Risk Parity",
        others=0.05,
        nrow=25,
        cmap="tab20",
        height=10,
        width=18,
    )
    plt.show()

# 2. El Gráfico Circular (Pesos de la Cartera / Pie Chart)
    #Este gráfico es la recomendación final y directa del modelo ("HRP Naive Risk Parity").
        # •Cómo interpretarlo: Te muestra el porcentaje exacto de tu capital total que deberías asignar a cada acción.
        # •Por qué el modelo elige estos pesos: Dado que le pediste al script que minimice la varianza (rm="MV"), el modelo le dará porcentajes más grandes a las acciones que son más estables (menos volátiles) o a aquellas que sirven de "refugio" porque no se mueven al mismo ritmo que el resto de la cartera. Las acciones muy volátiles o muy correlacionadas entre sí tendrán porciones mucho más pequeñas.
        # •¿Para qué sirve? Es tu "receta" de inversión. Si tienes $100,000 para invertir, este gráfico te dice exactamente cuántos dólares poner en YPF, cuántos en Galicia, etc., para obtener la cartera más segura (matemáticamente hablando) con esos activos.

    # 6. Visualize the risk contribution of each asset
    rp.plot_risk_con(
        w=weights,
        cov=returns.cov(),
        returns=returns,
        rm="MV",
        rf=0,
        alpha=0.05,
        color="tab:blue",
        height=10,
        width=21,
        t_factor=252,
    )
    plt.show()

    #  3. El Gráfico de Barras (Contribución al Riesgo / Risk Contribution)
            # Este es crucial y a menudo se malinterpreta. Muestra qué porcentaje del riesgo total (volatilidad) de tu nueva cartera proviene de cada acción.
                # •Peso vs. Riesgo: Es vital entender que poner el 10% de tu dinero en una acción no significa que esa acción aporte el 10% del riesgo. Si pones un 10% en un bono del gobierno (muy seguro) y un 10% en una empresa a punto de quebrar (muy volátil), la empresa aportará casi todo el riesgo de tu cartera.
                # •Cómo interpretarlo: Revisa las barras más altas. Esas son las acciones que, incluso después de la optimización, son las principales responsables de los altibajos de tu cartera.
                # •¿Para qué sirve?: Te permite hacer un chequeo de "confort". Si ves que una sola acción está aportando, por ejemplo, el 40% del riesgo total de tu cartera, podrías decidir que es demasiado peligroso y optar por sacarla de tu lista inicial de activos (assets) y volver a correr el script.


if __name__ == "__main__":
    main()


    # Resumen práctico de uso:
        # 1. Miras el Dendrograma para entender qué acciones de tu lista son básicamente "la misma cosa" a los ojos del mercado.
        # 2. Miras el Gráfico Circular para saber cómo armar tu cartera hoy mismo para minimizar sobresaltos.
        # 3. Miras la Contribución al Riesgo para asegurarte de que ninguna acción individual tenga el poder de hundir tu rentabilidad si tiene un mal día.
