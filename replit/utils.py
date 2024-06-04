
import csv
from constants import IS_VERBOSE


def printout(s=''):
  if not IS_VERBOSE:
    return

  print(s)



def fetch_past_earnings_dates():
  with open('earnings_dates/mdb.csv', 'r') as f:
    dates = f.read().splitlines()
    return dates