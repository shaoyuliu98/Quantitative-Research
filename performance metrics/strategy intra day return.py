import numpy as np
import pandas as pd
import os

# Simple version: (Less interpretability but more efficient. We opt into the second approach just to be sure that the answer is correct.)
# signals.replace(0,np.nan,inplace=True)
# intraday = intraday.stack()
# strat_pnl = intraday.loc[(signals.index,slice(None))].unstack().multiply(signals,level=0,axis=1).stack().stack().reset_index()
# strat_pnl.columns = ['Day','Time','Symbol','Open_to_Date_Return']

class Strategy_PnL:
    def __init__(self,intraday_ret_path=None,signals_path=None):
        if (len(intraday_ret_path)==0) | (len(signals_path)==0):
            raise TypeError('Enter File Path.')
        self.intra_ret = pd.read_csv(intraday_ret_path,index_col=0,header=[0,1])
        self.signals = pd.read_csv(signals_path,index_col=0)

        self.intra_ret = self.intra_ret.stack()
        self.signals.replace(0,np.nan,inplace=True)

    def single_name_return(self,sig_col,ret_col):
        if sig_col.name!=ret_col.name:
            raise TypeError('Ticker Not in Agreement')
        ticker = sig_col.name
        temp_sig = sig_col.copy()
        temp_ret =  ret_col.reset_index(level=1)
        temp_ret.columns= ['Time','Cur_Day_Return']
        temp_combine = temp_ret.merge(temp_sig,how='left',left_index=True,right_index=True)
        temp_combine.rename({ticker:'Signal'},axis=1,inplace=True)
        temp_combine['Strat_Pnl'] = temp_combine['Cur_Day_Return']*temp_combine['Signal']
        return temp_combine

    def strategy_return(self):
        tot_strat_ret = pd.DataFrame()
        for i in self.intra_ret.columns:
            print(i)
            temp = self.single_name_return(self.signals[i], self.intra_ret[i])
            temp['Ticker'] = i
            tot_strat_ret = pd.concat([tot_strat_ret, temp])
        return tot_strat_ret

    def get_return(self):
        return self.strategy_return()


if __name__ == '__main__':
    intraday_return = './data/intraday return/SP 100 - Intraday Return.csv'
    signal = ['./signals/Open Gap Signals/SP 100/'+i for i in os.listdir('./signals/Open Gap Signals/SP 100') if i[-4:]=='.csv']

    for j in signal:
        print(j)
        cur_strategy = Strategy_PnL(intraday_return,j)
        cur_pnl = cur_strategy.get_return()
        file_name = './pnl/Open Gap Pnl/SP 100/'+j.replace('./signals/Open Gap Signals/SP 100/','')
        file_name = file_name.replace('signal','pnl')
        cur_pnl.to_csv(file_name)