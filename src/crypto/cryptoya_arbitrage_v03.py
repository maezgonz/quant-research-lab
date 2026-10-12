import requests
import pandas as pd
import time
from datetime import datetime
from tabulate import tabulate

class ArbitrajeDetector:
    def __init__(self, intervalo_segundos=60, umbral_ganancia=0.5, excluir_mercado_p2p=True):
        """
        Inicializa el detector de arbitraje.
        
        Args:
            intervalo_segundos (int): Intervalo entre verificaciones (en segundos)
            umbral_ganancia (float): Umbral mínimo de ganancia porcentual para reportar
            excluir_mercado_p2p (bool): Si se excluyen las operaciones del mercado P2P
        """
        self.base_url = "https://criptoya.com/api"
        self.intervalo = intervalo_segundos
        self.umbral_ganancia = umbral_ganancia
        self.excluir_mercado_p2p = excluir_mercado_p2p
        
        # Identificadores de mercado P2P
        self.mercados_p2p = {
            "p2p", "trubitp2p", "binancep2p", "bybitp2p", "okexp2p", 
            "bitgetp2p", "bingxp2p", "kucoinp2p", "lemoncashp2p",
            "eldoradop2p", "paxfulp2p", "bitfinexp2p", "coinexp2p",
            "ripioexchange", "lnp2pbotp2p"
        }
        
        # Criptomonedas a monitorear
        self.criptos = ["btc", "eth", "usdt", "dai", "usdc"]
        
        # Monedas fiat por país
        self.monedas_por_pais = {
            "argentina": "ars",
            "mexico": "mxn",
            "colombia": "cop",
            "peru": "pen",
            "chile": "clp",
            "uruguay": "uyu",
            "venezuela": "ves",
            "paraguay": "pyg",
            "bolivia": "bob",
            "brazil": "brl",
            "dominicana": "dop"
        }
        
        # Comisiones estimadas de exchanges (porcentajes)
        self.fees_exchanges = {
            "binance": 0.1,
            "ripio": 0.5,
            "belo": 0.4,
            "bitso": 0.6,
            "letsbit": 0.5,
            "buenbit": 0.7,
            "lemoncash": 0.5,
            "fiwind": 0.5,
            "tiendacrypto": 1.0,
            "bitmonedero": 0.8,
            "decrypto": 0.9,
            "latamex": 0.8,
            "kriptonmarket": 0.7,
            "calypso": 0.9,
            "bybit": 0.1,
            "cryptomkt": 0.8,
            "paxful": 1.5,
            "saldo": 0.8,
            "satoshitango": 1.0,
            "banexcoin": 0.7,
            "copter": 0.9,
            "buda": 0.7,
            "bitex": 0.7,
            "orionx": 0.7,
            "trocafacil": 0.8
        }
        
        # Redes blockchain por criptomoneda 
        self.redes_blockchain = {
            "btc": [
                ["Bitcoin", 3.5, 30]
            ],
            "eth": [
                ["Ethereum", 2.0, 5],
                ["Arbitrum", 0.3, 1],
                ["Optimism", 0.3, 1]
            ],
            "usdt": [
                ["Ethereum (ERC20)", 2.5, 5],
                ["Tron (TRC20)", 0.1, 1],
                ["BSC (BEP20)", 0.2, 1],
                ["Polygon", 0.05, 1],
                ["Solana", 0.02, 1],
                ["Arbitrum", 0.2, 1]
            ],
            "dai": [
                ["Ethereum (ERC20)", 2.2, 5],
                ["BSC (BEP20)", 0.2, 1],
                ["Polygon", 0.05, 1],
                ["Arbitrum", 0.2, 1],
                ["Optimism", 0.2, 1]
            ],
            "usdc": [
                ["Ethereum (ERC20)", 2.0, 5],
                ["Tron (TRC20)", 0.1, 1],
                ["BSC (BEP20)", 0.2, 1],
                ["Polygon", 0.05, 1],
                ["Solana", 0.02, 1],
                ["Arbitrum", 0.2, 1],
                ["Avalanche", 0.1, 1]
            ]
        }
        
        # Redes soportadas por cada exchange
        self.redes_por_exchange = {
            "binance": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum", "Arbitrum", "Optimism"],
                "usdt": ["Ethereum (ERC20)", "Tron (TRC20)", "BSC (BEP20)", "Polygon", "Solana", "Arbitrum"],
                "dai": ["Ethereum (ERC20)", "BSC (BEP20)", "Polygon", "Arbitrum", "Optimism"],
                "usdc": ["Ethereum (ERC20)", "Tron (TRC20)", "BSC (BEP20)", "Polygon", "Solana", "Arbitrum", "Avalanche"]
            },
            "ripio": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum"],
                "usdt": ["Ethereum (ERC20)", "Tron (TRC20)"],
                "dai": ["Ethereum (ERC20)"],
                "usdc": ["Ethereum (ERC20)"]
            },
            "bitso": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum"],
                "usdt": ["Ethereum (ERC20)"],
                "dai": ["Ethereum (ERC20)"],
                "usdc": ["Ethereum (ERC20)"]
            },
            "letsbit": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum"],
                "usdt": ["Ethereum (ERC20)", "Tron (TRC20)"],
                "dai": ["Ethereum (ERC20)"],
                "usdc": ["Ethereum (ERC20)"]
            },
            "buenbit": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum"],
                "usdt": ["Ethereum (ERC20)"],
                "dai": ["Ethereum (ERC20)"],
                "usdc": ["Ethereum (ERC20)"]
            },
            "lemoncash": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum"],
                "usdt": ["Ethereum (ERC20)", "Tron (TRC20)"],
                "dai": ["Ethereum (ERC20)"],
                "usdc": ["Ethereum (ERC20)"]
            },
            "belo": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum"],
                "usdt": ["Ethereum (ERC20)"],
                "dai": ["Ethereum (ERC20)"],
                "usdc": ["Ethereum (ERC20)"]
            },
            "bybit": {
                "btc": ["Bitcoin"],
                "eth": ["Ethereum", "Arbitrum", "Optimism"],
                "usdt": ["Ethereum (ERC20)", "Tron (TRC20)", "BSC (BEP20)", "Polygon", "Solana", "Arbitrum"],
                "dai": ["Ethereum (ERC20)", "BSC (BEP20)", "Polygon", "Arbitrum"],
                "usdc": ["Ethereum (ERC20)", "Tron (TRC20)", "BSC (BEP20)", "Polygon", "Solana", "Arbitrum", "Avalanche"]
            }
        }
        
        # Para exchanges no listados explícitamente, usar estas redes por defecto
        self.redes_default = {
            "btc": ["Bitcoin"],
            "eth": ["Ethereum"],
            "usdt": ["Ethereum (ERC20)", "Tron (TRC20)"],
            "dai": ["Ethereum (ERC20)"],
            "usdc": ["Ethereum (ERC20)"]
        }

    def es_mercado_p2p(self, exchange):
        """Determina si es una operación de mercado P2P."""
        return any(p2p in exchange.lower() for p2p in self.mercados_p2p)

    def obtener_tipo_cambio(self, moneda_origen, moneda_destino, datos):
        """
        Calcula el tipo de cambio entre dos monedas usando USD como puente.
        """
        try:
            if moneda_origen == moneda_destino:
                return 1
            
            # Obtener tasas USD para ambas monedas
            usd_origen = 1
            usd_destino = 1
            
            if 'dolar' in datos:
                if moneda_origen != 'usd':
                    usd_origen = datos['dolar'].get('price', 1)
                if moneda_destino != 'usd':
                    usd_destino = datos['dolar'].get('price', 1)
            
            return usd_destino / usd_origen
        except Exception as e:
            print(f"Error calculando tipo de cambio: {str(e)}")
            return 1
    def obtener_precio(self, cripto, moneda, pais="argentina"):
        """Obtiene precios de una criptomoneda en todos los exchanges disponibles."""
        try:
            url = f"{self.base_url}/{cripto}/{moneda}/{pais}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error al obtener datos: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error en la solicitud: {str(e)}")
            return {}

    def encontrar_mejor_red(self, exchange_origen, exchange_destino, cripto):
        """Encuentra la red blockchain más económica que es soportada por ambos exchanges."""
        # Obtener redes soportadas por cada exchange
        redes_origen = self.redes_por_exchange.get(exchange_origen, self.redes_default).get(cripto, [])
        redes_destino = self.redes_por_exchange.get(exchange_destino, self.redes_default).get(cripto, [])
        
        # Encontrar redes comunes
        redes_comunes = [red for red in redes_origen if red in redes_destino]
        
        if not redes_comunes:
            return None, None, None
        
        # Encontrar la red más económica entre las comunes
        mejor_red = None
        menor_fee = float('inf')
        tiempo_confirmacion = 0
        
        for red_comun in redes_comunes:
            for red_info in self.redes_blockchain.get(cripto, []):
                if red_info[0] == red_comun and red_info[1] < menor_fee:
                    mejor_red = red_comun
                    menor_fee = red_info[1]
                    tiempo_confirmacion = red_info[2]
        
        return mejor_red, menor_fee, tiempo_confirmacion

    def calcular_arbitraje_local(self, pais, datos, oportunidades):
        """Calcula arbitrajes dentro de un mismo país."""
        moneda = self.monedas_por_pais[pais]
        
        for cripto, datos_cripto in datos.items():
            exchanges = []
            
            # Filtrar exchanges válidos
            for exchange, info in datos_cripto.items():
                if isinstance(info, dict) and 'ask' in info and 'bid' in info:
                    if not self.excluir_mercado_p2p or not self.es_mercado_p2p(exchange):
                        exchanges.append({
                            'nombre': exchange,
                            'compra': info.get('ask', 0),
                            'venta': info.get('bid', 0)
                        })
            
            self.analizar_oportunidad(exchanges, cripto, pais, moneda, datos_cripto, oportunidades)

    def calcular_arbitraje_internacional(self, pais_origen, pais_destino, datos_origen, datos_destino, oportunidades):
        """Calcula arbitrajes entre diferentes países."""
        moneda_origen = self.monedas_por_pais[pais_origen]
        moneda_destino = self.monedas_por_pais[pais_destino]
        
        for cripto in self.criptos:
            if cripto not in datos_origen or cripto not in datos_destino:
                continue
                
            datos_cripto_origen = datos_origen[cripto]
            datos_cripto_destino = datos_destino[cripto]
            
            # Calcular tipo de cambio entre monedas
            tipo_cambio = self.obtener_tipo_cambio(moneda_origen, moneda_destino, datos_cripto_origen)
            
            exchanges_origen = []
            exchanges_destino = []
            
            # Filtrar exchanges válidos en origen
            for exchange, info in datos_cripto_origen.items():
                if isinstance(info, dict) and 'ask' in info and 'bid' in info:
                    if not self.excluir_mercado_p2p or not self.es_mercado_p2p(exchange):
                        exchanges_origen.append({
                            'nombre': f"{exchange} ({pais_origen})",
                            'compra': info.get('ask', 0),
                            'venta': info.get('bid', 0)
                        })
            
            # Filtrar exchanges válidos en destino
            for exchange, info in datos_cripto_destino.items():
                if isinstance(info, dict) and 'ask' in info and 'bid' in info:
                    if not self.excluir_mercado_p2p or not self.es_mercado_p2p(exchange):
                        exchanges_destino.append({
                            'nombre': f"{exchange} ({pais_destino})",
                            'compra': info.get('ask', 0) * tipo_cambio,
                            'venta': info.get('bid', 0) * tipo_cambio
                        })
            
            # Combinar exchanges para análisis
            todos_exchanges = exchanges_origen + exchanges_destino
            self.analizar_oportunidad(todos_exchanges, cripto, f"{pais_origen}-{pais_destino}", 
                                    moneda_origen, datos_cripto_origen, oportunidades)

    def analizar_oportunidad(self, exchanges, cripto, pais, moneda_base, datos, oportunidades):
        """Analiza oportunidades de arbitraje entre exchanges."""
        for i in range(len(exchanges)):
            for j in range(len(exchanges)):
                if i != j:
                    exchange_compra = exchanges[i]
                    exchange_venta = exchanges[j]
                    
                    if exchange_compra['compra'] <= 0 or exchange_venta['venta'] <= 0:
                        continue
                    
                    # Extraer nombre base del exchange (sin país)
                    nombre_compra = exchange_compra['nombre'].split(' (')[0]
                    nombre_venta = exchange_venta['nombre'].split(' (')[0]
                    
                    mejor_red, fee_blockchain_usd, tiempo_confirmacion = self.encontrar_mejor_red(
                        nombre_compra, nombre_venta, cripto
                    )
                    
                    if not mejor_red:
                        continue
                    
                    # Calcular beneficios y costos
                    precio_compra = exchange_compra['compra']
                    precio_venta = exchange_venta['venta']
                    
                    fee_compra = precio_compra * (self.fees_exchanges.get(nombre_compra, 1.0) / 100)
                    fee_venta = precio_venta * (self.fees_exchanges.get(nombre_venta, 1.0) / 100)
                    
                    # Obtener tipo de cambio USD
                    usd_a_moneda_local = 1
                    if 'dolar' in datos:
                        usd_a_moneda_local = datos['dolar'].get('price', 1)
                    
                    fee_blockchain = fee_blockchain_usd * usd_a_moneda_local
                    beneficio_bruto = precio_venta - precio_compra
                    costos_totales = fee_compra + fee_venta + fee_blockchain
                    beneficio_neto = beneficio_bruto - costos_totales
                    porcentaje_ganancia = (beneficio_neto / precio_compra) * 100
                    
                    if porcentaje_ganancia > self.umbral_ganancia:
                        oportunidades.append({
                            'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'País': pais.capitalize(),
                            'Moneda': moneda_base.upper(),
                            'Cripto': cripto.upper(),
                            'Exchange Compra': exchange_compra['nombre'],
                            'Precio Compra': round(precio_compra, 2),
                            'Exchange Venta': exchange_venta['nombre'],
                            'Precio Venta': round(precio_venta, 2),
                            'Red Blockchain': mejor_red,
                            'Tiempo Conf. (min)': tiempo_confirmacion,
                            'Fee Compra': round(fee_compra, 2),
                            'Fee Venta': round(fee_venta, 2),
                            'Fee Blockchain': round(fee_blockchain, 2),
                            'Beneficio Bruto': round(beneficio_bruto, 2),
                            'Beneficio Neto': round(beneficio_neto, 2),
                            'Ganancia (%)': round(porcentaje_ganancia, 2),
                            'Ganancia USD': round(beneficio_neto / usd_a_moneda_local, 2)
                        })

    def calcular_oportunidades_arbitraje(self):
        """Calcula todas las oportunidades de arbitraje disponibles."""
        oportunidades = []
        
        # Obtener datos de todos los países
        datos_por_pais = {}
        for pais, moneda in self.monedas_por_pais.items():
            datos_por_pais[pais] = {}
            for cripto in self.criptos:
                print(f"Obteniendo datos de {cripto.upper()}/{moneda.upper()} en {pais}...")
                datos = self.obtener_precio(cripto, moneda, pais)
                if datos:
                    datos_por_pais[pais][cripto] = datos

        # Calcular arbitrajes
        for pais_origen, datos_origen in datos_por_pais.items():
            # Arbitraje dentro del mismo país
            self.calcular_arbitraje_local(pais_origen, datos_origen, oportunidades)
            
            # Arbitraje entre países
            for pais_destino, datos_destino in datos_por_pais.items():
                if pais_origen != pais_destino:
                    self.calcular_arbitraje_internacional(
                        pais_origen, pais_destino,
                        datos_origen, datos_destino,
                        oportunidades
                    )
        
        return sorted(oportunidades, key=lambda x: x['Ganancia (%)'], reverse=True)

    def mostrar_resultados(self, oportunidades):
        """Muestra los resultados en forma de tabla."""
        if not oportunidades:
            print("\n¡No se encontraron oportunidades de arbitraje que superen el umbral de ganancia!")
            return
        
        columnas = [
            'Fecha', 'País', 'Cripto', 'Moneda', 
            'Exchange Compra', 'Precio Compra', 
            'Exchange Venta', 'Precio Venta', 
            'Red Blockchain', 'Fee Blockchain',
            'Tiempo Conf. (min)', 'Beneficio Neto', 
            'Ganancia (%)', 'Ganancia USD'
        ]
        
        df = pd.DataFrame(oportunidades)[columnas]
        print("\nOportunidades de Arbitraje Encontradas:")
        print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
    
    def ejecutar_monitoreo_continuo(self):
        """Ejecuta el monitoreo continuo de oportunidades de arbitraje."""
        print("Iniciando monitoreo de oportunidades de arbitraje...")
        
        try:
            while True:
                print("\n" + "="*80)
                print(f"Verificando oportunidades de arbitraje: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*80)
                
                oportunidades = self.calcular_oportunidades_arbitraje()
                self.mostrar_resultados(oportunidades)
                
                print(f"\nEsperando {self.intervalo} segundos hasta la próxima verificación...")
                time.sleep(self.intervalo)
                
        except KeyboardInterrupt:
            print("\nMonitoreo detenido por el usuario.")
        except Exception as e:
            print(f"\nError en el monitoreo: {str(e)}")

# Ejecutar el script
if __name__ == "__main__":
    print("="*80)
    print("DETECTOR DE OPORTUNIDADES DE ARBITRAJE CRIPTO")
    print("="*80)
    
    intervalo = int(input("Intervalo entre verificaciones (segundos) [60]: ") or "60")
    umbral = float(input("Umbral mínimo de ganancia porcentual [0.5]: ") or "0.5")
    
    while True:
        incluir_p2p = input("¿Incluir mercados P2P? (s/n) [n]: ").lower()
        if incluir_p2p in ['s', 'n', '']:
            break
        print("Por favor, ingrese 's' o 'n'")
    
    excluir_mercado_p2p = incluir_p2p != 's'
    
    print("\nConfiguración actual:")
    print(f"- Intervalo: {intervalo} segundos")
    print(f"- Umbral de ganancia: {umbral}%")
    print(f"- Mercados P2P: {'Excluidos' if excluir_mercado_p2p else 'Incluidos'}")
    print("\nPresione Ctrl+C para detener el monitoreo\n")
    
    detector = ArbitrajeDetector(
        intervalo_segundos=intervalo,
        umbral_ganancia=umbral,
        excluir_mercado_p2p=excluir_mercado_p2p
    )
    
    detector.ejecutar_monitoreo_continuo()