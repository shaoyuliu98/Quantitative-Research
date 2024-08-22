import pandas as pd
import yfinance as yf
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_yf_data(st,et,ticker,save_sector=True,price_type=['Open','High','Low','Close','Adj Close']):
    all_data = pd.DataFrame()
    sector_data = pd.DataFrame()
    if isinstance(ticker,list):
        ticker_list = ticker.copy()
    elif isinstance(ticker,pd.DataFrame):
        ticker_list = ticker.T.values[0]
    else:
        raise Exception('Invalid Ticker List type.')

    for i in ticker_list:
        print(i)
        temp = pd.DataFrame(yf.download(i, start=st, end=et)[price_type].stack()).reset_index()
        temp.columns = ['Date', 'Type', 'Price']
        temp['Ticker'] = i
        all_data = pd.concat([all_data, temp])

        if save_sector:
            if len(temp)!=0:
                if i == 'CAT':
                    i_sector = 'Industrials'
                else:
                    temp_yf_ticker = yf.Ticker(i)
                    if 'sector' not in temp_yf_ticker.info:
                        print(i,'Sector not found. Use "Others" instead.')
                        i_sector = 'Others'
                    else:
                        i_sector = temp_yf_ticker.info['sector']
                sector_data = pd.concat([sector_data,pd.Series([i,i_sector])],axis=1)

    if save_sector:
        sector_data = sector_data.T
        sector_data.columns=['Ticker','Sector']

        all_data = all_data.merge(sector_data,how='left',on='Ticker')

    return all_data

if __name__ == '__main__':
    tz = pytz.timezone('America/New_York')
    # SP 100
    # start_dt = tz.localize(datetime(2009,12,31))
    # end_dt = tz.localize(datetime(2023,1,1))
    #
    # tickers = pd.read_csv('./data/SP 100 tickers.csv')
    #
    # price_data,sector_data = get_yf_data(start_dt,end_dt,tickers)
    #
    # price_data.to_csv('./data/SP 100 Daily Data.csv',index=False)
    # sector_data.to_csv('./data/SP 100 Sector Data.csv', index=False)

    # Barchart Chart of the Day
    data_info = pd.read_csv('./data/Chart of the Day Info.csv')
    data_info['Signal Date'] = pd.to_datetime(data_info['Signal Date'])
    data_info['Published Date'] = pd.to_datetime(data_info['Published Date'])

    start_dt = tz.localize(data_info['Signal Date'].min()+relativedelta(months=-6))
    end_dt = tz.localize(data_info['Published Date'].max())

    tickers = data_info[['Ticker']].copy()

    price_data = get_yf_data(start_dt, end_dt, tickers)

    price_data.to_csv('./data/Chart of the Day Daily Data.csv',index=False)
