import riskfolio as rp
import inspect
import pandas as pd

# Create a dummy portfolio
dummy_data = pd.DataFrame()
port = rp.Portfolio(dummy_data)

# Get the signature
sig = inspect.signature(port.assets_stats)
print("assets_stats signature:")
print(sig)
print("\nDocstring:")
print(port.assets_stats.__doc__)
