import os
import json
import numpy as np

from defipy import *

############## Benchmarks ##############

cwd =  os.getcwd().replace("notebooks","")
os.chdir(cwd)
actions_json = 'resources/dev/cwpt/0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a-actions-prices.json'
with open(actions_json, "r") as f:
    pool_actions = json.load(f)

USER = 'user_test'

amt_dai = 10000000
denorm_wt_dai = 10

amt_eth = 67738.6361731024
denorm_wt_eth = 40

init_pool_shares = 100

############## Join balancer pool ##############

dai = ERC20("DAI", "0x111")
dai.deposit(None, amt_dai)

weth = ERC20("WETH", "0x09")
weth.deposit(None, amt_eth)

bgrp = BalancerVault()
bgrp.add_token(dai, denorm_wt_dai)
bgrp.add_token(weth, denorm_wt_eth)

bfactory = BalancerFactory("WETH pool factory", "0x2")
exchg_data = BalancerExchangeData(vault = bgrp, symbol="LP", address="0x011")
lp = bfactory.deploy(exchg_data)
lp.join_pool(bgrp, init_pool_shares, USER)
lp.summary()

############## Price ##############

p = lp.get_price(dai, weth)

print(f"The price of {weth.token_name} is {p} {dai.token_name}")

############## Swap (out-given-in) ##################

amt_tkn_in = float(pool_actions[3]['action']['token_in']['amount'])
tkn_in = dai
tkn_out = weth
res = lp.swap_exact_amount_in(amt_tkn_in, tkn_in, tkn_out, USER)

print(f"{amt_tkn_in} {tkn_in.token_name} was swapped into {res['tkn_out_amt']} {tkn_out.token_name}")

lp.summary()

############## Swap (in-given-out) ##################

amt_tkn_out = res['tkn_out_amt']
tkn_out = weth
tkn_in = dai

res = lp.swap_exact_amount_out(amt_tkn_out, tkn_out, tkn_in, USER)

print(f"{amt_tkn_out} {tkn_out.token_name} was swapped into {res['tkn_in_amt']} {tkn_in.token_name}")

############## Add liquidity (based on token amounts) ##############

tkn_in = weth
amt_tkn_in = float(pool_actions[336]['action']['token_in']['amount'])

res = lp.join_swap_extern_amount_in(amt_tkn_in, tkn_in, USER)

print(f"{amt_tkn_in} {tkn_in.token_name} was added resulting in anadditional {res['shares_in_amt']} LP shares")

lp.summary()

############## Add liquidity (based on LP share amounts) ##############

tkn_in = weth
amt_shares_in = 10

res = lp.join_swap_pool_amount_out(amt_shares_in, tkn_in, USER)

print(f"{amt_shares_in} LP shares were added resulting in an additional {res['tkn_in_amt']} {tkn_in.token_name}")

lp.summary()

############## Remove liquidity (based on token amounts) ##############

tkn_out = weth
amt_tkn_out = float(pool_actions[664]['action']['token_out']['amount'])

res = lp.exit_swap_extern_amount_out(amt_tkn_out, tkn_out, USER)

print(f"{amt_tkn_out} {tkn_out.token_name} was removed resulting in the removal of {res['shares_out_amt']} LP shares")

lp.summary()

############## Remove liquidity (based on LP share amounts) ##############

tkn_out = weth
amt_shares_out = 10

res = lp.exit_swap_pool_amount_in(amt_shares_out, tkn_out, USER)

print(f"{amt_shares_out} LP shares were removed resulting in the removal of {res['tkn_out_amt']} {tkn_out.token_name}")

lp.summary()



