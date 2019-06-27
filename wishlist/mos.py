import argparse
import os
import requests
from utils import get_google_service, write_to_googlesheets
from stockapi import UnibitApi, FinancialPrepApi


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


def main(args):
    ticker = args.ticker
    googlesheets = args.googlesheets
    interval = args.interval
    size = args.size

#    if interval == 'quarterly':
    api = UnibitApi()
#    else:
#        api = FinancialPrepApi()

    service = get_google_service()

    incomes = api.fetch_income_statement(ticker, interval=interval, size=size)
    balances = api.fetch_balance_sheet_statement(ticker, interval=interval, size=size)
    cash_flows = api.fetch_cash_flow_statement(ticker, interval=interval, size=size)

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

    def _build_growth_formula(col, i):
        return '=({col}{current}-{col}{prev})/{col}{prev}'.format(col=col, current=i+2, prev=i+3)

    for i, income, balance, cash_flow in zip(range(len(incomes)), incomes, balances, cash_flows):
        date = api.get_date(income)
        revenue = api.get_revenue(income)
        net_income = api.get_net_income(income)
        fcf = api.get_free_cash_flow(cash_flow)
        equity = api.get_equity(balance)
        debt = api.get_debt(balance)
        
        writerow = {
          DATE_COLUMN: date, 
          REVENUE_COLUMN: revenue, 
          REVENUE_GROWTH_COLUMN: _build_growth_formula('B', i),
          NET_INCOME_COLUMN: net_income, 
          NET_INCOME_GROWTH_COLUMN: _build_growth_formula('D', i),
          FREE_CASH_FLOW_COLUMN: fcf, 
          FCF_GROWTH_COLUMN: _build_growth_formula('F', i),
          EQUITY_COLUMN: equity,
          EQUITY_GROWTH_COLUMN: _build_growth_formula('H', i),
          DEBT_COLUMN: debt,
          DEBT_GROWTH_COLUMN: _build_growth_formula('J', i),
        }
        writerows.append(writerow)

    print('outlines: {}'.format(writerows))

    if googlesheets:
        for i, row in enumerate(writerows):
            _range = '{}!A{}'.format(ticker, i+1)
            write_to_googlesheets(service, SPREADSHEET_ID, _range, row, headers)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ticker')
    parser.add_argument('--googlesheets', action='store_true')
    parser.add_argument('--interval', default='annual')
    parser.add_argument('--size', default='10')
    args = parser.parse_args()

    main(args)

