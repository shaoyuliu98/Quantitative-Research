import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

class Intraday:
    def __init__(self,df_source):
        self.data = pd.read_csv(df_source,skiprows=1)
        self.dates = pd.to_datetime(self.data.iloc[:,0])

        self.consolidate_price = pd.DataFrame()
        for i in range((len(self.data.columns) - 1) // 6):
            cur_stock = self.data.iloc[:, i * 6 + 1:i * 6 + 7]
            modified_stock = self.stack_price(self.dates, cur_stock)
            self.consolidate_price = pd.concat([self.consolidate_price, modified_stock])

        self.consolidate_price.sort_values(['Symbol', 'Date'], inplace=True)
        self.intraday_ret = self.consolidate_price.pivot_table(index=['Day'], columns=['Symbol', 'Time'],values='Open_to_Date_Return')
        self.intraday_ret = self.intraday_ret.rename_axis([None,None],axis=1).reset_index()

    def stack_price(self, date_series, stock_series):
        temp = pd.concat([date_series, stock_series], axis=1)
        temp.dropna(inplace=True)
        temp.columns = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']
        # price has thousand comma delimiter
        temp['Open'] = temp['Open'].astype(str).str.replace(',', '').astype(float)
        temp['High'] = temp['High'].astype(str).str.replace(',', '').astype(float)
        temp['Low'] = temp['Low'].astype(str).str.replace(',', '').astype(float)
        temp['Close'] = temp['Close'].astype(str).str.replace(',', '').astype(float)
        temp['Volume'] = temp['Volume'].astype(str).str.replace(',', '').astype(float)

        temp_close = temp[['Date', 'Symbol', 'Close']]
        temp_close['Day'] = temp_close['Date'].dt.date.astype(str)

        temp_hour = temp_close['Date'].dt.hour.astype(str)
        temp_minute = temp_close['Date'].dt.minute.astype(str)

        temp_close['Time'] = np.where(temp_hour.apply(lambda x: len(x)) == 1, '0' + temp_hour, temp_hour) + ':' + \
                             np.where(temp_minute.apply(lambda x: len(x)) == 1,'0' + temp_minute, temp_minute)

        temp_cur_day_open = temp.loc[(temp['Date'].dt.hour == 9) & (temp['Date'].dt.minute == 30), ['Date', 'Symbol', 'Open']]
        temp_cur_day_open['Day'] = temp_cur_day_open['Date'].dt.date.astype(str)

        temp_stack = temp_close.merge(temp_cur_day_open, how='left', on=['Symbol', 'Day'])
        temp_stack = temp_stack[['Date_x', 'Day', 'Time', 'Symbol', 'Close', 'Open']]
        temp_stack.columns = ['Date', 'Day', 'Time', 'Symbol', 'Close', 'Current_Day_Open']
        temp_stack['Open_to_Date_Return'] = temp_stack['Close'] / temp_stack['Current_Day_Open'] - 1
        return temp_stack

    def get_return(self):
        return self.intraday_ret


if __name__ == '__main__':
    path = './data/SP 100 Intrady.csv'

    intraday_return = Intraday(path)
    intraday_return.get_return().to_csv('./data/intraday return/SP 100 - Intraday Return.csv',index=False)




