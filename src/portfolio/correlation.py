import pandas as pd
import numpy as np
import yfinance as yf
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class AnalizadorCorrelacion:
    def __init__(self):
        # Separar activos por tipo
        self.acciones = {
            'Banco Macro': 'BMA.BA',
            'Edenor': 'EDN.BA',
            'Grupo Financiero Galicia': 'GGAL.BA',
            'Metro Gas': 'METR.BA',
            'Molinos Agro': 'MOLI.BA',
            'Morixe': 'MORI.BA',
            'Pampa Energía': 'PAMP.BA',
            'Semiconductores': 'SEMI.BA',
            'Transportadora Gas Norte': 'TGNO4.BA',
            'Transportadora Gas Sur': 'TGSU2.BA',
            'Transener': 'TRAN.BA',
            'YPF': 'YPFD.BA'
        }
        
        self.bonos = {
            'Bonar 2030': 'GD30.BA',
            'Bonar 2035': 'GD35.BA',
            'Bonar 2038': 'GD38.BA',
            'Bonar 2041': 'GD41.BA'
        }

    def obtener_datos(self, periodo_meses=6):
        """Descarga los datos históricos para el período especificado."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=periodo_meses*30)
            
            # Combinar todos los tickers
            todos_tickers = list(self.acciones.values()) + list(self.bonos.values())
            
            print(f"Descargando datos desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
            
            # Descargar datos
            datos = yf.download(todos_tickers, 
                              start=start_date, 
                              end=end_date, 
                              progress=False)['Adj Close']
            
            # Verificar datos faltantes
            datos_faltantes = [ticker for ticker in todos_tickers if ticker not in datos.columns]
            if datos_faltantes:
                print(f"\nAdvertencia: No se encontraron datos para: {', '.join(datos_faltantes)}")
            
            return datos
        except Exception as e:
            print(f"Error al obtener datos: {str(e)}")
            return None

    def calcular_correlaciones(self, datos):
        """Calcula las correlaciones y retorna diferentes análisis."""
        try:
            # Calcular rendimientos diarios
            rendimientos = datos.pct_change().fillna(0)
            
            # Matriz de correlación
            correlaciones = rendimientos.corr()
            
            # Estadísticas descriptivas
            stats = rendimientos.describe()
            
            # Volatilidad anualizada
            volatilidad = rendimientos.std() * np.sqrt(252) * 100
            
            return {
                'correlaciones': correlaciones,
                'estadisticas': stats,
                'volatilidad': volatilidad,
                'rendimientos': rendimientos
            }
        except Exception as e:
            print(f"Error al calcular correlaciones: {str(e)}")
            return None

    def visualizar_correlaciones(self, correlaciones, tipo='todos'):
        """Genera visualizaciones de las correlaciones."""
        try:
            plt.figure(figsize=(12, 8))
            
            # Filtrar por tipo si es necesario
            if tipo == 'acciones':
                tickers = list(self.acciones.values())
                titulo = "Correlación entre Acciones"
            elif tipo == 'bonos':
                tickers = list(self.bonos.values())
                titulo = "Correlación entre Bonos"
            else:
                tickers = correlaciones.columns
                titulo = "Correlación entre Todos los Activos"
            
            # Filtrar matriz de correlación
            matriz_filtrada = correlaciones.loc[tickers, tickers]
            
            # Crear mapa de calor
            sns.heatmap(matriz_filtrada, 
                       annot=True, 
                       cmap="coolwarm", 
                       center=0, 
                       linewidths=0.5, 
                       fmt='.2f',
                       square=True)
            
            plt.title(titulo)
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Error en la visualización: {str(e)}")

    def mostrar_estadisticas(self, analisis):
        """Muestra estadísticas relevantes de los activos."""
        try:
            print("\n=== ESTADÍSTICAS DE LOS ACTIVOS ===")
            
            # Volatilidad
            print("\nVolatilidad Anualizada (%):")
            print(analisis['volatilidad'].sort_values(ascending=False).round(2))
            
            # Rendimientos promedio
            print("\nRendimiento Diario Promedio (%):")
            print((analisis['estadisticas'].loc['mean'] * 100).sort_values(ascending=False).round(4))
            
            # Activos más correlacionados
            corr = analisis['correlaciones']
            np.fill_diagonal(corr.values, np.nan)
            max_corr = corr.unstack()
            max_corr = max_corr[~max_corr.isna()].sort_values(ascending=False)
            
            print("\nPares más correlacionados:")
            for i in range(5):
                par = max_corr.index[i]
                valor = max_corr.iloc[i]
                print(f"{par[0]} - {par[1]}: {valor:.3f}")
            
        except Exception as e:
            print(f"Error al mostrar estadísticas: {str(e)}")

def main():
    try:
        analizador = AnalizadorCorrelacion()
        
        # Obtener datos
        datos = analizador.obtener_datos(periodo_meses=6)
        if datos is None:
            return
        
        # Calcular análisis
        analisis = analizador.calcular_correlaciones(datos)
        if analisis is None:
            return
        
        # Mostrar visualizaciones
        print("\nGenerando visualizaciones...")
        analizador.visualizar_correlaciones(analisis['correlaciones'], 'acciones')
        analizador.visualizar_correlaciones(analisis['correlaciones'], 'bonos')
        analizador.visualizar_correlaciones(analisis['correlaciones'], 'todos')
        
        # Mostrar estadísticas
        analizador.mostrar_estadisticas(analisis)
        
    except Exception as e:
        print(f"Error en la ejecución principal: {str(e)}")

if __name__ == "__main__":
    main()