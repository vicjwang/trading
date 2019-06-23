import os
import pickle


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SPREADSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PICKLE_EXT = '.pkl'
GOOGLE_TOKEN_FILEPATH = './token' + PICKLE_EXT
COLUMNS_FILEPATH = './columns.txt'
DATA_DIR = './data'
GOOGLE_CREDENTIALS_FILEPATH = 'credentials.json'


def get_columns():
    columns = []
    with open(COLUMNS_FILEPATH, 'r') as f:
        for line in f.readlines():
            columns.append(line.strip())
    return columns


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


def write_to_googlesheets(service, spreadsheetId, range, row, colnames):
    # Use colnames for order. Row is dictionary where colnames are keys.
    sheet = service.spreadsheets()
    row_values = [str(row[colname]) for colname in colnames]
    values = [row_values]
    body = {
        'values': values
    }
    result = sheet.values().update(
        spreadsheetId=spreadsheetId, range=range, valueInputOption='USER_ENTERED', body=body).execute()


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


