"""
Generic code for backtesting different strategies. Include indicators.py and strategies.py to customize backtest.
"""

import sys
import pandas as pd
import numpy as np

from actions import Action
from strategies import Macd, Rsi, Stochastic_Rsi, ParabolicSAR


if __name__ == "__main__":
    symbol = 'AAPL'
    period = 'day'
    cash = 1000
    wins = 0
    losses = 0
    holding = (0, 0)

    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    if len(sys.argv) > 2:
        period = sys.argv[2]
    if len(sys.argv) > 4:
        if sys.argv[4] == 'long':
            period += '/long'

    # read historical data
    data = pd.read_csv(f'./historic_data/{period}/{symbol}.csv' , index_col=0, header=0, parse_dates=True)
    closing_prices = data['close']

    # get pertinent indicators incorporated into data
    strategies = []
    strategies.append(ParabolicSAR(data))
    # strategies.append(Stochastic_Rsi(data, upper_limit=70, lower_limit=30, stop_loss=0.01, stop_price=0.02))
    # strategy2 = Macd(data, stop_loss=0.01, stop_price=0.02)
    # strategy2 = Rsi(data, upper_limit=70, lower_limit=30, stop_loss=0.01, stop_price=0.02)

    lag = max([strategy.getLag() for strategy in strategies])

    for price in closing_prices:
        i = strategies[0].i
#        if strategy.i % 1440 == 0:
#            print(closing_prices.index[strategy.i])

        # skip the first days for the macd to become accurate
        if i < lag:
            list(map(lambda strategy: strategy.add_value(cash), strategies))
            list(map(lambda strategy: strategy.increment(), strategies))
            continue
        decisions = [strategy.decide(holding) for strategy in strategies]

        # change holdings and cash based on trading decision
        if all([decision == Action.BUY for decision in decisions]) and holding == (0, 0):
            shares_to_buy = cash // price
            cash -= shares_to_buy * price
            holding = (shares_to_buy, price)
        elif (decisions[0] == Action.SELL and holding != (0, 0)) or i == len(closing_prices)-1:
            if holding[1] < price:
                wins += 1
            else:
                losses += 1
            cash += holding[0] * price
            list(map(lambda strategy: strategy.add_value(cash), strategies))
            holding = (0, 0)

        list(map(lambda strategy: strategy.increment(), strategies))


    if len(sys.argv) > 3:
        if sys.argv[3] == '-v':
            strategies[0].plot()

    print(f'cash: {cash}\nwins: {wins}\nlosses: {losses}')
