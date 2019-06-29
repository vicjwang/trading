import arrow
import requests
import os
from datetime import datetime
from utils import skip, pickle_cache, clean_float


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

    RPS_KEY = 'Revenue per Share'
    EPS_KEY = 'Net Income per Share'
    FCFPS_KEY = 'Free Cash Flow per Share'
    BPS_KEY = 'Book Value per Share'

    PS_KEY = 'Price to Sales Ratio'
    PE_KEY = 'PE ratio'
    PFCF_KEY = 'PFCF ratio'
    PB_KEY = 'PB ratio'
 
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

    def fetch_company_metrics(self, ticker, interval=StockApi.ANNUAL_INTERVAL):
        url = self._build_url(self.FINANCIALS_ENDPOINT, ticker)
        resp = requests.get(url)
        return resp.json()['metrics']
 
    @classmethod
    def get_date(cls, report):
        date = report[cls.DATE_KEY]
        return date

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

    @classmethod
    def get_ps(cls, metrics):
        return metrics[cls.PS_KEY]

    @classmethod
    def get_pe(cls, metrics):
        return metrics[cls.PE_KEY]

    @classmethod
    def get_pfcf(cls, metrics):
        return metrics[cls.PFCF_KEY]

    @classmethod
    def get_pb(cls, metrics):
        return metrics[cls.PB_KEY]


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
        date = report[cls.DATE_KEY]
        return datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')

    @classmethod
    @clean_float
    @skip
    def get_revenue(cls, report):
        return report[cls.REVENUE_KEY]

    @classmethod
    @clean_float
    @skip
    def get_net_income(cls, report):
        return report[cls.NET_INCOME_KEY]

    @classmethod
    @skip
    def get_free_cash_flow(cls, report):
        ocf = report[cls.OCF_KEY].replace(',', '')
        capex = report[cls.CAPEX_KEY].replace(',', '')  # assumed negative
        return (float(ocf) + float(capex)) * 1000

    @classmethod
    @clean_float
    @skip
    def get_equity(cls, report):
        return report[cls.EQUITY_KEY]

    @classmethod
    @clean_float
    @skip
    def get_debt(cls, report):
        return report[cls.DEBT_KEY]

    @classmethod
    @clean_float
    def get_shares(cls, report):
        return report[cls.OUTSTANDING_SHARES_KEY]


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

    @classmethod
    def get_price(cls, raw_history, date, key='close'):
        history = {YYYYmmdd[:-3]: prices for YYYYmmdd, prices in list(raw_history.items())}
        keys = ['open', 'high', 'low', 'close', 'volume']
        labels = ['{}. {}'.format(i+1, key) for i, key in enumerate(keys)]
        labelsByKeys = dict(zip(keys, labels))
        YYYYmm = date[:-3]
        return history[YYYYmm][labelsByKeys[key]]


if __name__ == '__main__':
    api = AlphavantageApi()

