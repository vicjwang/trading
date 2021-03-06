import os
import pickle
import time
from datetime import datetime


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SPREADSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
PICKLE_EXT = '.pkl'
GOOGLE_TOKEN_FILEPATH = './token' + PICKLE_EXT
COLUMNS_FILEPATH = './columns.txt'
DATA_DIR = './data'
GOOGLE_CREDENTIALS_FILEPATH = 'credentials.json'


def get_columns(stock_type=None):
    columns = []
    columns_filepath = os.path.join(stock_type, COLUMNS_FILEPATH)
    with open(columns_filepath, 'r') as f:
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
    row_values = [str(row.get(colname, '')) for colname in colnames]
    values = [row_values]
    body = {
        'values': values
    }
    result = sheet.values().update(
        spreadsheetId=spreadsheetId, range=range, valueInputOption='USER_ENTERED', body=body).execute()


def write_rows_to_googlesheets(rows, columns, spreadsheet_id, sheet_name, verbose=False):
    sheet_range = '{}!A'.format(sheet_name)
    service = get_google_service()
    for i, writerow in zip(range(1, len(rows)+1), rows):
        if verbose:
            print(','.join([str(writerow.get(col, '')) for col in columns]))
        time.sleep(.1)
        write_to_googlesheets(service, spreadsheet_id, '{}{}'.format(sheet_range, i), writerow, columns)

def save_to_disk(data, filepath):
    print('Saving to {}'.format(filepath))
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)


def load_from_disk(filepath):
    if not os.path.isfile(filepath):
        return None
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    return data


def derive_pickle_filepath(func, *args, **kwargs):
    filename = '_'.join([func.__name__] + [str(arg) for arg in args] + ['{}-{}'.format(key, value) for key, value in kwargs.items()] + [datetime.now().strftime("%Y%b")])
    filehash = str(hash(filename))
    return os.path.join(DATA_DIR,  filehash + PICKLE_EXT)


def pickle_cache(func):
    def _(*args, force=False, **kwargs):
        pickle_filepath = derive_pickle_filepath(func, *args, **kwargs)
        if os.path.isfile(pickle_filepath) and force is False:
            return load_from_disk(pickle_filepath)
        else:
            data = func(*args, **kwargs)
            save_to_disk(data, pickle_filepath)
            return data
    return _


def skip(func):
    def _(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print('Skipping...', e, func)
            return ''
    return _


def clean_float(func):
    def _(*args, **kwargs):
        return float(func(*args, **kwargs).replace(',', ''))*1000
    return _
       

def retry(func):
    def _(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            now = datetime.now()
            sleep_seconds = 1
            while datetime.now().minute == now.minute:
                time.sleep(sleep_seconds)
                sleep_seconds *= 2
            return func(*args, **kwargs)
    return _


def nonnegative_or_blank(func):
    def _(*args, **kwargs):
        ret = func(*args, **kwargs)
        return ret if ret >= 0 else ''
    return _
