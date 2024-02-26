"""
strategies for the backtest program to utilize.
"""

from actions import Action
from scipy import stats
import pandas as pd
import datetime
import talib
import matplotlib.pyplot as plt


class Strategy():
    def __init__(self, lag, data):
        self.lag = lag
        self.traded = False
        self.i = 0
        self.data = data
        self.value_history = [[], []]

    def getLag(self):
        return self.lag

    def increment(self):
        self.i += 1

    def plot(self):
        self.data['close'].plot()
        normalize = self.data['close'][0] / self.value_history[1][0]
        plt.plot(self.value_history[0], [x*normalize for x in self.value_history[1]])
        plt.show()

    def add_value(self, value):
        self.value_history[1].append(value)
        self.value_history[0].append(self.data.index[self.i])


class Macd(Strategy):
    def __init__(self, data, stop_price=0.015, stop_loss=0.01):
        super().__init__(26, data)
        self.upper = stop_price
        self.lower = stop_loss
        self.macd()
        self.data['date_ordinal'] = pd.to_datetime(self.data.index.map(datetime.datetime.toordinal))

    def decide(self, holding):
        price = self.data['close'][self.i]
        boughtPrice = holding[1]

        # slope_of_signal, intercept, r_value, p_value, std_err = stats.linregress([i for i in range(3)], self.data['signal'][self.i-3:self.i])
        # slope_of_macd, intercept, r_value, p_value, std_err = stats.linregress([i for i in range(3)], self.data['macd'][self.i-3:self.i])
        # make a new sell logic that looks at when the macd is is evening out.
        # if (holding != (0,0) and self.data['signal'][self.i] > 0 and  price > boughtPrice * (1+self.upper)) or price < boughtPrice * (1-self.lower):
        #     self.traded = False
        #     return Action.SELL
        if holding != (0,0) and (price > boughtPrice * (1+self.upper) or price < boughtPrice * (1-self.lower)):
            self.traded = False
            return Action.SELL
        elif self.data['signal'][self.i] > self.data['macd'][self.i] and self.data['signal'][self.i] > 0 and not self.traded:
            self.traded = True
            return Action.BUY
        else:
            return Action.NOTHING

    def macd(self):
        """The MACD is calculated by subtracting the 26-period Exponential Moving Average (EMA) from the 12-period EMA.
        The result of that calculation is the MACD line. A nine-day EMA of the MACD called the "signal line," is then
        plotted on top of the MACD line, which can function as a trigger for buy and sell signals."""
        self.data['ewm_26'] = self.data['close'].ewm(span=26,min_periods=0,adjust=False,ignore_na=False).mean()
        self.data['ewm_12'] = self.data['close'].ewm(span=12,min_periods=0,adjust=False,ignore_na=False).mean()
        self.data['macd'] = self.data['ewm_12'] - self.data['ewm_26']
        self.data['signal'] = self.data['macd'].ewm(span=9,min_periods=0,adjust=False,ignore_na=False).mean()


class Rsi(Strategy):
    def __init__(self, data, upper_limit=70, lower_limit=30, stop_price=0.015, stop_loss=0.01):
        super().__init__(14, data)
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.stop_price = stop_price
        self.stop_loss = stop_loss
        self.rsi()

    def decide(self, holding):
        price = self.data['close'][self.i]
        boughtPrice = holding[1]
        if self.data['rsi'][self.i] > self.lower_limit:
            self.traded = False
        if holding != (0, 0) and (price > boughtPrice * (1+self.stop_price) or price < boughtPrice * (1-self.stop_loss)):
            return Action.SELL
        elif self.data['rsi'][self.i] < self.lower_limit and not self.traded:
            self.traded = True
            return Action.BUY
        else:
            return Action.NOTHING

    def rsi(self):
        """The relative strength index (RSI) is a momentum indicator used in technical analysis
        that measures the magnitude of recent price changes to evaluate overbought or oversold
        conditions in the price of a stock or other asset."""
        delta = self.data['close'] - self.data['open']
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0

        # Calculate the EWMA
        roll_up = up.ewm(span=self.lag).mean()
        roll_down = down.abs().ewm(span=self.lag).mean()
        self.data['rsi'] = 100 - (100/(1+(roll_up/roll_down)))

class Stochastic_Rsi(Rsi):
    """Using RSI values within the Stochastic formula gives traders an idea of whether the current
    RSI value is overbought or oversold."""
    def __init__(self, data, upper_limit=70, lower_limit=30, stop_price=0.015, stop_loss=0.01):
        super().__init__(data, upper_limit, lower_limit, stop_price, stop_loss)
        self.stoch_rsi()

    def decide(self, holding):
        price = self.data['close'][self.i]
        boughtPrice = holding[1]


        if self.data['stoch_rsi'][self.i] > self.lower_limit:
            pass
            # self.traded = False
        if holding != (0, 0) and (price > boughtPrice * (1+self.stop_price) or price < boughtPrice * (1-self.stop_loss)):
            return Action.SELL
        elif self.data['stoch_rsi'][self.i] < self.lower_limit:#  and not self.traded:
            # self.traded = True
            return Action.BUY
        else:
            return Action.NOTHING

    def stoch_rsi(self):
        max = self.data['rsi'].rolling(self.lag).max()
        min = self.data['rsi'].rolling(self.lag).min()
        self.data['stoch_rsi'] = (self.data['rsi'] - min)*100/(max-min)


class ParabolicSAR(Strategy):
    """"""
    def __init__(self, data):
        super().__init__(0, data)
        self.sar()

    def decide(self, holding):
        if holding != (0, 0) and self.data['SAR'][self.i] > self.data['close'][self.i]:
            return Action.SELL
        elif self.data['SAR'][self.i] < self.data['close'][self.i]:
            return Action.BUY
        else:
            return Action.NOTHING

    def sar(self):
        self.data['SAR'] = talib.SAR(self.data['high'], self.data['low'], acceleration=0.02, maximum=0.2)
