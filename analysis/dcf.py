import argparse
from stockapi import FinancialPrepApi
from utils import write_rows_to_googlesheets

SPREADSHEET_ID = '1zTqWcKLocRn2APfpGL2oIQIoqoVExMji4k0dt231eAU'
HEADERS = [
    'date',
    'close',
    'eps',
    'eps growth yoy',
    '5 year dcf',
]

def get_close(ticker, date):
    return '=INDEX(GOOGLEFINANCE("{ticker}", "price", "{date}"), 2, 2)'.format(ticker=ticker, date=date)

def main(ticker):
    api = FinancialPrepApi()
    incomes = api.fetch_income_statement(ticker)
    metrics_list = api.fetch_company_metrics(ticker)
    writerows = []
    writerows.append(dict(zip(HEADERS, HEADERS)))

    for metrics in reversed(metrics_list):
        date = metrics['date']
        close = get_close(ticker, date)
        eps = metrics['Free Cash Flow per Share']
        row = {'date': date, 'close': close, 'eps': eps}
        writerows.append(row)

    write_rows_to_googlesheets(writerows, HEADERS, SPREADSHEET_ID, ticker)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('ticker')
    args = parser.parse_args()
    ticker = args.ticker
    main(ticker)

    

