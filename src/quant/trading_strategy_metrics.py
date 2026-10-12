##Trading Strategy Performance Matrices using ffn (Financial functions for Python)
##Overview: ffn is a library that contains many useful functions for performance measurement and evaluation of backtesting of Qunatitative Trading Strategies
## Install: pip install ffn - Documentation: Read the docs at http://pmorissette.github.io/ffn

# importing libraries
import pandas as pd
import numpy as np
import ffn
#%matplotlib inline

#creating a dataframe
num_days = 1000
data = (np.random.randn(num_days) + np.random.uniform(low=0.0, high=0.2, size=num_days))
index = pd.date_range('01/01/2010',periods=num_days, freq='D')
data = pd.DataFrame(data,index=index,columns=['Returns'])

#creating a trading account name 'Equity' with a starting capital of 100
data['Equity'] = data.cumsum()+ 100
data.iloc[0] = 100

data