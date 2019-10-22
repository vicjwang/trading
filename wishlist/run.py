from __future__ import print_function
from datetime import datetime
import argparse
import os
import requests
from constants import *
from utils import get_columns, get_google_service, pickle_cache, write_to_googlesheets
from stockapi import FinancialPrepApi


MY_NUMBER = "my number"


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


def fetch_company_profile(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, PROFILE_ENDPOINT, ticker) + JSON_DATATYPE
    resp = requests.get(url)
    return resp.json()[ticker]


def fetch_financials(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, FINANCIALS_ENDPOINT, ticker) + JSON_DATATYPE
    resp = requests.get(url)
    return resp.json()['metrics'][0]


def fetch_growth(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, GROWTH_ENDPOINT, ticker) + JSON_DATATYPE
    resp = requests.get(url)
    return resp.json()['growth'][0]


def fetch_discounted_cash_flow(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, 'company', DCF_ENDPOINT, ticker) + JSON_DATATYPE
    resp = requests.get(url)
    return {'DCF': resp.json()['DCF']}


@pickle_cache
def fetch_metrics(ticker):
    profile = fetch_company_profile(ticker)
    financials = fetch_financials(ticker)
    growth = fetch_growth(ticker)
    dcf = fetch_discounted_cash_flow(ticker)
    finapi = FinancialPrepApi()
    balance_sheet = finapi.fetch_balance_sheet_statement(ticker)[0]
    
    metrics = {'ticker': ticker}
    metrics.update(profile)
    metrics.update(financials)
    metrics.update(growth)
    metrics.update(dcf)
    metrics.update(balance_sheet)
    return metrics


MY_PS = 2
MY_PE = 14
MY_PFCF = 8
MY_PB = 3
def calc_derived_metrics(metrics):
    PS = float(metrics['Price to Sales Ratio'])
    PE = float(metrics['Net Income per Share'])
    FCF = float(metrics['Free Cash Flow per Share'])
    PB = float(metrics['Book Value per Share'])
    return {
        MY_NUMBER: (MY_PE * MY_PFCF * MY_PB * max(PE, 1.0) * max(FCF, 1.0) * max(PB, 1.0)) ** (1/3),
        'Price': '=GOOGLEFINANCE("{}", "price")'.format(ticker),
        '10 cap FCF': 10.0*FCF,
    }


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('stock_type')
    parser.add_argument('--googlesheets', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    stock_type = args.stock_type

    columns = get_columns(stock_type)

    tickers_filepath = os.path.join(stock_type, TICKERS_FILEPATH)
    tickers = []
    with open(tickers_filepath, 'r') as f:
        for line in f.readlines():
            tickers.append(line.strip())
    service = get_google_service()
    
    sheet_range = '{}!A'.format(datetime.today().date())
    writerows = []
    writerows.append({colname: colname for colname in columns})
    for ticker in tickers:
        try:
          metrics = fetch_metrics(ticker, force=args.force)
          metrics.update(calc_derived_metrics(metrics))
          writerows.append(metrics)
        except Exception as e:
          print('{}: Failed to pull metrics for {}'.format(e, ticker))
          continue

    for i, writerow in zip(range(1, len(writerows)+1), writerows):
        print(','.join([str(writerow[col]) for col in columns]))
        if args.googlesheets:
            spreadsheet_id = SPREADSHEETS[stock_type]
            write_to_googlesheets(service, spreadsheet_id, '{}{}'.format(sheet_range, i), writerow, columns)
