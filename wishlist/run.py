from datetime import datetime
import os
import pickle
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


WISHLIST_TICKERS_FILEPATH = './tickers.txt'
WISHLIST_COLUMN_NAMES = [
    'ticker',
    'Price',
    'sector',
    'Beta',
    'LastDiv',
    'Range',

    # key metrics
    'Revenue per Share',
    'Operating Cash Flow per Share',
    'Net Income per Share',
    'Free Cash Flow per Share',

    'Book Value per Share',
    'Shareholders Equity per Share',
    'Graham Number',

    # growth metrics
    'EPS Growth',
    'Free Cash Flow growth',
    '10Y Revenue Growth (per Share)',
    '5Y Revenue Growth (per Share)',
    '3Y Revenue Growth (per Share)',
    '10Y Net Income Growth (per Share)',
    '5Y Net Income Growth (per Share)',
    '3Y Net Income Growth (per Share)',
]


API_DOMAIN = 'https://financialmodelingprep.com'
API_NAMESPACE = 'api'
API_VERSION = 'v3'
PROFILE_ENDPOINT = 'company/profile'
FINANCIALS_ENDPOINT = 'company-key-metrics'
GROWTH_ENDPOINT = 'financial-statement-growth'
RATIOS_ENDPOINT = 'financial-ratios'
JSON_DATATYPE = '?datatype=json'
DATA_DIR = './data'
PICKLE_EXT = '.pkl'

SPREADSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1yljf1CTj7aihKKFx-A3qGMPfvy0AYr1BK9ejWAhOmGI'
GOOGLE_TOKEN_FILEPATH = './token' + PICKLE_EXT
GOOGLE_CREDENTIALS_FILEPATH = '../../credentials.json'


def get_google_service():
    creds = None
    print('vjw exists {}'.format(GOOGLE_TOKEN_FILEPATH))
    if os.path.exists(GOOGLE_TOKEN_FILEPATH):
        with open(GOOGLE_TOKEN_FILEPATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print('vjw expied')
            creds.refresh(Request())
        else:
            print('vjw flow')
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILEPATH, SPREADSHEET_SCOPES)
            creds = flow.run_local_server()
        with open(GOOGLE_TOKEN_FILEPATH, 'wb') as token:
            pickle.dump(creds, token)
    print('vjw creds')
    print(creds)
    return build('sheets', 'v4', credentials=creds)


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


def save_to_disk(data, filepath):
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)


def load_from_disk(filepath):
    if not os.path.isfile(filepath):
        return None
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    return data


def derive_pickle_filepath(ticker):
    return os.path.join(DATA_DIR, ticker + PICKLE_EXT)


def pickle_cache(func):
    def _(ticker):
        pickle_filepath = derive_pickle_filepath(ticker)
        if os.path.isfile(pickle_filepath):
            return load_from_disk(pickle_filepath)
        else:
            data = func(ticker)
            save_to_disk(data, pickle_filepath)
            return data
    return _


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


@pickle_cache
def fetch_metrics(ticker):
    profile = fetch_company_profile(ticker)
    financials = fetch_financials(ticker)
    growth = fetch_growth(ticker)
    
    metrics = {'ticker': ticker}
    metrics.update(profile)
    metrics.update(financials)
    metrics.update(growth)
    return metrics


def write_to_googlesheets(service, range, row, colnames=None):
    # Use colnames for order. Row is dictionary where colnames are keys.
    sheet = service.spreadsheets()
    row_values = [str(row[colname]) for colname in colnames]
    values = [row_values]
    print(','.join(row_values))
    body = {
        'values': values
    }
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID, range=range, valueInputOption='USER_ENTERED', body=body).execute()


if __name__ == '__main__':

    tickers = []
    with open(WISHLIST_TICKERS_FILEPATH, 'r') as f:
        for line in f.readlines():
            tickers.append(line.strip())
    service = get_google_service()
    
    sheet_range = '{}!A'.format(datetime.today().date())
    write_to_googlesheets(service, '{}1'.format(sheet_range), {colname: colname for colname in WISHLIST_COLUMN_NAMES}, WISHLIST_COLUMN_NAMES)
    for i, ticker in zip(range(2, len(tickers)+2), tickers):
        metrics = fetch_metrics(ticker)
        write_to_googlesheets(service, '{}{}'.format(sheet_range, i), metrics, colnames=WISHLIST_COLUMN_NAMES)
