from datetime import datetime
import argparse
import os
import pickle
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


COLUMNS_FILEPATH = './columns.txt'


def get_columns():
    columns = []
    with open(COLUMNS_FILEPATH, 'r') as f:
        for line in f.readlines():
            columns.append(line.strip())
    return columns


WISHLIST_TICKERS_FILEPATH = './tickers.txt'
WISHLIST_COLUMN_NAMES = get_columns()

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


MY_NUMBER = "my number"


def get_google_service():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILEPATH):
        with open(GOOGLE_TOKEN_FILEPATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILEPATH, SPREADSHEET_SCOPES)
            creds = flow.run_local_server()
        with open(GOOGLE_TOKEN_FILEPATH, 'wb') as token:
            pickle.dump(creds, token)
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
    def _(ticker, force=False):
        pickle_filepath = derive_pickle_filepath(ticker)
        if os.path.isfile(pickle_filepath) and force is False:
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
def fetch_metrics(ticker, force=False):
    profile = fetch_company_profile(ticker)
    financials = fetch_financials(ticker)
    growth = fetch_growth(ticker)
    
    metrics = {'ticker': ticker}
    metrics.update(profile)
    metrics.update(financials)
    metrics.update(growth)
    return metrics


MY_PS = 2
MY_PE = 15
MY_PFCF = 10
MY_PB = 4
def calc_derived_metrics(metrics):
    PS = max(float(metrics['Price to Sales Ratio']), 1)
    PE = max(float(metrics['Net Income per Share']), 1)
    FCF = max(float(metrics['Free Cash Flow per Share']), 1)
    PB = max(float(metrics['Book Value per Share']), 1)
    return {
        MY_NUMBER: (MY_PE * MY_PFCF * MY_PB * PE * FCF * PB) ** (1/3),
        'Price': '=GOOGLEFINANCE("{}", "price")'.format(ticker)
    }


def write_to_googlesheets(service, range, row, colnames=None):
    # Use colnames for order. Row is dictionary where colnames are keys.
    sheet = service.spreadsheets()
    row_values = [str(row[colname]) for colname in colnames]
    values = [row_values]
    body = {
        'values': values
    }
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID, range=range, valueInputOption='USER_ENTERED', body=body).execute()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--googlesheets', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    tickers = []
    with open(WISHLIST_TICKERS_FILEPATH, 'r') as f:
        for line in f.readlines():
            tickers.append(line.strip())
    service = get_google_service()
    
    sheet_range = '{}!A'.format(datetime.today().date())
    writerows = []
    writerows.append({colname: colname for colname in WISHLIST_COLUMN_NAMES})
    for ticker in tickers:
        metrics = fetch_metrics(ticker, args.force)
        metrics.update(calc_derived_metrics(metrics))
        writerows.append(metrics)

    for i, writerow in zip(range(1, len(writerows)+1), writerows):
        print(','.join([str(writerow[col]) for col in WISHLIST_COLUMN_NAMES]))
        if args.googlesheets:
            write_to_googlesheets(service, '{}{}'.format(sheet_range, i), writerow, WISHLIST_COLUMN_NAMES)
