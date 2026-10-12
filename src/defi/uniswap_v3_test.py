#Abstract Interface (V3)
    #Join(): joins X and Y amounts to pool
    #Swap(): swaps X for Y (and vice verse)
    #AddLiquidity(): adds liquidity using only X or Y amounts
    #RemoveLiquidity(): removes liquidity using only X or Y amounts
    #SwapDeposit(): deposit desired token -> perform approx. 50% swap -> perform approx. 50/50 deposit (exact percentages are calculated)
    #WithdrawSwap(): perform approx. 50/50 withdraw -> swap remaining approx. 50% -> return desired token (exact percentages are calculated)


from defipy import *

user_nm = 'user0'
eth_amount = 1000
tkn_amount = 100000

fee = UniV3Utils.FeeAmount.MEDIUM
tick_spacing = UniV3Utils.TICK_SPACINGS[fee]
lwr_tick = UniV3Utils.getMinTick(tick_spacing)
upr_tick = UniV3Utils.getMaxTick(tick_spacing)

#Join()
    #joins tkn0 and tkn1 amounts to pool


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

out_v3 = Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()
 

#Swap()
    #tkn0 for tkn1


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

out_v3 = Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

out = Swap().apply(lp, tkn, user_nm, 1000)
lp.summary()


    #tkn1 for tkn0

eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

out_v3 = Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

out = Swap().apply(lp, eth, user_nm, 10)
lp.summary()


#AddLiquidity()
    #add tkn1 and determine tkn0


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

out_v3 = Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

AddLiquidity().apply(lp, tkn, user_nm, 1000, lwr_tick, upr_tick)
lp.summary()


    #add tkn0 and determine tkn1


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

out_v3 = Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

AddLiquidity().apply(lp, eth, user_nm, 100, lwr_tick, upr_tick)
lp.summary()


#RemoveLiquidity()
    #remove tkn1 and determine tkn0


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

out_v3 = Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

RemoveLiquidity().apply(lp, tkn, user_nm, 1000, lwr_tick, upr_tick)
lp.summary()


    #remove tkn0 and determine tkn1


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

out_v3 = Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

RemoveLiquidity().apply(lp, eth, user_nm, 10, lwr_tick, upr_tick)
lp.summary()


#SwapDeposit()
    #swap exact tkn1 for tkn0
    #deposit desired token -> perform 50% swap -> perform 50/50 deposit
    
eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

SwapDeposit().apply(lp, tkn, user_nm, 100, lwr_tick, upr_tick)
lp.summary() 


    #swap exact tkn0 for tkn1
    #deposit desired token -> perform 50% swap -> perform 50/50 deposit


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

SwapDeposit().apply(lp, eth, user_nm, 10, lwr_tick, upr_tick)
lp.summary() 


#WithdrawSwap()
    #withdraw exact tkn1
    #withdraw LP based upon expected amount of eth
    #perform 50/50 withdraw -> swap remaining 50% -> return desired token


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

WithdrawSwap().apply(lp, eth, user_nm, 1, lwr_tick, upr_tick)
lp.summary()


    #withdraw exact tkn0
    #withdraw LP based upon expected amount of tkn


eth = ERC20("ETH", "0x09")
tkn = ERC20("TKN", "0x111")

exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", 
                                   address="0x011", version = 'V3', 
                                   tick_spacing = tick_spacing, 
                                   fee = fee)

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)

Join().apply(lp, user_nm, eth_amount, tkn_amount, lwr_tick, upr_tick)
lp.summary()

expected_amount_out = WithdrawSwap().apply(lp, tkn, user_nm, 100,lwr_tick, upr_tick)
lp.summary()