import pandas as pd
from datetime import timedelta
from sklearn.decomposition import PCA

class Eigen_Portfolio:
    def __init__(self,path,st_date,end_date,lookback_mo):
        self.data = pd.read_csv(path)
        self.st_date = st_date
        self.end_date = end_date
        self.lookback_mo = lookback_mo

        self.data = self.stock_selection(self.data,self.st_date)
        self.ret_df_daily = self.get_daily_return(self.data)
        self.ret_df_monthly = self.ret_df_daily.groupby('Month').sum()

        self.rolling_dict = pd.date_range(pd.to_datetime(st_date)+timedelta(1),end_date,freq='M').strftime('%Y-%m')

        self.strat_return, self.strat_weight = self.pca_strat(self.lookback_mo,self.rolling_dict,
                                                              self.ret_df_daily,self.ret_df_monthly)
        self.benchmark_return = self.get_benchmark_ret(self.ret_df_monthly)

        self.consolidated_return = pd.concat([self.strat_return,self.benchmark_return],axis=1)
    def stock_selection(self,price_df,st_date):
        # excluding a few stocks for lack of data. This makes sure that our backtesting universe starts on 2009-12-31(st_date) and ends on 2022-12-30(end_date).
        selection = price_df.loc[price_df['Type']=='Adj Close'].groupby('Ticker')['Date'].first()==st_date
        selection = selection.loc[selection==True].index

        price_df_ret = price_df.loc[(price_df['Type']=='Adj Close')&(price_df['Ticker'].isin(selection))].pivot_table(
            index='Date',columns='Ticker',values='Price')

        if price_df_ret.isna().sum().sum() > 0:
            raise Exception("There is missing price information in the dataset.")
        return price_df_ret
    def get_daily_return(self,price_df):
        ret_df = (price_df / price_df.shift() - 1).dropna()
        ret_df.reset_index(inplace=True)
        ret_df['Month'] = pd.to_datetime(ret_df['Date']).dt.to_period('M').astype(str)
        ret_df.drop('Date',axis=1,inplace=True)
        ret_df.set_index('Month',inplace=True)
        return ret_df
    def pca_strat(self,n_lookback,rolling,ret_daily,ret_monthly):
        strat_ret_all = pd.DataFrame()
        strat_weight_all = pd.DataFrame()

        for i in range(n_lookback,len(rolling)):
            print('Training:',rolling[i-1])
            # Data
            training_period = rolling[i-n_lookback:i]
            training_set = ret_daily.loc[ret_daily.index.isin(training_period)]
            # Normalize Return
            ret_normalized = (training_set - training_set.mean()) / training_set.std()
            rho_ = ret_normalized.corr()
            # PCA
            cur_pca = PCA(n_components=len(rho_))
            cur_pca.fit(rho_)
            # Weight Calculation
            cur_loadings = pd.DataFrame(cur_pca.components_.T, columns=['PC' + str(i) for i in range(1, len(rho_) + 1)],index=rho_.index)
            cur_eigen_weight = cur_loadings[['PC1', 'PC2', 'PC3']]
            cur_eigen_weight = cur_eigen_weight.div(training_set.std(), axis=0)
            cur_weights = cur_eigen_weight.apply(lambda x: x / x.sum())
            # Holding Return
            holding_period = rolling[i]
            holding_period_ret = ret_monthly.loc[holding_period]
            # Weight Record
            cur_weights_record = cur_weights.stack().reset_index()
            cur_weights_record.columns = ['Ticker', 'PC', 'Weight']
            cur_weights_record['Month'] = holding_period
            strat_weight_all = pd.concat([strat_weight_all, cur_weights_record])
            # Strategy Return Calculation
            cur_strat_ret = pd.concat([cur_weights,holding_period_ret],axis=1)
            cur_strat_ret['PC1 Ret'] = cur_strat_ret['PC1']*cur_strat_ret[holding_period]
            cur_strat_ret['PC2 Ret'] = cur_strat_ret['PC2']*cur_strat_ret[holding_period]
            cur_strat_ret['PC3 Ret'] = cur_strat_ret['PC3']*cur_strat_ret[holding_period]
            cur_strat_ret = cur_strat_ret[['PC1 Ret', 'PC2 Ret', 'PC3 Ret']].sum()
            cur_strat_ret = pd.DataFrame(cur_strat_ret,columns=[holding_period]).T
            # Strategy Return Record
            strat_ret_all = pd.concat([strat_ret_all,cur_strat_ret])
        return strat_ret_all, strat_weight_all
    def get_benchmark_ret(self,ret_monthly):
        benchmark = pd.DataFrame(ret_monthly.mean(axis=1),columns=['Equal Weight'])
        return benchmark
    def get_return(self):
        return self.consolidated_return
    def get_weight(self):
        return self.strat_weight

if __name__ == '__main__':
    price_path = './data/SP 100 Daily Data.csv'
    st_date = '2009-12-31'
    end_date = '2022-12-31'
    lookback_month = 12

    eigen_portfolio3 = Eigen_Portfolio(price_path,st_date,end_date,lookback_month)
    eigen_portfolio3_return = eigen_portfolio3.get_return()
    eigen_portfolio3_weight = eigen_portfolio3.get_weight()

    eigen_portfolio3_return.to_csv('./pnl/Eigen Portfolio Pnl/SP 100/Backtesting Return_'+str(lookback_month)+'mo_rolling.csv')
    eigen_portfolio3_weight.to_csv('./pnl/Eigen Portfolio Pnl/SP 100/Backtesting Weight_'+str(lookback_month)+'mo_rolling.csv')


