from . import defi_tools as dft

df = dft.geckoMarkets("ethereum")
print(df.info())
# returns top 100 ethereum quotes by volume