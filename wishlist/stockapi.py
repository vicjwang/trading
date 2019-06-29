import requests
import os
from utils import skip, pickle_cache


class StockApi:

    ANNUAL_INTERVAL = 'annual'
    JSON_DATATYPE = 'datatype=json'

    def _append_query(self, url, **query):
        return ''.join([
          url,
          '?',
          self._build_query(**query)
        ])
    
    def _build_url(self, *args):
        raise NotImplementedError()

    def fetch_income_statement(self, ticker, **query):
        url = self._append_query(self._build_url(self.INCOME_ENDPOINT, ticker), **query)
        resp = requests.get(url)
        return resp.json()

    def fetch_balance_sheet_statement(self, ticker, **query):
        url = self._append_query(self._build_url(self.BALANCE_SHEET_ENDPOINT, ticker), **query)
        resp = requests.get(url)
        return resp.json()

    def fetch_cash_flow_statement(self, ticker, **query):
        url = self._append_query(self._build_url(self.CASH_FLOW_ENDPOINT, ticker), **query)
        resp = requests.get(url)
        return resp.json()

    def _build_query(self, **params):
        return '&'.join(['='.join(item) for item in list(params.items())]) 
        

class FinancialPrepApi(StockApi):
    API_DOMAIN = 'https://financialmodelingprep.com'
    API_NAMESPACE = 'api'
    API_VERSION = 'v3'
    PROFILE_ENDPOINT = 'company/profile'
    FINANCIALS_ENDPOINT = 'company-key-metrics'
    GROWTH_ENDPOINT = 'financial-statement-growth'
    RATIOS_ENDPOINT = 'financial-ratios'
    DCF_ENDPOINT = 'discounted-cash-flow'
    INCOME_ENDPOINT = 'financials/income-statement'
    BALANCE_SHEET_ENDPOINT = 'financials/balance-sheet-statement'
    CASH_FLOW_ENDPOINT = 'financials/cash-flow-statement'
    DATE_KEY = 'date'
    REVENUE_KEY = 'Revenue'
    NET_INCOME_KEY = 'Net Income'
    FCF_KEY = 'Free Cash Flow'
    EQUITY_KEY = 'Total shareholders equity'
    DEBT_KEY = 'Total debt'
 
    def _build_url(self, endpoint, ticker):
        return os.path.join(
          self.API_DOMAIN, self.API_NAMESPACE, self.API_VERSION, endpoint, ticker
        )

    def fetch_income_statement(self, ticker, interval=StockApi.ANNUAL_INTERVAL):
        return super(FinancialPrepApi, self).fetch_income_statement(ticker)['financials']

    def fetch_balance_sheet_statement(self, ticker, interval=StockApi.ANNUAL_INTERVAL):
        return super(FinancialPrepApi, self).fetch_balance_sheet_statement(ticker)['financials']

    def fetch_cash_flow_statement(self, ticker, interval=StockApi.ANNUAL_INTERVAL):
        return super(FinancialPrepApi, self).fetch_cash_flow_statement(ticker)['financials']
 
    @classmethod
    def get_date(cls, report):
        return report[cls.DATE_KEY]

    @classmethod
    def get_revenue(cls, report):
        return report[cls.REVENUE_KEY]

    @classmethod
    def get_net_income(cls, report):
        return report[cls.NET_INCOME_KEY]

    @classmethod
    def get_free_cash_flow(cls, report):
        return report[cls.FCF_KEY]

    @classmethod
    def get_equity(cls, report):
        return report[cls.EQUITY_KEY]

    @classmethod
    def get_debt(cls, report):
        return report[cls.DEBT_KEY]


class UnibitApi(StockApi):
    API_DOMAIN = 'https://api.unibit.ai'
    API_NAMESPACE = 'api'
    API_VERSION = 'financials'
