import sys

sys.path.append('../')

import numpy as np
import pandas as pd
from datetime import datetime
from performance_metrics.performance import Trading_Strategy
from performance_metrics import price_to_info as pti
import pytz
import matplotlib
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

matplotlib.use("Qt5Agg")


### Next Steps:
# 1. Use IV as vol weighting scheme instead of realized vol (need paid data)
# 2. If works well, explore more frequent rebalance, and consider paid subscriptions

class Momentum:
    def __init__(self, trading_universe, start_time, end_time, path,
                 momentum_dict=None, long_only_dict=None, force_run=False):
        self.tickers = trading_universe
        self.signals = None
        self.position_no_shift = None

        self.pivot_price_data = pti.init_data(path, start_time, end_time, self.tickers, force_run=force_run)

        self.daily_log_return = pti.get_log_return(self.pivot_price_data)
        self.monthly_log_return = pti.get_log_return(self.pivot_price_data, rtype='m')
        self.monthly_log_return_std = pti.rolling_std(self.daily_log_return, rtype='m')

        self.signal_generation(momentum_dict, long_only_dict)
        self.vol_adj()

    def signal_generation_helper(self, ticker, momentum, longonly):
        rolling_ret = {'rolling' + str(i): self.monthly_log_return[ticker].rolling(i).sum().dropna() for i in momentum}
        index_adj = rolling_ret['rolling' + str(momentum[-1])].index
        rolling_ret_adj = dict(zip(rolling_ret.keys(),
                                   list(map(lambda x: x.loc[index_adj], rolling_ret.values()))))
        avg_rolling_ret = pd.DataFrame(pd.concat(rolling_ret_adj.values()).groupby(level=0).mean())

        if longonly:
            avg_rolling_ret['signal'] = np.where(avg_rolling_ret[ticker] >= 0, 1, 0)
        else:
            avg_rolling_ret['signal'] = np.where(avg_rolling_ret[ticker] >= 0, 1, -1)

        return avg_rolling_ret[['signal']].rename({'signal': ticker}, axis=1)

    def signal_generation(self, momentum_dict, long_only_dict):
        momentum = {}
        if (momentum_dict is None):
            momentum = {i: [3, 6, 9, 12] for i in self.tickers}
        else:
            for i, j in momentum_dict.items():
                for k in i:
                    momentum[k] = j
                    
            for i in self.tickers:
                if i not in momentum:
                    momentum[i] = [3, 6, 9, 12]

        long_only = {}
        if (long_only_dict is None):
            long_only = {i: False for i in self.tickers}
        else:
            for i, j in long_only_dict.items():
                for k in i:
                    long_only[k] = j
                    
            for i in self.tickers:
                if i not in long_only:
                    long_only[i] = False

        all_signal = pd.DataFrame()
        for i in momentum:
            all_signal = pd.concat([all_signal, self.signal_generation_helper(i, momentum[i], long_only[i])], axis=1)

        self.signals = all_signal.copy().dropna()
        for i in self.signals.columns:
            self.signals[i] = self.signals[i].astype(int)

        return

    def vol_adj(self):
        self.monthly_log_return = self.monthly_log_return.loc[self.signals.index].copy()
        self.monthly_log_return_std = self.monthly_log_return_std.loc[self.signals.index].copy()

        return

    def get_performance(self, allocation):
        sub_signals = self.signals[allocation.columns]
        position = allocation * sub_signals

        if len(allocation.columns) == len(self.tickers):
            self.position_no_shift = position

        ret = (position.shift() * self.monthly_log_return[position.columns]).dropna().sum(axis=1)
        ret = ret.reset_index()
        ret.columns = ['date', 'return']

        return ret

    def get_vol(self):
        return self.monthly_log_return_std


if __name__ == '__main__':
    etf_list = [
        'SPY', 'IWM', 'EFA', 'EEM', 'QQQ',
        'XLE', 'XLK', 'XLY', 'IYR', 'SMH',
        'LQD', 'IEF', 'TIP', 'TLT', 'AGG',
        'UUP', 'FXE', 'FXF',
        'GLD', 'USO', 'DBC', 'SLV', 'UNG', 'CORN',
    ]

    stock_etf = ['SPY', 'IWM', 'EFA', 'EEM', 'QQQ']  # s&p, russell2000, eu/japan/aus, emerging market, nasdaq
    sector_etf = ['XLE', 'XLK', 'XLY', 'IYR', 'SMH']  # energy, tech, consumer discretionary, real estate, semi
    bond_etf = ['LQD', 'IEF', 'TIP', 'TLT','AGG'] # IG corp, 7-10yr treasury, inflation bond, 20+yr treasury, IG corp market
    fx_etf = ['UUP', 'FXE', 'FXF'] # US $ bull, Euro, Swiss Franc
    commod_etf = ['GLD', 'USO', 'DBC', 'SLV', 'UNG', 'CORN']  # gold, oil, commod index, silver, natural gas, corn

    # etf_list = list(set(etf_list)-set(fx_etf))

    tz = pytz.timezone('America/New_York')
    st = tz.localize(datetime(2006, 1, 1))
    et = tz.localize(datetime(2024, 9, 1))

    filename = '../yfinance_data/cta_momentum_data.csv'

    momentum_window = {tuple(stock_etf): [3, 6, 9, 12],
                       tuple(sector_etf): [3, 6, 9, 12],
                       # tuple(bond_etf): [3, 6, 9, 12],
                       # tuple(fx_etf): [3, 6, 9, 12],
                       tuple(commod_etf): [3, 6, 9, 12]}

    long_only_table = {tuple(stock_etf): True,
                       tuple(sector_etf): True,
                       # tuple(bond_etf): True,
                       # tuple(fx_etf): True,
                       tuple(commod_etf): True}

    strategy_cutoff = '2022-01'

    momentum_strat = Momentum(etf_list, st, et, filename, momentum_window, long_only_table, force_run=True)

    all_return = pd.DataFrame()
    all_return_perf = pd.DataFrame()
    for i in [etf_list,
              stock_etf,
              sector_etf,
              # bond_etf,
              # fx_etf,
              commod_etf]:
        temp_return = momentum_strat.get_performance(pti.get_alloc_weight(momentum_strat.get_vol(), i))
        all_return = pd.concat([all_return, temp_return.set_index('date')], axis=1)

        temp_perf = Trading_Strategy(temp_return.loc[temp_return['date'] >= strategy_cutoff],
                                     'Monthly').get_metrics_table()
        all_return_perf = pd.concat([all_return_perf, temp_perf], axis=1)

    all_return.columns = ['overall',
                          'stocks',
                          'sector',
                          # 'bond',
                          # 'fx',
                          'commodity',
                          ]

    all_return_perf.columns = ['overall',
                               'stocks',
                               'sector',
                               # 'bond',
                               # 'fx',
                               'commodity'
                               ]

    print(all_return_perf)
    print('\n')
    # print(all_return[strategy_cutoff:].corr())
    # print('\n')
    # print(momentum_strat.position_no_shift.iloc[-1])

    # print(all_return.rolling(12).corr().iloc[-4:,:])
    np.exp(all_return[strategy_cutoff:].cumsum()).plot()
    plt.show()
