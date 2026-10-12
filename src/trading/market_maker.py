import pyRofex
import enum
import config1

#LO PRIMERO DEFINO ESTADOS POR LO QUE PUEDE ESTAR LA ESTRATEGIA, ESTO ME SIRVE PARA SABER EN DONDE ESTOY PARADO ACTUALMENTE, O QUE ES LO QUE ESTA HACIENDO EL BOT
class States(enum.Enum):
    WAITING_MARKET_DATA = 0 #ESPERANDO LA DATA DEL MERCADO
    WAITING_CANCEL = 1 #CANCELO ORDENES PARA LIMPIAR POR CUALQUIER COSA
    WAITING_ORDERS = 2 #PRIMERO SI ENVIO ORDENES ESPERO A QUE ME CONTESTE EL MERCADO ANTES DE VOLVER A ENVIAR ORDENES

# LA VENTAJA DE HACER ESTRATEGIA EN CLASE ES QUE UNO PUEDE REPLICAR EL CODIGO FACILMENTE EN IF __NAME__ == usando otros instrumentos
class MyStrategy:

    def __init__(self, instrument, size, spread): #iniciliza la estrategia con instrumento size y spread
        # Define variables
        self.instrument = instrument
        self.instrument1 = instrument1
        self.comision = 0
        self.initial_size = size
        self.buy_size = size  #definir size para que se vaya actualizando cada vez que me operen, 
        self.sell_size = size
        self.spread = spread #definir spread
        self.tick = 1 #fijarse cual es el tick minimo 
        self.my_order = dict()
        self.last_md = None
        self.state = States.WAITING_MARKET_DATA #estado inicial con el que arranca la estretia es esperando market data



        # inicializar la coneccion websocket y cuando llegue a market data llamar a estos dos parametros que es una funcion interna de la estrategia
        pyRofex.init_websocket_connection(
            market_data_handler=self.market_data_handler,
            order_report_handler=self.order_report_handler
        )

        # se subscribe a market data del instrumento que defini (bid y offer)
        pyRofex.market_data_subscription(
            tickers=[
                self.instrument,
                self.instrument1
            ],
            entries=[
                pyRofex.MarketDataEntry.BIDS,
                pyRofex.MarketDataEntry.OFFERS
            ]
        )

        # se subscribe 
        pyRofex.order_report_subscription()

    # lo primero que recibe es un mensaje de market data.
    def market_data_handler(self, message):
        if self.state is States.WAITING_MARKET_DATA: #si estoy en el estado de "waiting market data, esperando la data del mercado"
            print("Estoy esperando la data del mercado: {0}".format(message)) 
            self.last_md = None #si ya tengo market data, lo pongo en none cosa de que ya se que procese el ultimo mensaje de market data
            bid = message["marketData"]["BI"] #pedir bid , como es un diccionario [marketData] pido solamente ["BI"]
            offer = message["marketData"]["OF"] #pedir offer , lo mismo que arriba
            if bid and offer: #como el bid y offer puede venir vacio, primero chequeo que el bid y el ofer sean positivos, es decir, que haya un bid y un offer cargado y si es que lo tengo:↓
                bid_px = bid[0]["price"] #me fijo el precio del mejor bid
                offer_px = offer[0]["price"] #me fijo el precio del mejor offer
                bid_offer_spread = round(offer_px - bid_px, 6) - 0.002 #calculo un spread : me fijo la diferencia entre offer y bid
                if bid_offer_spread >= self.spread: #si esta diferencia es mayor al spread que habiamos definido 
                    if self.my_order: #aca tiene que chequear cosas , tenemos que ver si tenemos ordenes en el mercado o no, porque puede ser que tengmaos ordenes , nos mejoran el precio , el spread sigue siendo positivo , y tenemos que mejorar la orden
                        for order in self.my_order.values(): #por cada orden que tengamos nos fijamos si nos mejoraron el precio 
                            if order["orderReport"]["side"] == "BUY" and \
                                    order["orderReport"]["price"] < bid_px:# si el precio de mi orden es menor es porque alguien me mejoro la oferta que yo hice y la mando a mejorar de vuelta
                                self._send_order(pyRofex.Side.BUY, bid_px + self.tick, self.buy_size)
                            elif order["orderReport"]["side"] == "SELL" and \
                                    order["orderReport"]["price"] > offer_px:#lo mismo para la orden de venta
                                self._send_order(pyRofex.Side.SELL, offer_px - self.tick, self.sell_size) #mando a mejorar de vuelta
                    else: #y si no tenemos ordenes hacemos lo siguiente
                        if self.buy_size > 0: #manda a comprar de acuerdo a lo que setie en el tick minimo , un tick por encima por una cantidad que yo defini , si me operaron todo de un lado pero el otro todavia sigue con posicion el size que esta en 0 no me va a mandar nada 
                            self._send_order(pyRofex.Side.BUY, bid_px + self.tick, self.buy_size)
                        if self.sell_size > 0: #manda a vender de acuerdo a lo que vendi en el tick minimo , si me operaron todo de un lado pero el otro todavia sigue con posicion el size que esta en 0 no me va a mandar nada, y el type  que todavia tenga posicion me va a mandar a vender al mejor precio
                            self._send_order(pyRofex.Side.SELL, offer_px - self.tick, self.sell_size)
                else:  # Lower spread
                    self._cancel_if_orders() #llegado al caso de que el spread es menor, mando a cancelar las ordenes 
            else:
                self._cancel_if_orders() #si en el caso que no exista un bid o offer cargado, mando a cancelar las ordenes (la funcion esta definida mas abajo en linea 118)
        else: #y si no estoy en el mercado de market data, voy almacenando el ultimo mensaje de market data cosa que despues si lo necesito vuelvo a hacer todo lo de arriba
            self.last_md = message

    # Defines the handlers that will process the Order Reports.
    def order_report_handler(self, order_report): 
        print("Order Report Message Received: {0}".format(order_report))
        if order_report["orderReport"]["clOrdId"] in self.my_order.keys(): #aca chequeo si las ordenes que me llego aca, se una de las que YO mande
            self._update_size(order_report) #actualizo el size , le paso el mensaje de la orden (linea 109)
            if order_report["orderReport"]["status"] in ("NEW", "PARTIALLY_FILLED"):  
                print("processing new order")
                self.my_order[order_report["orderReport"]["clOrdId"]] = order_report
            elif order_report["orderReport"]["status"] == "FILLED":
                print("processing filled")
                del self.my_order[order_report["orderReport"]["clOrdId"]] #si la orden se me opero, borro la orden de mis ordenes porque ya no esta mas activa
            elif order_report["orderReport"]["status"] == "CANCELLED":
                print("processing cancelled")
                del self.my_order[order_report["orderReport"]["clOrdId"]] #y lo mismo que filled    

            if self.state is States.WAITING_CANCEL: #si estoy en el estado de cancel order me fijo que no tenga mas ordenes activas 
                if not self.my_order:
                    self.state = States.WAITING_MARKET_DATA 
                    if self.last_md:
                        self.market_data_handler(self.last_md) 
            elif self.state is States.WAITING_ORDERS: #si estoy ene l estado de esperando ordenes
                for order in self.my_order.values():
                    if not order: #si no tienen un estado, return
                        return
                self.state = States.WAITING_MARKET_DATA 
                if self.last_md:
                    self.market_data_handler(self.last_md)

    def _update_size(self, order): #lo llamo cuando recibo una orden
        if order["orderReport"]["status"] in ("PARTIALLY_FILLED", "FILLED"): #si se me opero la orden , parcialmente o completa
            if order["orderReport"]["side"] == "BUY":
                self.buy_size -= round(order["orderReport"]["lastQty"]) #aca descuento la cantidad 
            if order["orderReport"]["side"] == "SELL":
                self.sell_size -= round(order["orderReport"]["lastQty"])
            if self.sell_size == self.buy_size == 0: #si vendi todo lo que tenia en el total de size de compra y size de venta, incializo de vuelta el size, de esta manera me aseguro que no se vendan los nominales, no voy a volver a cotizar otros nominales
                self.sell_size = self.buy_size = self.initial_size

    def _cancel_if_orders(self): 
        if self.my_order: #aca se fija en el diccionario donde voy guardando mis ordenes , y si ese diccionario esta vacio, es porque no tengo ordenes en el mercado, y si tengo ordenes hago lo siguiente
            self.state = States.WAITING_CANCEL #cancelo todas las ordenes
            for order in self.my_order.values():
                pyRofex.cancel_order(order["orderReport"]["clOrdId"]) #aca precisamente cancelo
                print("cancelando ordenes %s" % order["orderReport"]["clOrdId"])

    def _send_order(self, side, px, size): #utiliza la libreria de pyrofex para enviar la orden
        self.state = States.WAITING_ORDERS
        order = pyRofex.send_order(
            ticker=self.instrument,
            side=side,
            size=size,
            price=round(px, 6),
            order_type=pyRofex.OrderType.LIMIT,
            cancel_previous=True
        )
        self.my_order[order["order"]["clientId"]] = None
        print("sending %s order %s@%s - id: %s" % (side, size, px, order["order"]["clientId"]))


if __name__ == "__main__":
    MyStrategy("MERV - XMEV - AL30 - 48hs", 700, 10 )
    #MyStrategy("MERV - XMEV - AL30C - 48hs", 1, 2)
#si arranque con 10 nominales, me operan 5, ese size se transforma en 5, y asi hasta llegar a 0 hasta que los size (buy y sell) terminan en 0