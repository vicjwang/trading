import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime, timedelta



DATE_FMT = '%Y-%m-%d'


class TradeBot:

    def __init__(self):
        self.df = pd.DataFrame()
        self.baseline_df = None
        self.baseline_stats_df = pd.DataFrame()
        self.simulation_df = None
        self.delta_threshold = .05
        self.fund_size = None
        self.holdings = None
        self.baseline_ratio = None
        self.current_date = None
        self.simulation_iter = None

    def add_security(self, prices):
        self.df = pd.concat([self.df, prices], axis=1)

    def calculate_baseline(self, years):
        start_date = datetime.strptime(self.df.index[0], DATE_FMT).date()

        self.baseline_end_date = (start_date + timedelta(days=years*365)).strftime(DATE_FMT)
        self.baseline_df = self.df[self.df.index < self.baseline_end_date]

        self.simulation_df = self.df[self.df.index >= self.baseline_end_date]
        self.simulation_iter = self.simulation_df.iterrows()
        self.current_date, _ = self.simulation_iter.next()
        means_df = pd.DataFrame([[np.mean(self.baseline_df[col]) for col in self.baseline_df.columns]], columns=self.df.columns, index=['mean'])
        self.baseline_stats_df = self.baseline_stats_df.append(means_df)
        self.baseline_ratio = means_df.loc['mean'][self.df.columns[0]]/sum(means_df.loc['mean'])

    def allocate_funds(self, fund_size):
        self.fund_size = fund_size
        even = int(fund_size/len(self.df.columns))

        self.holdings = {col:int(even/self.baseline_df.iloc[-1][col]) for col in self.df.columns}
        # Store key => {value, shares}

    def sell(self, security, shares, date):
        price = self.get_price(security, date)
        self.holdings[security] -= shares
        return price*shares

    def buy(self, security, shares, date):
        price = self.get_price(security, date)
        self.holdings[security] += shares
        return price*shares

    def get_price(self, security, date):
        return self.df.loc[date][security]

    def simulate(self, days):

        # Baseline ratio
        # If gold ratio increases by 10%, sell 10% gold and buy silver
        # If gold ratio decreases by 10%, buy 10% gold and sell silver
        for i in range(days):
            self.current_date, row = self.simulation_iter.next()
            date = self.current_date
            gold_ratio = row['gold']/sum(row)
            if gold_ratio > self.baseline_ratio + self.delta_threshold:
                gold_shares = int(self.holdings['gold']*self.delta_threshold)
                revenue = self.sell('gold', gold_shares, date)
                silver_shares = revenue/self.get_price('silver', date)
                self.buy('silver', silver_shares, date)

            elif gold_ratio < self.baseline_ratio - self.delta_threshold:
                silver_shares = int(self.holdings['silver']*self.delta_threshold)
                revenue = self.sell('silver', silver_shares, date)
                gold_shares = revenue/self.get_price('gold', date)
                self.buy('gold', gold_shares, date)

    def calculate_portfolio(self, date=None):
        if date is None:
            date = self.current_date
        # Return tuple (profit, ror)
        return sum([shares*self.df.loc[date][security] for security, shares in self.holdings.items()])


GOLD_PRICES_FILEPATH = '../data/gld_2009-2019.csv'
SILVER_PRICES_FILEPATH = '../data/slv_2009-2019.csv'


def main():
    # Read data files into dataframes.
    gold_prices = pd.read_csv(GOLD_PRICES_FILEPATH, index_col=0, names=['date', 'gold'], header=0)
    silver_prices = pd.read_csv(SILVER_PRICES_FILEPATH, index_col=0, names=['date', 'silver'], header=0)

    # Add dataframe to tradebot.
    tradebot = TradeBot()
    tradebot.add_security(gold_prices)
    tradebot.add_security(silver_prices)

    # Use first X years as baseline.
    # Use remaining years as simulation.
    BASELINE_YEARS = 2
    tradebot.calculate_baseline(BASELINE_YEARS)

    # Allocate initial fund size between the securities evenly.
    INITIAL_FUND = 10000
    tradebot.allocate_funds(INITIAL_FUND)
    print tradebot.calculate_portfolio()

    # Everyday, decide to buy or sell each security.
    SIM_DAYS = 1000
    for i in range(SIM_DAYS):
        tradebot.simulate(1)

    # At end, calculate profit and rate of return.
    print tradebot.calculate_portfolio()
    plt.plot([float(row['gold']/(sum(row))) for date, row in tradebot.df.iterrows()])
    plt.show()


if __name__ == '__main__':
    main()
