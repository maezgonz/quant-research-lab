from . import defi_tools as dft

pair = ['huobi-token','tether']
apr = 45

dft.farmSimulate(pair, apr, start='2021-01-01')