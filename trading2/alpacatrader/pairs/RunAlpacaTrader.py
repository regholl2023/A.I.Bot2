#!/usr/bin/env python3
import AlpacaTrader
import pandas as pd

authenticator = AlpacaTrader.Authenticator()
price = AlpacaTrader.GetPrices(authenticator)
price.update()
accountData = AlpacaTrader.AccountData(authenticator)
reporter = AlpacaTrader.Reporter(authenticator)

pairsList = pd.read_csv('data/pairs.csv', header=0, index_col=0)
numPairs = len(pairsList.index)

for index, row in pairsList.iterrows():
    stock1 = AlpacaTrader.Currency(row[0])
    stock2 = AlpacaTrader.Currency(row[1])
    pair = AlpacaTrader.PairsInfo(currency1=stock1, currency2=stock2, ratio2=0.5)
    trade1, trade2, tradeDetails = AlpacaTrader.Decider(pair,numPairs,accountData,authenticator,reporter).tradeit()
    executor = AlpacaTrader.Executor(trade1, trade2, tradeDetails, reporter, authenticator, accountData)
    executor.execute()
    
