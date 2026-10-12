import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json

class CriptoYaAPI:
    def __init__(self):
        self.base_url = "https://criptoya.com/api"
        
    def obtener_precio(self, cripto, moneda, pais="argentina"):
        """
        Obtiene el precio actual de una criptomoneda en diferentes exchanges.
        
        Args:
            cripto (str): Criptomoneda (ej. 'btc', 'eth', 'usdt')
            moneda (str): Moneda fiat (ej. 'ars', 'usd', 'mxn')
            pais (str): País de consulta (default: 'argentina')
            
        Returns:
            dict: Datos de precios en diferentes exchanges
        """
        url = f"{self.base_url}/{cripto}/{moneda}/{pais}"
        response = requests.get(url, timeout=15)
        return response.json()
    
    def obtener_historico(self, exchange, cripto, moneda, periodo=24):
        """
        Obtiene datos históricos de precios.
        
        Args:
            exchange (str): Nombre del exchange (ej. 'binance', 'ripio')
            cripto (str): Criptomoneda (ej. 'btc', 'eth')
            moneda (str): Moneda fiat (ej. 'ars', 'usd')
            periodo (int): Horas de histórico (default: 24)
            
        Returns:
            dict: Datos históricos de precios
        """
        url = f"{self.base_url}/{exchange}/{cripto}/{moneda}/{periodo}h"
        response = requests.get(url, timeout=15)
        return response.json()
    
    def comparar_exchanges(self, cripto, moneda, pais="argentina"):
        """
        Compara precios entre diferentes exchanges.
        
        Args:
            cripto (str): Criptomoneda (ej. 'btc', 'eth')
            moneda (str): Moneda fiat (ej. 'ars', 'usd')
            pais (str): País de consulta (default: 'argentina')
            
        Returns:
            pd.DataFrame: DataFrame con comparación de precios
        """
        datos = self.obtener_precio(cripto, moneda, pais)
        
        # Crear lista para almacenar datos de cada exchange
        exchanges_data = []
        
        for exchange, info in datos.items():
            # Verificar si es un exchange (omitir campos como 'time')
            if isinstance(info, dict) and 'ask' in info:
                exchanges_data.append({
                    'Exchange': exchange,
                    'Precio Compra': info.get('ask', 0),
                    'Precio Venta': info.get('bid', 0),
                    'Volumen 24h': info.get('volume', 0)
                })
        
        # Crear DataFrame
        df = pd.DataFrame(exchanges_data)
        return df
    
    def visualizar_historico(self, exchange, cripto, moneda, periodo=24):
        """
        Visualiza datos históricos en un gráfico.
        
        Args:
            exchange (str): Nombre del exchange
            cripto (str): Criptomoneda
            moneda (str): Moneda fiat
            periodo (int): Horas de histórico
            
        Returns:
            None: Muestra el gráfico
        """
        datos = self.obtener_historico(exchange, cripto, moneda, periodo)
        
        # Crear DataFrame
        df = pd.DataFrame(datos)
        
        # Convertir timestamp a datetime
        df['time'] = pd.to_datetime(df['t'], unit='s')
        
        # Graficar
        plt.figure(figsize=(12, 6))
        plt.plot(df['time'], df['p'], label=f'Precio {cripto.upper()}/{moneda.upper()}')
        plt.title(f'Evolución de precio de {cripto.upper()} en {exchange.capitalize()}')
        plt.xlabel('Fecha')
        plt.ylabel(f'Precio ({moneda.upper()})')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
        
    def exportar_datos(self, cripto, moneda, pais="argentina", formato="csv"):
        """
        Exporta datos a un archivo.
        
        Args:
            cripto (str): Criptomoneda
            moneda (str): Moneda fiat
            pais (str): País de consulta
            formato (str): Formato de exportación ('csv' o 'json')
            
        Returns:
            str: Ruta del archivo guardado
        """
        df = self.comparar_exchanges(cripto, moneda, pais)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{cripto}_{moneda}_{pais}_{timestamp}"
        
        if formato.lower() == "csv":
            filepath = f"{filename}.csv"
            df.to_csv(filepath, index=False)
        else:
            filepath = f"{filename}.json"
            df.to_json(filepath, orient="records")
            
        print(f"Datos exportados a {filepath}")
        return filepath

# Ejemplo de uso
if __name__ == "__main__":
    api = CriptoYaAPI()
    
    # Ejemplo 1: Obtener precio de Bitcoin en ARS (Argentina)
    print("Precio de Bitcoin en diferentes exchanges (Argentina):")
    precios_btc = api.obtener_precio("btc", "ars")
    print(json.dumps(precios_btc, indent=2))
    
    # Ejemplo 2: Comparar precios entre exchanges
    print("\nComparación de precios de ETH/USD:")
    comparacion = api.comparar_exchanges("eth", "usd")
    print(comparacion)
    
    # Ejemplo 3: Exportar datos a CSV
    api.exportar_datos("btc", "ars", formato="csv")
    
    # Ejemplo 4: Visualizar datos históricos (descomenta para ejecutar)
    # api.visualizar_historico("binance", "btc", "usdt", 24)