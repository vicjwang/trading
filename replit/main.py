import os
import pickle
import pandas as pd
import requests
import matplotlib.pyplot as plt

from datetime import datetime

from analyze_options import determine_overpriced_option_contracts
from collections import namedtuple, defaultdict
#from analyze_fundamentals import graph_historical_valuations
from constants import SHOULD_AVOID_EARNINGS

from utils import printout

SHOW_GRAPH = False

SHOW_TICKERS = defaultdict(
  bool,
  dict(
    #AAPL=1,
    #ABNB=1,
    #AMZN=1,
    #CRM=1,
    CRWD=1,
    #DDOG=1,
    #GOOG=1,
    #OKTA=1,
    #META=1,
    #MDB=1,
    #GME=1,
    #MSFT=1,
    #MSTR=1,
    #NVDA=1,
    #SHOP=1,
    #SNAP=1,
    #SQ=1,
    #TSLA=1,
    #TWLO=1,
    TSM=1,
    TXN=1,
  )
)



START_DATE = '2023-01-01'  # rate cut?
#START_DATE = '2020-04-01' # COVID
EXPIRY_DAYS = None

# Get the list of tickers
RENDER_FIG = False

Ticker = namedtuple('Ticker', ['symbol', 'name', 'next_earnings'], defaults=(None, None, None))

TICKERS = [
  Ticker('AAPL', name='Apple Inc.', next_earnings='2024-07-26'),
  Ticker(symbol='ABNB', name='Airbnb', next_earnings='2024-08-01'),
  Ticker(symbol='AMZN', name='amazon', next_earnings='2024-08-01'),
  Ticker(symbol='BRK/B', name='berkshire'),
  Ticker('CRM', name='Salesforce'),
  Ticker(symbol='CRWD', name='crowdstrike', next_earnings='2024-06-04'),
  Ticker(symbol='DIS', name='disney', next_earnings='2024-08-14'),
  Ticker(symbol='DDOG', name='datadog', next_earnings='2024-08-07'),
  Ticker(symbol='GOOG', name='google', next_earnings='2024-07-23'),
  Ticker(symbol='HTZ', name='hertz'),
  Ticker(symbol='META', name='facebook', next_earnings='2024-07-24'),
  Ticker(symbol='MDB', name='mongodb', next_earnings='2024-08-30'),
  Ticker(symbol='MSFT', name='microsoft', next_earnings='2024-07-22'),
  Ticker(symbol='MSTR', name='Microstrategy', next_earnings='2024-07-30'),
  Ticker(symbol='NET', name='Cloudflare', next_earnings='2024-08-01'),
  Ticker(symbol='NVDA', name='nvidia', next_earnings='2024-08-21'),
  Ticker(symbol='OKTA', name='okta', next_earnings='2024-08-29'),
  Ticker(symbol='SHOP', name='Shopify', next_earnings='2024-08-07'),
  Ticker(symbol='SNAP', name='snapchat', next_earnings='2024-07-23'),
  Ticker(symbol='SQ', name='Square'),
  Ticker(symbol='SVOL', name='SVOL'),
  Ticker(symbol='TSLA', name='tesla', next_earnings='2024-07-16'),
  Ticker(symbol='TWLO', name='twilio', next_earnings='2024-08-13'),
  Ticker(symbol='TSM', name='TSM', next_earnings='2024-07-18'),
  Ticker(symbol='TXN', name='Texas Instruments', next_earnings='2024-07-23'),
  #Ticker(symbol='GME', name='Gamestop'),
]


def cache():
  def decorator(func):
    def wrapper(*args, **kwargs):
      file_name = func.__name__ + '_' + '-'.join(args) + '.pkl'
      if os.path.exists(file_name):
        # If the pickle file exists, load the cached result
        with open(file_name, 'rb') as file:
          result = pickle.load(file)
      else:
        # If the file doesn't exist, call the function and cache the result
        result = func(*args, **kwargs)
        with open(file_name, 'wb') as file:
          pickle.dump(result, file)
      return result
    return wrapper
  return decorator




#@cache
def fetch_raw_pe(symbol, company):
  url = f'https://www.macrotrends.net/stocks/charts/{symbol}/{company}/pe-ratio'
  return fetch_raw_historical(url)


def fetch_raw_pfcf(symbol, company):
  url = f'https://www.macrotrends.net/stocks/charts/{symbol}/{company}/price-fcf'
  return fetch_raw_historical(url)


def fetch_raw_historical(url):
  
  headers = {
      'User-Agent': (
          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
          '(KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
      )
  }
  resp = requests.get(url, headers=headers)

  data = pd.read_html(resp.text, skiprows=1)
  return data[0]


def graph_historical_pe(symbol, company, start_date=None, ax=None):
  column_names = ['Date', 'Price', 'EPS', 'PE']
  data = fetch_raw_pe(symbol, company)  
  data.columns = column_names

  date = data['Date'].apply(pd.to_datetime)
  pe = data['PE'].apply(pd.to_numeric)
  pe_mean = round(pe.mean(), 2)
  
  print('Last earnings date:', date.iloc[0])
  print('Last earnings PE:', pe.iloc[0])
  print('Historical mean PE:', pe_mean)

  if ax:
    graph_historical(date.tolist(), pe.tolist(), pe_mean, symbol, ax)


def graph_historical(x, y, mean, title, ax):
  ax.set_title(title)
  ax.plot(x, y)
  ax.plot(x, [mean] * len(x), color='r', linestyle='--')





def main():
  
  tickers = sorted([ticker for ticker in TICKERS if SHOW_TICKERS[ticker.symbol] == 1], key=lambda t: t.symbol)
  
  start_date = START_DATE
  PLT_WIDTH = 13.5
  PLT_HEIGHT = 2.5

  fig = plt.figure(figsize=(PLT_WIDTH, PLT_HEIGHT * 6)) if RENDER_FIG else None

  contracts = []
  
  for i, ticker in enumerate(tickers):
    printout('#' * 70)
    print(ticker)
    ax = fig.add_subplot(len(tickers), 2, i + 1) if fig else None

    next_earnings_date = None
    try:
      next_earnings_date = datetime.strptime(ticker.next_earnings, '%Y-%m-%d')
    except:
      pass

    expiry_days = EXPIRY_DAYS
    
    if next_earnings_date and SHOULD_AVOID_EARNINGS:
      delta_days = (next_earnings_date - datetime.now()).days
      if delta_days > 1:
        expiry_days = delta_days
    
    overpriced_contracts = determine_overpriced_option_contracts(ticker.symbol, start_date, ax, expiry_days)

    for contract in overpriced_contracts:
      ticker = contract['root_symbol']
      desc = contract['description']
      last = contract['last']
      annual_roi = contract['annual_roi']
      print(f' {desc} last={last} annual_roi={round(annual_roi, 2)*100}%')

    contracts += overpriced_contracts
    #graph_historical_pe(ticker.symbol, ticker.name, start_date, ax)
    
    printout()
    printout()

  print(f'Found {len(contracts)} potentially overpriced option contracts:')
  for contract in sorted(contracts, key=lambda c: -c['annual_roi']):
    ticker = contract['root_symbol']
    desc = contract['description']
    last = contract['last']
    annual_roi = contract['annual_roi']
    print(f' {desc} last={last} annual_roi={round(annual_roi*100, 2)}%')


  if SHOW_GRAPH:
    printout('Rendering plot in Output tab...')
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
  main()






