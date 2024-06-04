import statistics
import math
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta

from utils import fetch_past_earnings_dates, printout

from tradier import (
  make_api_request,
  get_last_price,
  fetch_historical_prices,
  fetch_options_expirations,
  fetch_options_chain,
  fetch_next_earnings_date,
)

from constants import SHOULD_AVOID_EARNINGS


START_DATE = '2020-04-01'
REFERENCE_CONFIDENCE = 0.158


def select_max_iv_contract(chain):
  if not chain:
    raise ValueError('No options found')

#  print(chain)

  max_seen = 0
  max_index = -1
  for i, option in enumerate(chain):
    bid_iv = option['greeks']['bid_iv']

    if bid_iv > max_seen:
      max_seen = bid_iv
      max_index = i
  return chain[max_index]


def calc_historical_price_movement_stats(prices, period=1, ax=None):
  earnings_dates = set(fetch_past_earnings_dates())

  price_moves = []

  high_52 = 0
  low_52 = 1_000_000_000
  year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
  # iterate from 0 to len - period
  for i in range(0, len(prices) - period):

    # Store high and lows for past year.
    if prices[i]['close'] > high_52 and prices[i]['date'] > year_ago:
      high_52 = prices[i]['close']
    if prices[i]['close'] < low_52 and prices[i]['date'] > year_ago:
      low_52 = prices[i]['close']
  
  
    # save price diff from i to i + period
    price_move = (prices[i + period]['close'] - prices[i]['close'])/prices[i]['close']
    price_moves.append(price_move)

  if ax:
    ax.hist(price_moves)
    ax.legend(title=f'Period={period}')
  
  # return avg, stdev
  return statistics.mean(price_moves), statistics.stdev(price_moves), high_52, low_52


def calc_expected_strike(current_price, mu, sigma, days_to_expiry, zscore):

  exp_price = current_price * (1 + days_to_expiry*mu + sigma/math.sqrt(days_to_expiry))

  
  
  

def determine_overpriced_option_contracts(symbol, start_date=START_DATE, ax=None, expiry_days=None):
  historical_prices = fetch_historical_prices(symbol, start_date)
  last_close = historical_prices[-1]['close']
  printout(f'Latest price: {last_close}')

  prices = historical_prices
  
  # Get all expirations up to 7 weeks.
  expirations = fetch_options_expirations(symbol)[1:7]

  expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime('%Y-%m-%d') if expiry_days else None
  default_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
  
  # NOTE next earnings call date - consider up to week before earnings.
  next_earnings_date = fetch_next_earnings_date(symbol)

  # String comparisons default to 'z' to ensure min works properly.
  date_cutoff = min(next_earnings_date or 'z', expiry_date or 'z', default_date)

  # If there is no next earnings date, use 2 months from now right before theta crush.
  printout(f'Next earnings date: {next_earnings_date}')
  printout()
  expirations = [expiry for expiry in expirations if (datetime.strptime(date_cutoff, '%Y-%m-%d') - datetime.strptime(expiry, '%Y-%m-%d')).days > 0]



  # Find highest IV contract expiry.
  combined_chain = []
  for expiry in expirations:
    combined_chain += fetch_options_chain(symbol, expiry, 'call', last_close, plus_minus=31)
  
  if len(combined_chain) == 0:
    printout('No suitable options found.')
    return []
  
  max_iv_contract = select_max_iv_contract(combined_chain)
  max_iv_expiry = max_iv_contract['expiration_date']
  #if max_iv_expiry == today:
    
  
  # Strategy: if market thinks strike at delta = 0.158 is HIGHER than my expected +1 sigma strike, sell covered call.
  #    aka Rule: if strike(delta=0.158) > S, sell CC.

  days_to_expiry = expiry_days or (datetime.strptime(max_iv_expiry, '%Y-%m-%d').date() - date.today()).days # don't add one to not count date of sale
  printout(f'Days to max IV contract expiry: {days_to_expiry}')
  printout()

  # Calculate average price change and sigma of 1 day.
  mu, sigma, high_52, low_52 = calc_historical_price_movement_stats(prices, days_to_expiry, ax=ax)

  printout(f'52 week high: {high_52}')

  # Pull closest strike to S (= expected avg+1 sigma) and delta D of chain.
  exp_strike = last_close * (1 + mu + sigma)
  printout(f'My expected 1 sigma move price INCREASE: {round(exp_strike, 2)} (aka {REFERENCE_CONFIDENCE} confidence)')
  printout(f' mu: {round(mu*100, 4)}%, sigma: {round(sigma * 100, 4)}%')
  
  this_chain = fetch_options_chain(symbol, max_iv_expiry, 'call', exp_strike, plus_minus=3)
  printout('-')

  ret = []

  # 2 price points to sell CC:
  #    1) at S if D is > 0.158
  #      Ex. market: current price is $85. At avg+1 sigma = $100 and marketDelta = 50%, I sell CC at $100 because I think price won't hit $100.
  #    2) at market delta = 0.158 if strike > S
  #      Ex. market: current price is $85. At marketDelta = 15.8%, strike is $110. But avg+1 sigma = $90 so I think $110 is basically zero so sell CC at $110.
  for contract in this_chain:
    strike = contract['strike']
    delta = contract['greeks']['delta']
    bid = contract['bid']
    ask = contract['ask']
    last = contract['last']
    printout(contract['description'])
    printout(f' bid={bid}, ask={ask} last={last} delta={round(delta, 4)}')
    should_sell_cc = abs((strike - exp_strike)/exp_strike) < .02 and delta > REFERENCE_CONFIDENCE
    printout(f' Sell cc? {should_sell_cc}')
    if should_sell_cc:
      roi = bid / strike
      printout(f' ROI: {round(roi, 2)}')
      annualized_roi = roi * 365 / days_to_expiry
      printout(f' Annualized ROI: {round(annualized_roi, 2)}')
      printout(f' is strike higher than within 1% of 52 week high? {strike > high_52*.99}')
      contract['annual_roi'] = annualized_roi
      ret.append(contract)

  printout()
  printout('*' * 10)
  printout()
  
  # Do same thing for CSEP.
  printout(f'52 week low: {low_52}')
  
  exp_strike = last_close * (1 + mu - sigma)
  
  printout(f'My expected 1 sigma move price DECREASE: {round(exp_strike, 2)} (aka {REFERENCE_CONFIDENCE} confidence)')
  printout(f' mu: {round(mu*100, 4)}%, sigma: {round(sigma * 100, 4)}%')
  printout()

  this_chain = fetch_options_chain(symbol, max_iv_expiry, 'put', exp_strike, plus_minus=3)
  
  for contract in this_chain:
    strike = contract['strike']
    delta = contract['greeks']['delta'] * -1
    bid = contract['bid']
    ask = contract['ask']
    last = contract['last']
    printout(contract['description'])
    printout(f' bid={bid} ask={ask} last={last} delta={round(delta, 4)}')
    should_sell = abs((strike - exp_strike)/exp_strike) < .02 and delta > REFERENCE_CONFIDENCE
    printout(f' Sell CSEP? {should_sell}')
    if should_sell:
      roi = bid / strike
      printout(f' ROI: {round(roi, 2)}')
      annualized_roi = roi * 365 / days_to_expiry
      printout(f' Annualized ROI: {round(annualized_roi, 2)}')
      #print(' is strike higher than within 1% of 52 week high?', strike > high_52*.99)
      contract['annual_roi'] = annualized_roi
      ret.append(contract)
  
  printout()
  return ret
  


  









