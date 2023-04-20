import collections

import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# Things to consider:
# Signal generation variables: Rolling window size, Significance level, Gap definition, Long/Short type
# PnL related variables (regression): Holding Period, Volume, Volatility, Portfolio Construction
# Alternatively, can use Bayesian Optimization to find optimal exit time.
# Exit time: complex conditions: [pnl, time, sma cross over (short 30min,long 2hours)
# https://github.com/fmfn/BayesianOptimization

class Gap_Trading:
    def __init__(self,df_source,r_win=[100],s_lvl=[100]):
        self.data = pd.read_csv(df_source,skiprows=1)
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        self.data.sort_values('Date',inplace=True)
        self.data.fillna(method='ffill',inplace=True)

        self.dates = self.data['Date'].copy()

        self.consolidate_price = pd.DataFrame()
        for i in range((len(self.data.columns) - 1) // 6):
            cur_stock = self.data.iloc[:, i * 6 + 1:i * 6 + 7]
            modified_stock = self.stack_price(self.dates, cur_stock)
            self.consolidate_price = pd.concat([self.consolidate_price, modified_stock])

        self.gap_price = self.get_open_gap(self.get_daily_price(self.consolidate_price))

        self.rolling_window = r_win
        self.significant_lvl = s_lvl
        self.signals = collections.defaultdict()

        for i in self.rolling_window: # 50 days, 75 days, 100 days, 200 days
            for j in self.significant_lvl: # 80%, 85%, 90%, 95%, 100%
                gap_ranking = self.gap_price.pivot_table(index='Date', columns='Symbol', values='Open Gap').rolling(i).rank().stack()
                signal = gap_ranking.loc[gap_ranking >= i * j / 100].unstack()
                signal = (~signal.isna()).astype(float)
                self.signals[(i,j)] = signal

    def stack_price(self,date_series,stock_series):
        temp = pd.concat([date_series,stock_series],axis=1)
        temp.dropna(inplace=True)
        temp.columns = ['Date','Symbol','Open','High','Low','Close','Volume']
        # price has thousand comma delimiter
        temp['Open'] = temp['Open'].astype(str).str.replace(',','').astype(float)
        temp['High'] = temp['High'].astype(str).str.replace(',', '').astype(float)
        temp['Low'] = temp['Low'].astype(str).str.replace(',', '').astype(float)
        temp['Close'] = temp['Close'].astype(str).str.replace(',', '').astype(float)
        temp['Volume'] = temp['Volume'].astype(str).str.replace(',', '').astype(float)

        temp = temp[['Date','Symbol','Open','Close']]
        temp_stack = pd.melt(temp,id_vars=['Date','Symbol'])
        return temp_stack

    def get_daily_price(self,price_df):
        temp_open_price = price_df.loc[(price_df['variable']=='Open')&(price_df['Date'].dt.hour==9)&(price_df['Date'].dt.minute==30)].copy()
        temp_open = temp_open_price.drop('variable',axis=1)
        temp_open.columns = ['Date','Symbol','Open']
        temp_open['Date'] = temp_open['Date'].dt.date

        temp_close_price = price_df.loc[(price_df['variable']=='Close')&(price_df['Date'].dt.hour==15)&(price_df['Date'].dt.minute==45)].copy()
        temp_close = temp_close_price.drop('variable',axis=1)
        temp_close.columns = ['Date', 'Symbol', 'Close']
        temp_close['Date'] = temp_close['Date'].dt.date

        temp = temp_open.merge(temp_close,on=['Date','Symbol'])
        return temp

    def get_open_gap(self,price_df):
        temp = price_df.copy()
        temp['Prev Close'] = price_df.groupby('Symbol')['Close'].shift()
        temp.dropna(inplace=True)
        temp['Open Gap'] = temp['Open'] - temp['Prev Close']
        return temp

    def get_signals(self):
        return self.signals


if __name__ == '__main__':
    path = './data/SP 100 Intrady.csv'

    gap_trade = Gap_Trading(path,[50,75,100,200],[80,85,90,95,100])

    for key, value in gap_trade.get_signals().items():
        # print(key,value.sum().sum()/13) # avg trade per year
        value.to_csv('./signals/Open Gap Signals/SP 100/sp100_signal_'+str(key[0])+'rolling_'+str(key[1])+'lvl.csv')