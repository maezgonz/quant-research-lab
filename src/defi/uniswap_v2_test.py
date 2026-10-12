from defipy import *

user_nm = 'user0'
eth_amount = 1000
tkn_amount = 100000

#Swap()
    #tkn0 for tkn1


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

out = Swap().apply(lp, tkn, user_nm, 1000)
lp.summary()


    #tkn1 for tkn0


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

out = Swap().apply(lp, eth, user_nm, 10)
lp.summary()


    #swap lp token for tkn1


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = lp_tkn.total_supply
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, lp_tkn_amount, tkn_amount, lp_tkn_amount, tkn_amount)
lp2.summary()

out = Swap().apply(lp2, lp_tkn, user_nm, 100)
lp2.summary()


    #swap lp token for tkn0


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = lp_tkn.total_supply
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, lp_tkn_amount, tkn_amount, lp_tkn_amount, tkn_amount)
lp2.summary()

out = Swap().apply(lp2, tkn2, user_nm, 100)
lp2.summary()


#AddLiquidity()
    #add tkn1 and determine tkn0


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

AddLiquidity().apply(lp, eth, user_nm, 10)
lp.summary()


    #add tkn0 and determine tkn1


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

AddLiquidity().apply(lp, tkn, user_nm, 1000)
lp.summary()
lp.liquidity_providers


    #add LP based on tkn2


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = lp_tkn.total_supply
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, lp_tkn_amount, tkn_amount, lp_tkn_amount, tkn_amount)
lp2.summary()

AddLiquidity().apply(lp2, tkn2, user_nm, 10)
lp2.summary()


    #add LP based on lp_tkn


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = lp_tkn.total_supply
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, lp_tkn_amount, tkn_amount, lp_tkn_amount, tkn_amount)
lp2.summary()

AddLiquidity().apply(lp2, lp_tkn, user_nm, 10)
lp2.summary()


#RemoveLiquidity()
    #remove tkn1 and determine tkn0


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

RemoveLiquidity().apply(lp, eth, user_nm, 999)
lp.summary()


    #remove tkn0 and determine tkn1


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

RemoveLiquidity().apply(lp, tkn, user_nm, 100)
lp.summary()


    #remove LP based on tkn2


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = 1000
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, eth_amount, lp_tkn_amount, eth_amount, lp_tkn_amount)
lp2.summary()

RemoveLiquidity().apply(lp2, tkn2, user_nm, 10)
lp2.summary()


    #remove LP based on lp_tkn


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = 1000
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, eth_amount, lp_tkn_amount, eth_amount, lp_tkn_amount)
lp2.summary()

RemoveLiquidity().apply(lp2, lp_tkn, user_nm, 10)
lp2.summary()


#SwapDeposit()
    #swap exact tkn1 for tkn0
    #deposit desired token -> perform 50% swap -> perform 50/50 deposit


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

SwapDeposit().apply(lp, tkn, user_nm, 100)
lp.summary() 


    #swap exact tkn0 for tkn1
    #deposit desired token -> perform 50% swap -> perform 50/50 deposit


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

amount_out = SwapDeposit().apply(lp, eth, user_nm, 1)
lp.summary()


    #deposit LP with only tkn2
    #deposit desired token -> perform 50% swap -> perform 50/50 deposit


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, eth_amount, lp_tkn_amount, eth_amount, lp_tkn_amount)
lp2.summary()

SwapDeposit().apply(lp2, tkn2, user_nm, 10)
lp2.summary() 


    #deposit LP with only lp_tkn
    #deposit desired token -> perform 50% swap -> perform 50/50 deposit


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = 1000
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, eth_amount, lp_tkn_amount, eth_amount, lp_tkn_amount)
lp2.summary()

SwapDeposit().apply(lp2, lp_tkn, user_nm, 10)
lp2.summary() 


#WithdrawSwap()
    #withdraw exact tkn1
    #withdraw LP based upon expected amount of eth
    #perform 50/50 withdraw -> swap remaining 50% -> return desired token


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

expected_amount_out = WithdrawSwap().apply(lp, eth, user_nm, 1)
lp.summary()

    #withdraw exact tkn0
    #withdraw LP based upon expected amount of tkn


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp = factory.deploy(exchg_data)
lp.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp.summary()

expected_amount_out = WithdrawSwap().apply(lp, tkn, user_nm, 100)
lp.summary()


    #withdraw LP based upon expected amount of tkn2
    #perform 50/50 withdraw -> swap remaining 50% -> return desired token


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = 1000
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, eth_amount, lp_tkn_amount, eth_amount, lp_tkn_amount)
lp2.summary()

WithdrawSwap().apply(lp2, tkn2, user_nm, 10)
lp2.summary() 


    #withdraw LP based upon expected amount of tkn2
    #perform 50/50 withdraw -> swap remaining 50% -> return desired token


tkn = ERC20("TKN", "0x111")
eth = ERC20("ETH", "0x09")
exchg_data = UniswapExchangeData(tkn0 = eth, tkn1 = tkn, symbol="LP", address="0x011")

factory = UniswapFactory("ETH pool factory", "0x2")
lp_tkn = factory.deploy(exchg_data)
lp_tkn.add_liquidity(user_nm, eth_amount, tkn_amount, eth_amount, tkn_amount)
lp_tkn.summary()

tkn2 = ERC20("TKN", "0x112")
lp_tkn_amount = 1000
exchg_data = UniswapExchangeData(tkn0 = lp_tkn, tkn1 = tkn2, symbol="LP2", address="0x012")
lp2 = factory.deploy(exchg_data)
lp2.add_liquidity(user_nm, eth_amount, lp_tkn_amount, eth_amount, lp_tkn_amount)
lp2.summary()

WithdrawSwap().apply(lp2, lp_tkn, user_nm, 10)
lp2.summary() 