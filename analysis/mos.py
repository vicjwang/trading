import argparse
import os
import requests
from utils import get_google_service, write_to_googlesheets
from stockapi import UnibitApi, FinancialPrepApi, AlphavantageApi

SPREADSHEET_ID = '16mECdYtwd28_Jc2idft2wW8Y8LFEPbzIeW6oHZ-5qNo'
DATE_COLUMN = 'date'
PRICE_COLUMN = 'price'
HIGH_PRICE_COLUMN = 'high'
LOW_PRICE_COLUMN = 'low'
SHARES_COLUMN = 'shares'
REVENUE_COLUMN = 'revenue'
REVENUE_GROWTH_COLUMN = 'revenue growth'
NET_INCOME_COLUMN = 'net income'
NET_INCOME_GROWTH_COLUMN = 'net income growth'
FREE_CASH_FLOW_COLUMN = 'free cash flow'
FCF_GROWTH_COLUMN = 'fcf growth'
EQUITY_COLUMN = 'equity'
EQUITY_GROWTH_COLUMN = 'equity growth'
DEBT_COLUMN = 'debt'
DEBT_GROWTH_COLUMN = 'debt growth'
PS_COLUMN = 'ps ratio'
PE_COLUMN = 'pe ratio'
PCFC_COLUMN = 'pfcf ratio'
PB_COLUMN = 'pb ratio'


def main(args):
    ticker = args.ticker
    googlesheets = args.googlesheets
    interval = args.interval
    size = args.size

    stockapi = AlphavantageApi()
    if interval == 'quarterly':
        finapi = UnibitApi()
    else:
        finapi = FinancialPrepApi()

    service = get_google_service()

    incomes = finapi.fetch_income_statement(ticker, interval=interval)
    balances = finapi.fetch_balance_sheet_statement(ticker, interval=interval)
    cash_flows = finapi.fetch_cash_flow_statement(ticker, interval=interval)
#    price_history = stockapi.get_price_history(ticker)
    metrics_history = finapi.fetch_company_metrics(ticker, interval=interval)

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
      PS_COLUMN,
      PE_COLUMN,
      PCFC_COLUMN,
      PB_COLUMN,

#      SHARES_COLUMN,
#      PRICE_COLUMN,
#      HIGH_PRICE_COLUMN,
#      LOW_PRICE_COLUMN,
    ]
    writerows = []
    writerows.append({header: header for header in headers})

    def _build_growth_formula(col, i):
        return '=({col}{current}-{col}{prev})/{col}{prev}'.format(col=col, current=i+2, prev=i+3)

    for i, income, balance, cash_flow, metrics in zip(range(len(incomes)), incomes, balances, cash_flows, metrics_history):
        date = finapi.get_date(income)
        revenue = finapi.get_revenue(income)
        net_income = finapi.get_net_income(income)
        fcf = finapi.get_free_cash_flow(cash_flow)
        equity = finapi.get_equity(balance)
        debt = finapi.get_debt(balance)
        ps = finapi.get_ps(metrics)
        pe = finapi.get_pe(metrics)
        pfcf = finapi.get_pfcf(metrics)
        pb = finapi.get_pb(metrics)

#        price = stockapi.get_price(price_history, date)
#        high = stockapi.get_price(price_history, date, 'high')
#        low = stockapi.get_price(price_history, date, 'low')
#        shares = finapi.get_shares(balance)
#        
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
#          SHARES_COLUMN: shares,
#          PRICE_COLUMN: price,
#          HIGH_PRICE_COLUMN: high,
#          LOW_PRICE_COLUMN: low,
          PS_COLUMN: ps,
          PE_COLUMN: pe,
          PCFC_COLUMN: pfcf,
          PB_COLUMN: pb,
        }
        writerows.append(writerow)

    print('outlines: {}'.format(writerows))

    if googlesheets:
        print('Writing to googlesheets {} tab.'.format(ticker))
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

