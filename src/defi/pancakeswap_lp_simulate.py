from . import defi_tools as dft
dft.value_f, iloss = dft.iloss_simulate('cake','bnb', value=1000, base_pct_chg=50, quote_pct_chg=-25)
