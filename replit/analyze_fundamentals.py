import json
import requests
from tradier import fetch_valuation_ratios

import pandas as pd



def graph_historical_valuations(symbol, start_date=None, ax=None):
  url = 'https://www.macrotrends.net/stocks/charts/AAPL/apple/pe-ratio'
  headers = {
      'User-Agent': (
          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
          '(KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
      )
  }
  resp = requests.get(url, headers=headers)
  
  
  #data = pd.read_html(url, skiprows=1)

  #df = pd.DataFrame(data[0])
  print('vjw df', resp)