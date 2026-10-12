#Uniswap V2 to V3

from defipy import *


    #Uni V2


user_nm = 'user_intro'
eth_amount = 3162.277660168379
dai_amount = 316227.7660168379

dai = ERC20("DAI", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = dai, symbol="LP", 
address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity("user0", eth_amount, dai_amount, eth_amount, dai_amount)
lp.summary()


    #Uni V3


user = 'user_intro'
fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)
init_price = UniV3Utils.encodePriceSqrt(100, 1)

dai = ERC20("DAI", "0x09")
eth = ERC20("ETH", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = dai, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.initialize(init_price)
out = lp.mint(user, lwr_tick, upr_tick, 31622.776601683792)
lp.summary()

    
    #Using GWEI Precision


user = 'user_intro'
fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)
init_price = UniV3Utils.encodePriceSqrt(1, 10)

tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")

exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   precision = UniswapExchangeData.TYPE_GWEI,
                                   fee = fee)

factory = UniswapFactory("TKN pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.initialize(init_price)
lp.mint(user, lwr_tick, upr_tick, 3161)
lp.summary()


    #Using Decimal Precision
        #Uni V3: Mint and Burn


user = 'user_intro'
fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)
init_price = UniV3Utils.encodePriceSqrt(1, 10)

tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")

exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("TKN pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.initialize(init_price)
out = lp.mint(user, lwr_tick, upr_tick, 3162.2776601683795)
lp.summary()

out = lp.burn(user, lwr_tick, upr_tick, 1000)
lp.summary()


    #Uni V3: swapExact0For1 (Correct)


user = 'user_intro'
fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)
init_price = UniV3Utils.encodePriceSqrt(1, 10)

tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")

exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("TKN pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.initialize(init_price)
out = lp.mint(user, lwr_tick, upr_tick, 3162.2776601683795)
lp.summary()

out_v3 = lp.swapExact0For1(user, 100, None)
lp.summary()


    #Uni V2: Comparison Check


tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")
exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user, 10000, 1000, 10000, 1000)
lp.summary()

out_v2 = Swap().apply(lp, tkn, user, 100)
lp.summary()

uni_test = 'PASS' if round(out_v2,8) == round(abs(out_v3[2]),8)  else 'FAIL'
print(f'UniV2 == UniV3 (DAI): {uni_test}')
 

    #Uni V3: swap0ForExact1 (Correct)

user = 'user_intro'
fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)
init_price = UniV3Utils.encodePriceSqrt(1, 10)

tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")

exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("TKN pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.initialize(init_price)
out = lp.mint(user, lwr_tick, upr_tick, 3162.2776601683795)
lp.summary()

out_v3 = lp.swap0ForExact1(user, 100, None)
lp.summary()


    #Uni V2: Comparison Check


tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")
exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user, 10000, 1000, 10000, 1000)
lp.summary()

out_v2 = Swap().apply(lp, tkn, user, 1114.4544745347152)
lp.summary()

uni_test = 'PASS' if round(out_v2,8) == round(abs(out_v3[2]),8)  else 'FAIL'
print(f'UniV2 == UniV3 (DAI): {uni_test}')


    #Uni V3: swapExact1For0 (Correct)


user = 'user_intro'
fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)
init_price = UniV3Utils.encodePriceSqrt(1, 10)

tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")

exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("TKN pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.initialize(init_price)
out = lp.mint(user, lwr_tick, upr_tick, 3162.2776601683795)
lp.summary()

out_v3 = lp.swapExact1For0(user, 100, None)
lp.summary()


    #Uni V2: Comparison Check


tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")
exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user, 10000, 1000, 10000, 1000)
lp.summary()

out_2 = Swap().apply(lp, dai, user, 100)
lp.summary()

uni_test = 'PASS' if round(out_v2,8) == round(abs(out_v3[2]),8)  else 'FAIL'
print(f'UniV2 == UniV3 (TKN): {uni_test}')


    #Uni V3: swap1ForExact0 (Correct)


user = 'user_intro'
fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)
init_price = UniV3Utils.encodePriceSqrt(1, 10)

tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")

exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("TKN pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.initialize(init_price)
out = lp.mint(user, lwr_tick, upr_tick, 3162.2776601683795)
lp.summary()

out_v3 = lp.swap1ForExact0(user, 100, None)
lp.summary()


    #Uni V2: Comparison Check


tkn = ERC20("TKN", "0x111")
dai = ERC20("DAI", "0x09")
exchg_data = UniswapExchangeData(tkn0 = tkn, tkn1 = dai, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user, 10000, 1000, 10000, 1000)
lp.summary()

out_v2 = Swap().apply(lp, dai, user, 10.131404313952)
lp.summary()

uni_test = 'PASS' if round(out_v2,8) == round(abs(out_v3[1]),8)  else 'FAIL'
print(f'UniV2 == UniV3 (TKN): {uni_test}')