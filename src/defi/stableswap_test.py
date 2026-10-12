######## Basic Composable Stable Testing and Overview ########

import json
import numpy as np
from decimal import Decimal
from defipy import *

##Parameters

USER = 'user_test'

AMPL_COEFF = 2000 

amt_dai = 79566307.559825807715868071
decimal_dai = 18

amt_usdc = 81345068.187939
decimal_usdc = 6

amt_usdt = 55663250.772939
decimal_usdt = 6

##Tokens

dai = ERC20("DAI", "0xA0b", decimal_dai)
dai.deposit(None, amt_dai)

usdc = ERC20("USDC", "0xf93", decimal_usdc)
usdc.deposit(None, amt_usdc)

usdt = ERC20("USDT", "0xd7c", decimal_usdt)
usdt.deposit(None, amt_usdt)
sgrp = StableswapVault()
sgrp.add_token(dai)
sgrp.add_token(usdc)
sgrp.add_token(usdt)

######## Join Stableswap Pool with all Assets ########

sfactory = StableswapFactory("Pool factory", "0x2")
exchg_data = StableswapExchangeData(vault = sgrp, symbol="LP", address="0x011")
lp = sfactory.deploy(exchg_data)
lp.join_pool(sgrp, AMPL_COEFF, USER)
lp.summary()

######## Price: USDC/DAI and DAI/USDC ########

p_usdc_dai = lp.get_price(usdc, dai)
p_dai_usdc = lp.get_price(dai, usdc)

print(f'Price of USDC/DAI is {p_usdc_dai} and DAI/USDC is {p_dai_usdc}')

######## Swap: USDC -> USDT ########

usdc_before = lp.get_reserve(usdc)
usdt_before = lp.get_reserve(usdt)

amt_tkn_in = 10000
tkn_in = usdc
tkn_out = usdt
res = lp.swap(amt_tkn_in, tkn_in, tkn_out, USER)

print(f"{amt_tkn_in} {tkn_in.token_name} was swapped for {res['tkn_out_amt']} {tkn_out.token_name}")

lp.summary()

######## Check for leaks ########
usdc_check = lp.get_reserve(usdc)-amt_tkn_in
usdt_check = lp.get_reserve(usdt)+res['tkn_out_amt']

usdc_test = 'PASS' if {usdc_before == usdc_check} else 'FAIL'
usdt_test = 'PASS' if {usdt_before == usdt_check} else 'FAIL'
print(f'Liquidity Leak (USDC): {usdc_test}')
print(f'Liquidity Leak (USDT): {usdt_test}')

######## Swap: USDC -> DAI ########

usdc_before = lp.get_reserve(usdc)
dai_before = lp.get_reserve(dai)

amt_tkn_in = 10000
tkn_in = usdc
tkn_out = dai
res = lp.swap(amt_tkn_in, tkn_in, tkn_out, USER)

print(f"{amt_tkn_in} {tkn_in.token_name} was swapped for {res['tkn_out_amt']} {tkn_out.token_name}")

lp.summary()

######## Check for leaks ########

usdc_check = lp.get_reserve(usdc)-amt_tkn_in
dai_check = lp.get_reserve(dai)+res['tkn_out_amt']

usdc_test = 'PASS' if {usdc_before == usdc_check} else 'FAIL'
dai_test = 'PASS' if {dai_before == dai_check} else 'FAIL'
print(f'Liquidity Leak (USDC): {usdc_test}')
print(f'Liquidity Leak (DAI): {dai_test}')

######## Add Liquidity: USDT ########

usdt_before = lp.get_reserve(usdt)

amt_tkn_in = 10000
tkn_in = usdt
res = lp.add_liquidity(amt_tkn_in, tkn_in, USER)

print(f"{amt_tkn_in} {tkn_in.token_name} was deposited for {res['liquidity_amt_in']} LP tokens")

lp.summary()

######## Check for leaks ########

usdt_check = lp.get_reserve(usdt)-amt_tkn_in

usdt_test = 'PASS' if {usdt_before == usdc_check} else 'FAIL'
print(f'Liquidity Leak (USDT): {usdt_test}')

######## Add Liquidity: DAI ########

amt_tkn_in = 10000
tkn_in = dai
dai_before = lp.get_reserve(dai)
res = lp.add_liquidity(amt_tkn_in, tkn_in, USER)

print(f"{amt_tkn_in} {tkn_in.token_name} was deposited for {res['liquidity_amt_in']} LP tokens")

lp.summary()

########  Check for leaks ########

dai_check = lp.get_reserve(dai)-amt_tkn_in

dai_test = 'PASS' if {dai_before == dai_check} else 'FAIL'
print(f'Liquidity Leak (USDT): {dai_test}')

######## Remove Liquidity: DAI ########

amt_lp_out = 250000
tkn_out = dai
dai_before = lp.get_reserve(dai)
lp_amt_before = lp.total_supply
res = lp.remove_liquidity(amt_lp_out, tkn_out, USER)

