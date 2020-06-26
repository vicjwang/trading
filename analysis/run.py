from __future__ import print_function
from datetime import datetime
import argparse
import numpy as np
import os
import requests
import time
import traceback
from constants import *
from utils import get_columns, get_google_service, pickle_cache, write_to_googlesheets, retry, nonnegative_or_blank 
from stockapi import FinancialPrepApi, AlphavantageApi
from metrics import (
  calc_composite_mean_price, calc_10cap_fcfps, calc_reverse_dcf_growth, get_google_attr, calc_mean_price_by_attr
)

MY_NUMBER = "my number"
API_KEY = os.environ['FIN_PREP_API_KEY']


def find_spreadsheet_id(portfolio_name):
  if portfolio_name in SPREADSHEETS:
    return SPREADSHEETS[portfolio_name]
  with open('./{}/spreadsheet_id'.format(portfolio_name), 'r') as f:
    text = f.read().strip()
    return text

def main():
    # Keep separate file of tickers
    # Add to google spreadsheet. Create tab labeled with current YYYY-MM-DD
    # Keep list of personal preference constants
    # company profile https://financialmodelingprep.com/api/company/profile/AAPL
    # Pull current financials from https://financialmodelingprep.com/api/v3/company-key-metrics/GOOGL
    # Pull growth numbers from https://financialmodelingprep.com/api/v3/financial-statement-growth/AAPL
    # Profitability margin https://financialmodelingprep.com/api/financial-ratios/AAPL
    # Master, Management, Moat, Margin of safety
    pass


PERIOD_ANNUAL = 'annual'
PERIOD_QUARTER = 'quarter'

def fetch_company_profile(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, PROFILE_ENDPOINT, ticker) + JSON_DATATYPE + '&apikey={}'.format(API_KEY)
    resp = requests.get(url)
    if not resp.ok:
        raise Error('Invalid response: {}'.format(url))
    print('vjw {}'.format(resp.json()))
    return resp.json().get(ticker, {})


def fetch_financials(ticker, period=PERIOD_ANNUAL, n=1):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, FINANCIALS_ENDPOINT, ticker) + JSON_DATATYPE + '&apikey={}'.format(API_KEY)
    if period == 'quarter':
        url += '&period=quarter'
    resp = requests.get(url)
    if not resp.ok:
        raise Error('Invalid response: {}'.format(url))
    return resp.json()['metrics'][:n]


def fetch_growth(ticker, period=PERIOD_ANNUAL, n=1):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, GROWTH_ENDPOINT, ticker) + JSON_DATATYPE + '&apikey={}'.format(API_KEY)
    if period == 'quarter':
        url += '&period=quarter'
    resp = requests.get(url)
    if not resp.ok:
        raise Error('Invalid response: {}'.format(url))
    return resp.json()['growth'][:n]


def fetch_discounted_cash_flow(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, 'company', DCF_ENDPOINT, ticker) + JSON_DATATYPE + '&apikey={}'.format(API_KEY)
    resp = requests.get(url)
    if not resp.ok:
        raise Error('Invalid response: {}'.format(url))

    return {'DCF': resp.json().get('dcf', '')}


def fetch_sma(ticker):
    api = AlphavantageApi()
    sma200 = api.get_sma(ticker, 200)
    sma50 = api.get_sma(ticker, 50)
    return {
      'sma200': sma200,
      'sma50': sma50,
    }


@retry
@pickle_cache
def fetch_metrics(ticker, period=PERIOD_ANNUAL):
    profile = fetch_company_profile(ticker)
    financials = fetch_financials(ticker, period=period)[0]
    growth = fetch_growth(ticker, period=period)[0]
    dcf = fetch_discounted_cash_flow(ticker)
    finapi = FinancialPrepApi()
    balance_sheet = finapi.fetch_balance_sheet_statement(ticker, interval=period)[0]
    sma = fetch_sma(ticker)
    
    metrics = {'ticker': ticker}
    metrics.update(profile)
    metrics.update(financials)
    metrics.update(growth)
    metrics.update(dcf)
    metrics.update(balance_sheet)
    metrics.update(sma)
    return metrics


def get_historical_stats(ticker, attr):
    items = fetch_financials(ticker, n=20)
    values = [ round(float(item[attr]), 2) for item in items if item[attr] ]
    return max(values), min(values), np.mean(values)


