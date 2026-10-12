from . import defi_tools as dft
import pandas as pd

exchanges = ['pancakeswap', 'curve', 'makerdao', 'uniswap','Compound', 'AAVE','sushiswap','anchor']

hist = [dft.getProtocol(exchange)[1] for exchange in exchanges]
df = pd.concat(hist, axis=1)
df.columns = exchanges

df.plot(figsize=(12,6))
