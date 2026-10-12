from . import defi_tools as dft

# Impermanent loss for stableCoin & -20% return token 
dft.iloss(0.8)

# Impermanent loss for stableCoin & +60% return token 
dft.iloss(1.6, numerical=True)