print(f"{amt_lp_out} LP tokens as removed for {res['tkn_out_amt']} {tkn_out.token_name}")

lp.summary()

######## Check for leaks ########

dai_check = lp.get_reserve(dai)-res['tkn_out_amt']
lp_amt_check = lp.total_supply - amt_lp_out

dai_test = 'PASS' if {dai_before == dai_check} else 'FAIL'
lp_amt_test = 'PASS' if {lp_amt_before == lp_amt_check} else 'FAIL'
print(f'Liquidity Leak (DAI): {dai_test}')
print(f'Liquidity Leak (LP AMT): {lp_amt_test}')

######## Remove Liquidity: USDC ########

amt_lp_out = 500000
tkn_out = usdc
usdc_before = lp.get_reserve(usdc)
lp_amt_before = lp.total_supply
res = lp.remove_liquidity(amt_lp_out, tkn_out, USER)

print(f"{amt_lp_out} LP tokens as removed for {res['tkn_out_amt']} {tkn_out.token_name}")

lp.summary()

## Check for leaks
usdc_check = lp.get_reserve(usdc)-res['tkn_out_amt']
lp_amt_check = lp.total_supply - amt_lp_out

usdc_test = 'PASS' if {usdc_before == usdc_check} else 'FAIL'
lp_amt_test = 'PASS' if {lp_amt_before == lp_amt_check} else 'FAIL'
print(f'Liquidity Leak (USDC): {usdc_test}')
print(f'Liquidity Leak (LP AMT): {lp_amt_test}')

######## Remove Liquidity: USDT ########

amt_lp_out = 500000
tkn_out = usdt
usdt_before = lp.get_reserve(usdt)
lp_amt_before = lp.total_supply
res = lp.remove_liquidity(amt_lp_out, tkn_out, USER)

print(f"{amt_lp_out} LP tokens as removed for {res['tkn_out_amt']} {tkn_out.token_name}")

lp.summary()

## Check for leaks
usdt_check = lp.get_reserve(usdt)-res['tkn_out_amt']
lp_amt_check = lp.total_supply - amt_lp_out

usdt_test = 'PASS' if {usdt_before == usdt_check} else 'FAIL'
lp_amt_test = 'PASS' if {lp_amt_before == lp_amt_check} else 'FAIL'
print(f'Liquidity Leak (USDT): {usdt_test}')
print(f'Liquidity Leak (LP AMT): {lp_amt_test}')

######## Check Exchange / Math Pool / Token Balances ########

math_pool = lp.get_math_pool()
tkn_decimal_amts = sgrp.get_decimal_amts()
lp_test = 'PASS' if {lp.total_supply == round(math_pool.tokens/10**18,6)} else 'FAIL'
print(f'Math Pool LP tkn balance == LP tkn balance: {lp_test}')

for k, tkn_nm in enumerate(lp.tkn_reserves):
    tkn = sgrp.get_token(tkn_nm)
    tkn_balance = tkn.token_total
    tkn_math_pool_balance = float(Decimal(str(math_pool.balances[k]))/Decimal(str(10**tkn.token_decimal))) 
    assert round(tkn_balance,5) == round(tkn_math_pool_balance,5), f'ERROR: {tkn_nm} TOKEN VALUE DOES NOT MATCH WITH MATH POOL'
    print(f'Math pool [{tkn_nm}] balance == [{tkn_nm}] balance: PASS ')

for k, tkn_nm in enumerate(lp.tkn_reserves):
    tkn = sgrp.get_token(tkn_nm)
    tkn_balance = lp.tkn_reserves[tkn_nm]
    tkn_math_pool_balance = float(Decimal(str(math_pool.balances[k]))/Decimal(str(10**tkn.token_decimal))) 
    assert round(tkn_balance,5) == round(tkn_math_pool_balance,5), f'ERROR: {tkn_nm} TOKEN VALUE DOES NOT MATCH WITH MATH POOL'
    print(f'Math pool [{tkn_nm}] balance == Reserve [{tkn_nm}] balance: PASS [{tkn_nm}]')

for k, tkn_nm in enumerate(tkn_decimal_amts):
    tkn = sgrp.get_token(tkn_nm)
    tkn_balance = float(Decimal(str(tkn_decimal_amts[tkn_nm]))/Decimal(str(10**tkn.token_decimal)))  
    tkn_math_pool_balance = float(Decimal(str(math_pool.balances[k]))/Decimal(str(10**tkn.token_decimal))) 
    assert round(tkn_balance,5) == round(tkn_math_pool_balance,5), f'ERROR: {tkn_nm} TOKEN VALUE DOES NOT MATCH WITH MATH POOL'
    print(f'Math pool [{tkn_nm}] balance == Group [{tkn_nm}] balance: PASS [{tkn_nm}] ')