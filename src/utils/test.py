import SHDA
import pygsheets
import pandas as pd

# Autenticación con las credenciales de la API
gc = pygsheets.authorize(service_account_file='ruta/a/tu/credencial.json')

# Abre una hoja de cálculo existente por nombre
sh = gc.open('nombre_de_tu_hoja')

# Selecciona la primera hoja
worksheet = sh.sheet1
import SHDA

host = 81#Mismos numeros de broker que PyHomeBroker
dni = ""
user = ""
password = ""
comitente=""  # Numero de comitente


hb=SHDA.SHDA(host,dni,user,password)

df=hb.get_bluechips("48hs")
df=df._append(get_options("48hs"), ignore_index=True)

# Escribir el DataFrame en la hoja de cálculo comenzando en la celda A1
worksheet.set_dataframe(df, (1, 1))

# Ajustar el ancho de las columnas
worksheet.adjust_column_width(start=1, end=len(df.columns))
