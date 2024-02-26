import os
import sys
import alpaca_trade_api as tradeapi
import datetime
import time
import pytz


if __name__ == '__main__':
    symbol = ''
    period = 'day'
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        print('please input a symbol, eg. AAPL')
        sys.exit()
    if len(sys.argv) > 2:
        period = sys.argv[2]

    alpaca_client = os.environ['ALPACA_CLIENT']
    alpaca_secret = os.environ['ALPACA_SECRET']

    api = tradeapi.REST(alpaca_client, alpaca_secret,'https://api.alpaca.markets')
    if period == 'day':
        data = api.polygon.historic_agg_v2(symbol, 1, period, _from='2019-01-01', to=datetime.datetime.today().strftime('%Y-%m-%d %H:%M')).df
    else:
        start_date = datetime.datetime(2020, 1, 1, 0, 0)
        end_date = start_date + datetime.timedelta(days=1)
        data = api.polygon.historic_agg_v2(symbol, 1, period, _from=start_date.strftime('%Y-%m-%d %H:%M'), to=end_date.strftime('%Y-%m-%d %H:%M')).df

        while end_date < datetime.datetime(2020, 5, 1, 0, 0):
            try:
                start_date = end_date + datetime.timedelta(days=1)
                end_date = start_date + datetime.timedelta(days=1)
    
                new_data = api.polygon.historic_agg_v2(symbol, 1, period, _from=start_date.strftime('%Y-%m-%d %H:%M'), to=end_date.strftime('%Y-%m-%d %H:%M')).df
                data = data.append(new_data)
            except:
                break


    if len(sys.argv) > 3 and sys.argv[3] == 'long':
        time.sleep(30)
        request_count = 0
        start_date = data.index[-1] + datetime.timedelta(minutes=1)
        end_date = start_date + datetime.timedelta(days=1)
        while end_date < datetime.datetime.today().astimezone(pytz.timezone('America/New_York')):
            try:
                if request_count == 198:
                    time.sleep(60)
                    request_count = 0
                new_data = api.polygon.historic_agg_v2(symbol, 1, period, _from=start_date.strftime('%Y-%m-%d %H:%M'), to=end_date.strftime('%Y-%m-%d %H:%M')).df
                data = data.append(new_data)
                start_date = end_date + datetime.timedelta(days=1)
                end_date = start_date + datetime.timedelta(days=1)
                request_count += 1 
            except:
                break
        data.to_csv(f'../historic_data/{period}/long/{symbol}.csv')
    else:
        data.to_csv(f'../historic_data/{period}/{symbol}.csv')
