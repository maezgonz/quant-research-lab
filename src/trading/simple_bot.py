import requests, json as j, pandas as pd, time

# Ejercicio didactico de un taller dictado en Digital House para mujeres traders
# La idea es ver la lógica de un bot de trading, no tiene aplicación real es solo a fines didácticos de mostrar la idea

def getData(s):
    url = "https://min-api.cryptocompare.com/data/v2/histominute?fsym="+s
    url += "&tsym=USD&limit=100&e=bitstamp"
    json = j.loads(requests.get(url = url, timeout=15).text)
    df = pd.DataFrame(json['Data']['Data']).dropna()
    return df

def sma(serie,ruedas,nombreColumna):
    rta=pd.DataFrame({nombreColumna:[]})
    i = 0
    for valor in serie:
        if(i >= ruedas):
            promedio = sum(serie[i-ruedas+1:i+1])/ruedas
            rta.loc[i] = promedio
        i = i+1
    return rta         

def getTabla(simbolo,nRapida,nLenta):
    data = getData(simbolo)
    rapidas = sma(data['close'],nRapida,"rapida")
    lentas = sma(data['close'],nLenta,"lenta")
    #alternativa version de pandas para media: lentas = datos['close'].rolling(nLenta).mean().dropna()
    tabla = rapidas.join(lentas).join(data['close']).dropna().reset_index()
    return tabla

def accion(cruce, pos, precio):
    if(cruce>1):
        if (pos=="Wait"):
            print("--Buy Order $"+str(precio)+"--")
        pos = "hold"
    else:
        if (pos=="hold"):
            print("--Sell Order $"+str(precio)+"--")
        pos = "Wait"       
    return pos

pos = "Wait"
while True:
    tabla = getTabla("BTC",10,20)
    cruce = tabla['rapida'].iloc[-1] / tabla['lenta'].iloc[-1]
    precio = tabla['close'].iloc[-1]
    pos = accion(cruce, pos, precio)
    print(pos+" $" +str(precio) )
    time.sleep(60)    