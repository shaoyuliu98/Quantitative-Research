import pandas as pd
import numpy as np
import os
from yfinance_data import get_yf_data

def init_data(fpath,st,et,tickers,sector=False,ptype=['Adj Close'],force_run=False):
    if (not os.path.isfile(fpath)) or force_run:
        temp = get_yf_data(st, et, tickers, save_sector=sector, price_type=ptype)
        temp.to_csv(fpath, index=False)
        print('Data Download Complete.')
    price_data = pd.read_csv(fpath)

    return price_data.pivot_table(index='Date', columns='Ticker', values='Price').dropna()

def get_log_return(daily_price, rtype=None):
    if not rtype:
        rtype = 'd'
    if rtype not in ['d','m']:
        raise Exception('rtype must be in ["d","m"].')

    daily_log_return = np.log(daily_price / daily_price.shift()).dropna()

    if rtype == 'd':
        return daily_log_return

    monthly_price = daily_price.reset_index(names='Date')
    monthly_price['Month'] = pd.to_datetime(monthly_price['Date']).dt.to_period('M').astype(str)
    monthly_price = monthly_price.groupby('Month')[[i for i in monthly_price.columns if i not in ['Date', 'Month']]].last()
    monthly_log_return = np.log(monthly_price / monthly_price.shift()).dropna()

    return monthly_log_return

def rolling_std(daily_log_return, n=20, rtype=None):
    if not rtype:
        rtype = 'd'
    if rtype not in ['d','m']:
        raise Exception('rtype must be in ["d","m"].')

    if rtype == 'd':
        return daily_log_return.rolling(n).std()

    monthly_log_return = daily_log_return.reset_index(names='Date')
    monthly_log_return['Month'] = pd.to_datetime(monthly_log_return['Date']).dt.to_period('M').astype(str)

    return monthly_log_return.groupby('Month')[[i for i in monthly_log_return.columns if i not in ['Date', 'Month']]].std()

def get_alloc_weight(vol_df,sub_universe):
    sub_vols = vol_df[sub_universe]
    inv_vol = 1 / sub_vols

    return inv_vol.div(inv_vol.sum(axis=1).values, axis=0)


