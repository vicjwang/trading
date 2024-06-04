import os
from pandas.core.common import not_none
import requests
import statistics
import json

from datetime import datetime
from utils import printout


TRADIER_API_KEY = os.environ['TRADIER_API_KEY']


def make_api_request(endpoint, params):
  response = requests.get(
    endpoint,
    params=params,
    headers={'Authorization': f'Bearer {TRADIER_API_KEY}', 'Accept': 'application/json'}
  )
  json_response = response.json()
  return json_response


def get_last_price(symbol):
  endpoint = 'https://api.tradier.com/v1/markets/quotes'
  params = {'symbols': 'symbol', 'greeks': 'false'}
  return make_api_request(symbol)


def fetch_historical_prices(symbol, start_date, end_date = None):
  endpoint = 'https://api.tradier.com/v1/markets/history'
  params = {'symbol': symbol, 'interval': 'daily', 'start': start_date, 'end': end_date, 'session_filter': 'open'}
  return make_api_request(endpoint, params)['history']['day']


def fetch_options_expirations(symbol):
  endpoint = 'https://api.tradier.com/v1/markets/options/expirations'
  params = {'symbol': symbol, 'includeAllRoots': 'true', 'strikes': 'false'}
  return make_api_request(endpoint, params)['expirations']['date']


def fetch_options_chain(symbol, expiry_date, option_type=None, ref_price=None, plus_minus=0):
  endpoint = 'https://api.tradier.com/v1/markets/options/chains'
  params = {'symbol': symbol, 'expiration': expiry_date, 'greeks': 'true'}
  chain = make_api_request(endpoint, params)['options']['option']

  printout(f'Found {len(chain)} options for {symbol} {expiry_date}')

  if ref_price:
    chain = [option for option in chain if abs(option['strike'] - ref_price) < plus_minus]

  if option_type:
    chain = [option for option in chain if option['option_type'] == option_type]

  chain = sorted(chain, key=lambda option: option['strike'])
  return chain


def fetch_next_earnings_date(symbol):
  endpoint = 'https://api.tradier.com/beta/markets/fundamentals/calendars'
  params = {'symbols': symbol}
  events = make_api_request(endpoint, params)[0]['results'][0]['tables']['corporate_calendars']
  relevant_events = []
  if not events:
    return None

  for event in events:
    if event['event_type'] != 14:
      continue
    if event['begin_date_time'][:4] == str(datetime.now().year):
       relevant_events.append(event)

  next_event = sorted(relevant_events, key=lambda x: x['begin_date_time'])[0]['begin_date_time']
  today_str = str(datetime.now().date())
  return next_event if next_event > today_str else None


def fetch_valuation_ratios(symbol):
  endpoint = 'https://api.tradier.com/beta/markets/fundamentals/ratios'
  params = {'symbols': symbol}
  response = make_api_request(endpoint, params)
  return response