#    PROFILE_ENDPOINT = 'company/profile'
#    FINANCIALS_ENDPOINT = 'company-key-metrics'
#    GROWTH_ENDPOINT = 'financial-statement-growth'
#    RATIOS_ENDPOINT = 'financial-ratios'
#    DCF_ENDPOINT = 'discounted-cash-flow'
    INCOME_ENDPOINT = 'income_statement'
    BALANCE_SHEET_ENDPOINT = 'balance_sheet'
    CASH_FLOW_ENDPOINT = 'cash_flow'

    DATE_KEY = 'reportDate'
    REVENUE_KEY = 'totalRevenue'
    NET_INCOME_KEY = 'netIncome'
    EQUITY_KEY = 'totalStockholderEquity'
    DEBT_KEY = 'totalLiabilities'
    OCF_KEY = 'totalCashFlowOperating'
    CAPEX_KEY = 'capitalExpenditures'
    OUTSTANDING_SHARES_KEY = 'commonStock'

    ACCESS_KEY = os.environ['UNIBIT_ACCESS_KEY']

    def _build_url(self, endpoint, ticker):
        return os.path.join(
          self.API_DOMAIN, self.API_NAMESPACE, self.API_VERSION, ticker
        )

    def fetch_income_statement(self, ticker, interval=StockApi.ANNUAL_INTERVAL, **kwargs):
        query = dict(
          type=self.INCOME_ENDPOINT, interval=interval, AccessKey=self.ACCESS_KEY, **kwargs
        )
        return super().fetch_income_statement(ticker, **query)['Income Statement']

    def fetch_balance_sheet_statement(self, ticker, interval=StockApi.ANNUAL_INTERVAL, **kwargs):
        query = dict(
          type=self.BALANCE_SHEET_ENDPOINT, interval=interval, AccessKey=self.ACCESS_KEY, **kwargs
        )
        return super().fetch_balance_sheet_statement(ticker, **query)['Balance Sheet']

    def fetch_cash_flow_statement(self, ticker, interval=StockApi.ANNUAL_INTERVAL, **kwargs):
        query = dict(
          type=self.CASH_FLOW_ENDPOINT, interval=interval, AccessKey=self.ACCESS_KEY, **kwargs
        )
        return super().fetch_cash_flow_statement(ticker, **query)['Cash Flow']

    @classmethod
    @skip
    def get_date(cls, report):
        return report[cls.DATE_KEY]

    @classmethod
    @skip
    def get_revenue(cls, report):
        return float(report[cls.REVENUE_KEY].replace(',', ''))

    @classmethod
    @skip
    def get_net_income(cls, report):
        return float(report[cls.NET_INCOME_KEY].replace(',', ''))

    @classmethod
    @skip
    def get_free_cash_flow(cls, report):
        ocf = report[cls.OCF_KEY].replace(',', '')
        capex = report[cls.CAPEX_KEY].replace(',', '')  # assumed negative
        return float(ocf) + float(capex)

    @classmethod
    @skip
    def get_equity(cls, report):
        return float(report[cls.EQUITY_KEY].replace(',', ''))

    @classmethod
    @skip
    def get_debt(cls, report):
        return float(report[cls.DEBT_KEY].replace(',', ''))


class AlphavantageApi(StockApi):
    API_DOMAIN = 'https://www.alphavantage.co'
    API_NAMESPACE = 'query'
    API_VERSION = ''
 
    ACCESS_KEY = os.environ['ALPHAVANTAGE_API_KEY']

    def _build_url(self, ticker):
        return os.path.join(
          self.API_DOMAIN, self.API_NAMESPACE, ticker
        )
  
    @pickle_cache
    def get_price_history(self, ticker):
        query = {
          'function': 'TIME_SERIES_MONTHLY',
          'symbol': ticker,
          'apikey': self.ACCESS_KEY,
        }
        url = self._append_query(self._build_url(ticker), **query)
        resp = requests.get(url)
        return resp.json()['Monthly Time Series']

    def get_price(self, ticker, date):
        history = self.get_price_history(ticker)
        return history[date]


if __name__ == '__main__':
    api = AlphavantageApi()
    print(api.get_price_history('aapl'))
    print(api.get_price('aapl', '2019-03-29'))

