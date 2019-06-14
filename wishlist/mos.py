import argparse
import os
import requests
from constants import *
from utils import get_google_service, write_to_googlesheets


SPREADSHEET_ID = '1NcHqaQ8w8gVvhxiHFw7u55qDAr7QYPEAew-muTjRMSs'


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


    for income, balance, cash_flow in zip(incomes, balances, cash_flows):
        date = income['date']
        revenue = income['Revenue']
        net_income = income['Net Income']
        fcf = cash_flow['Free Cash Flow']
        equity = balance['Total shareholders equity']
        
        writerow = {
          'date': date, 
          'revenue': revenue, 
          'net income': net_income, 
          'free cash flow': fcf, 
          'equity': equity
        }
        _range = '{}!A'.format(ticker)
        write_to_googlesheets(service, SPREADSHEET_ID, _range, writerow, [])


    