@retry
def calc_derived_metrics(ticker, metrics):
    try:
        rps = float(metrics['Revenue per Share'])
        eps = float(metrics['Net Income per Share'])
        fcfps = float(metrics['Free Cash Flow per Share'])
        bps = float(metrics['Book Value per Share'])
        ocfps = float(metrics['Operating Cash Flow per Share'])

        co_pe_high, co_pe_low, co_pe_avg = get_historical_stats(ticker, 'PE ratio')
        co_pb_high, co_pb_low, co_pb_avg = get_historical_stats(ticker, 'PB ratio')
        
        sector = metrics['sector']
        sector_mean_pe = MEAN_RATIOS[sector][PE_KEY]
        sector_mean_fcf = MEAN_RATIOS[sector][PFCF_KEY]
        sector_mean_ps = MEAN_RATIOS[sector][PS_KEY]

        cash = metrics['Cash and cash equivalents']
        market_cap = metrics['Market Cap']
        implied_growth = calc_reverse_dcf_growth(ticker, sector_mean_pe)
        return {
            '#': '',
            'composite sector mean price': calc_composite_mean_price(rps, eps, ocfps, fcfps, bps, metrics['sector']),
            'Price': get_google_attr(ticker, 'price'),
            '10 cap FCF': calc_10cap_fcfps(fcfps),
            'implied growth': implied_growth,
            '15x pe': eps * 15,
            'lynch value': eps * float(metrics['10Y Net Income Growth (per Share)']) * 100,
            'low52': get_google_attr(ticker, 'low52'),
            'high52': get_google_attr(ticker, 'high52'),
            'co mean pe price': co_pe_avg * eps,
            'co high pe price': co_pe_high * eps,
            'co low pe price': co_pe_low * eps,
            'co mean pb price': co_pb_avg * bps,
            'co high pb price': co_pb_high * bps,
            'co low pb price': co_pb_low * bps,
            'sector mean ps price': calc_mean_price_by_attr(sector, PS_KEY, rps),
            'sector mean pe price': calc_mean_price_by_attr(sector, PE_KEY, eps),
            'sector mean pfcf price': calc_mean_price_by_attr(sector, PFCF_KEY, fcfps),
            'sector mean pb price': calc_mean_price_by_attr(sector, PB_KEY, bps),
            'sector mean pocf price': calc_mean_price_by_attr(sector, POCF_KEY, ocfps),
            'price to cash': '{}/{}'.format(get_google_attr(ticker, 'marketcap'), cash),
}
    except ValueError:
        return {
            'composite mean price': '',
            'Price': '=GOOGLEFINANCE("{}", "price")'.format(ticker),
            '10 cap FCF': '',
        }


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('portfolio_name')
    parser.add_argument('--googlesheets', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--quarter', action='store_true')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    portfolio_name = args.portfolio_name
    period = PERIOD_QUARTER if args.quarter else PERIOD_ANNUAL
    offset = args.offset
    limit = args.limit
    debug = args.debug
    verbose = args.verbose
    assert os.environ['PYTHONHASHSEED']

    columns = get_columns(portfolio_name)

    tickers_filepath = os.path.join(portfolio_name, TICKERS_FILEPATH)
    tickers = []
    with open(tickers_filepath, 'r') as f:
        for line in f.readlines():
            if line.startswith('#') or not line.strip():
                continue
            tickers.append(line.strip())
    service = get_google_service()
    end_index = len(tickers) if limit is None else offset + limit
    
    sheet_range = '{}!A'.format(datetime.today().date())
    writerows = []
    writerows.append({colname: colname for colname in columns})
    for ticker in tickers[offset:end_index]:

        if verbose:
            print('Fetching {} data...'.format(ticker))
        try:
          metrics = fetch_metrics(ticker, force=args.force, period=period)
          metrics.update(calc_derived_metrics(ticker, metrics))
          writerows.append(metrics)
        except Exception as e:
          if verbose:
              print('{}: Failed to pull metrics for {}'.format(e, ticker))
          if debug:
              traceback.print_exc()
              raise e
          continue

    for i, writerow in zip(range(1, len(writerows)+1), writerows):
        if verbose:
            print(','.join([str(writerow.get(col, '')) if writerow.get(col, 0) else '' for col in columns]))
        time.sleep(.1)
        if args.googlesheets:
            spreadsheet_id = find_spreadsheet_id(portfolio_name)
            write_to_googlesheets(service, spreadsheet_id, '{}{}'.format(sheet_range, i), writerow, columns)
