from stockapi import FinancialPrepApi


HEADERS = [
    'date',
    'price',
    'eps',
    'eps growth yoy',
    '5 year dcf',
]

def get_close(ticker, date):
    return '=INDEX(GOOGLEFINANCE("{ticker}", "price", "{date}"))'.format(ticker=ticker, date=date)

def main():
    # 
    ticker = 'DIS'
    api = FinancialPrepApi()
    incomes = api.fetch_income_statement(ticker)
    dates = [x['date'] for x in incomes]

    for income in incomes:
        date = income['date']
        close = get_close(ticker, date)
        eps = income['EPS']
        print(date, close, eps)


if __name__ == '__main__':
    
    main()
