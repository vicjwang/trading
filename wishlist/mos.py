import argparse
import os
import requests
from constants import *
from utils import get_google_service, write_to_googlesheets


SPREADSHEET_ID = '1NcHqaQ8w8gVvhxiHFw7u55qDAr7QYPEAew-muTjRMSs'
DATE_COLUMN = 'date'
REVENUE_COLUMN = 'revenue'
REVENUE_GROWTH_COLUMN = 'revenue growth'
NET_INCOME_COLUMN = 'net income'
NET_INCOME_GROWTH_COLUMN = 'net income growth'
FREE_CASH_FLOW_COLUMN = 'free cash flow'
FCF_GROWTH_COLUMN = 'fcf growth'
EQUITY_COLUMN = 'equity column'
EQUITY_GROWTH_COLUMN = 'equity growth column'
DEBT_COLUMN = 'debt'
DEBT_GROWTH_COLUMN = 'debt growth'


def fetch_income_statement(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, INCOME_ENDPOINT, ticker)
    resp = requests.get(url)
    return resp.json()['financials']


def fetch_balance_sheet_statement(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, BALANCE_SHEET_ENDPOINT, ticker)
    resp = requests.get(url)
    return resp.json()['financials']


def fetch_cash_flow_statement(ticker):
    url = os.path.join(API_DOMAIN, API_NAMESPACE, API_VERSION, CASH_FLOW_ENDPOINT, ticker)
    resp = requests.get(url)
    return resp.json()['financials']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ticker')
    args = parser.parse_args()
    ticker = args.ticker

    service = get_google_service()

    incomes = fetch_income_statement(ticker)
    balances = fetch_balance_sheet_statement(ticker)
    cash_flows = fetch_cash_flow_statement(ticker)

    headers = [
      DATE_COLUMN,
      REVENUE_COLUMN,
      REVENUE_GROWTH_COLUMN,
      NET_INCOME_COLUMN,
      NET_INCOME_GROWTH_COLUMN,
      FREE_CASH_FLOW_COLUMN,
      FCF_GROWTH_COLUMN,
      EQUITY_COLUMN,
      EQUITY_GROWTH_COLUMN,
      DEBT_COLUMN,
      DEBT_GROWTH_COLUMN,
    ]
    writerows = []
    writerows.append({header: header for header in headers})

    for i, income, balance, cash_flow in zip(range(2, len(incomes)), incomes, balances, cash_flows):
        date = income['date']
        revenue = income['Revenue']
        net_income = income['Net Income']
        fcf = cash_flow['Free Cash Flow']
        equity = balance['Total shareholders equity']
        debt = balance['Total debt']
        
        writerow = {
          DATE_COLUMN: date, 
          REVENUE_COLUMN: revenue, 
          REVENUE_GROWTH_COLUMN: '=(B{current}-B{prev})/B{prev}'.format(current=i, prev=i+1),
          NET_INCOME_COLUMN: net_income, 
          NET_INCOME_GROWTH_COLUMN: '=(D{current}-D{prev})/D{prev}'.format(current=i, prev=i+1),
          FREE_CASH_FLOW_COLUMN: fcf, 
          FCF_GROWTH_COLUMN: '=(F{current}-F{prev})/F{prev}'.format(current=i, prev=i+1),
          EQUITY_COLUMN: equity,
          EQUITY_GROWTH_COLUMN: '=(H{current}-H{prev})/H{prev}'.format(current=i, prev=i+1),
          DEBT_COLUMN: debt,
          DEBT_GROWTH_COLUMN: '=(J{current}-J{prev})/J{prev}'.format(current=i, prev=i+1),
        }
        writerows.append(writerow)

    for i, row in enumerate(writerows):
        _range = '{}!A{}'.format(ticker, i+1)
        write_to_googlesheets(service, SPREADSHEET_ID, _range, row, headers)


    


