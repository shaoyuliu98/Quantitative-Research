import numpy as np
import pandas as pd
from tabulate import tabulate

class Trading_Strategy:
    def __init__(self, input_df=None, freq='Daily'):
        # date, consolidated return of that date, sorted by date.
        # use log return
        # to do: Work on the difference between constant size betting vs. reinvesting.
        if len(input_df)>0:
            self.data = input_df
            self.ret = self.data['return']
            self.date = self.data['date']
            self.freq = freq
        else:
            print('Empty strategy created.')
        
        self.consolidated_metrics = self.get_metrics()

    def sharpe(self):
        std = self.ret.std()
        mean = self.ret.mean()
        if self.freq=='Daily':
            return mean/std*np.sqrt(252)
        if self.freq=='Monthly':
            return mean/std*np.sqrt(12)

    def sortino(self):
        std = self.ret.loc[self.ret<0].std()
        mean = self.ret.mean()
        if self.freq == 'Daily':
            return mean/std*np.sqrt(252)
        if self.freq == 'Monthly':
            return mean/std*np.sqrt(12)

    def vol(self):
        if self.freq == 'Daily':
            return self.ret.std()*np.sqrt(252)
        if self.freq == 'Monthly':
            return self.ret.std()*np.sqrt(12)

    def net_profit(self):
        return self.ret.sum()

    # def time_in_market(self):
    #     # to be improved. non trading days currently included
    #     if self.freq == 'Monthly':
    #         return np.nan
    #     st = self.date.min()
    #     et = self.date.max()
    #     return len(self.date)/((et-st).days+1)
    
    def win_ratio(self):
        return sum(self.ret>0)/len(self.ret)

    def avg_ret(self):
        return self.ret.mean()

    def avg_win(self):
        return self.ret.loc[self.ret>0].mean()

    def avg_loss(self):
        return self.ret.loc[self.ret<0].mean()

    def max_win(self):
        return self.ret.loc[self.ret>0].max()

    def max_loss(self):
        return self.ret.loc[self.ret<0].min()

    def mdd(self):
        cum_ret = self.ret.cumsum()+1
        return np.minimum((cum_ret - cum_ret.cummax())/cum_ret.cummax(),0).min()

    def calmar(self):
        if self.freq=='Daily':
            avg_ret = self.avg_ret()*np.sqrt(252)
        if self.freq == 'Monthly':
            avg_ret = self.avg_ret() * np.sqrt(12)
        return avg_ret/self.mdd()*-1

    def skewness(self):
        return self.ret.skew()

    def kurtosis(self):
        return self.ret.kurtosis()

    def get_metrics(self):
        metrics = np.array([self.sharpe(),
                   self.sortino(),
                   self.net_profit(),
                   self.avg_ret(),
                   self.avg_win(),
                   self.avg_loss(),
                   self.win_ratio(),
                   self.max_win(),
                   self.max_loss(),
                   # self.time_in_market(),
                   self.mdd(),
                   self.vol(),
                   self.calmar(),
                   self.skewness(),
                   self.kurtosis()])
        
        metrics = np.round(metrics,5).tolist()
        if self.freq == 'Daily':
            metrics = [self.date.min().date(),self.date.max().date()]+metrics
        if self.freq == 'Monthly':
            metrics = [self.date.min(), self.date.max()] + metrics

        metrics = pd.DataFrame(metrics,index=['From','To','Annualized Sharpe', 'Annualized Sortino',
                                              'Cumulative Return','Avg Return',
                                              'Avg Win','Avg Loss','Win Ratio',
                                              'Max Winner','Max Loser',
                                              # 'Time in Market',
                                              'Max Drawdown','Annualized Volatility','Annualized Calmar','Skew','Kurtosis'],
                               columns=['Value'])
        return metrics
    
    def print_metrics(self):
        print(tabulate(self.consolidated_metrics,headers='keys', tablefmt='grid'))

if __name__ == '__main__':
    pseudo_date = pd.Series(pd.date_range('2023-01-01','2023-01-31'))
    pseudo_ret = pd.Series(np.random.uniform(low=-0.05,high=0.1,size=len(pseudo_date)))

    pseudo = pd.concat([pseudo_date,pseudo_ret],axis=1)
    pseudo.columns = ['date','return']

    pseudo_strat = Trading_Strategy(pseudo)
    pseudo_strat.print_metrics()


