import pandas as pd
import yfinance as yf
import pytz
from datetime import datetime

def get_yf_data(st,et,ticker):
    all_data = pd.DataFrame()
    sector_data = pd.DataFrame()
    ticker_list = ticker.T.values[0]

    for i in ticker_list:
        print(i)
        temp = pd.DataFrame(yf.download(i, start=st, end=et)[['Open','High','Low','Close','Adj Close']].stack()).reset_index()
        temp.columns = ['Date', 'Type', 'Price']
        temp['Ticker'] = i
        all_data = pd.concat([all_data, temp])

        if len(temp)!=0:
            if i == 'CAT':
                i_sector = 'Industrials'
            else:
                temp_yf_ticker = yf.Ticker(i)
                i_sector = temp_yf_ticker.info['sector']
            sector_data = pd.concat([sector_data,pd.Series([i,i_sector])],axis=1)

    sector_data = sector_data.T
    sector_data.columns=['Ticker','Sector']

    return all_data,sector_data

if __name__ == '__main__':
    tz = pytz.timezone('America/New_York')

    start_dt = tz.localize(datetime(2010,1,1))
    end_dt = tz.localize(datetime(2023,1,1))

    tickers = pd.read_csv('./data/SP 100 tickers.csv')

    price_data,sector_data = get_yf_data(start_dt,end_dt,tickers)

    price_data.to_csv('./data/SP 100 Daily Data.csv',index=False)
    sector_data.to_csv('./data/SP 100 Sector Data.csv', index=False)