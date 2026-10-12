from . import defi_tools as dft

# Exercise: Get returns after 20 days, assuming token A is a stablecoin, token B perform + 150%
# individual staking pools for both = 0.01% & 0.05% daily
# liquidity-pool farming rewards =0.2% daily & Earn by fees/day = 0.01%
dft.compare(days=20, var_A=0, var_B=150, rw_pool_A=0.01, rw_pool_B=0.05, rw_pool_AB=0.2, fees_AB=0.01)
{
 "buy_hold": "75.00%",
 "stake": "75.60%",
 "farm": "71.96%",
 "Best": "Stake"
}