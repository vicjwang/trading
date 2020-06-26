

API_DOMAIN = 'https://financialmodelingprep.com'
API_NAMESPACE = 'api'
API_VERSION = 'v3'
PROFILE_ENDPOINT = 'profile'
FINANCIALS_ENDPOINT = 'company-key-metrics'
GROWTH_ENDPOINT = 'financial-statement-growth'
RATIOS_ENDPOINT = 'financial-ratios'
DCF_ENDPOINT = 'discounted-cash-flow'
JSON_DATATYPE = '?datatype=json'
INCOME_ENDPOINT = 'financials/income-statement'
BALANCE_SHEET_ENDPOINT = 'financials/balance-sheet-statement'
CASH_FLOW_ENDPOINT = 'financials/cash-flow-statement'

WISHLIST_SPREADSHEET_ID = '1yljf1CTj7aihKKFx-A3qGMPfvy0AYr1BK9ejWAhOmGI'
DIVIDEND_SPREADSHEET_ID = '1JTe-XA72s2whTbFQ4ZyI338qRj5339oDMoeAuWL_PgM'
GROWTH_SPREADSHEET_ID = '1ph9wCYSpfetbUhugB1Uj0s_YrLcyULzvpTdAlMUEtps'
CORE_SPREADSHEET_ID = '1jOi8k80C_QOsOG8ZhoQvzWZvNE2XC7hPkvzgy6JW6Sg'
MFPLUS_SPREADSHEET_ID = '1F-XVN65j8VNDr6beFDNBq0ADryXGzJB1iYeoJeyhERg'

TICKERS_FILEPATH = './tickers.txt'

SPREADSHEETS = {
  'dividend': DIVIDEND_SPREADSHEET_ID,
  'growth': GROWTH_SPREADSHEET_ID,
  'wishlist': WISHLIST_SPREADSHEET_ID,
  'core': CORE_SPREADSHEET_ID,
  'mfplus': MFPLUS_SPREADSHEET_ID
}

MATERIALS_SECTOR = 'Basic Materials'
INDUSTRIALS_SECTOR = 'Industrials'
FINANCIALS_SECTOR = 'Financial Services'
UTILITIES_SECTOR = 'Utilities'
CONSUMER_DISCRETIONARY_SECTOR = 'Consumer Defensive'
CONSUMER_STAPLES_SECTOR = 'Consumer Cyclical'
HEALTHCARE_SECTOR = 'Healthcare'
TECHNOLOGY_SECTOR = 'Technology'
ENERGY_SECTOR = 'Energy'
COMMUNICATIONS_SECTOR = 'Communication Services'
PS_KEY = 'PS'
PE_KEY = 'PE'
PB_KEY = 'PB'
PFCF_KEY = 'PFCF'
POCF_KEY = 'POCF'

MEAN_RATIOS = {
  TECHNOLOGY_SECTOR: {
    PS_KEY: 2.5,
    PE_KEY: 29.9,
    PB_KEY: 7.62,
    PFCF_KEY: 1/.0481,
    POCF_KEY: 19.2,
  },
  HEALTHCARE_SECTOR: {
    PS_KEY: 1,
    PE_KEY: 1,
    PB_KEY: 1,
    PFCF_KEY: 1,
    POCF_KEY: 1,
  },
  MATERIALS_SECTOR: {
    PS_KEY: 1,
    PE_KEY: 17,
    PB_KEY: 1.84,
    PFCF_KEY: 1/.0413,
    POCF_KEY: 10,
  },
  INDUSTRIALS_SECTOR: {
    PS_KEY: 1,
    PE_KEY: 19,
    PB_KEY: 5.03,
    PFCF_KEY: 1/.042,
    POCF_KEY: 12,
  },
  FINANCIALS_SECTOR: {
    PS_KEY: 3,
    PE_KEY: 13,
    PB_KEY: 1.62,
    PFCF_KEY: 10,
    POCF_KEY: 10,
  },
  UTILITIES_SECTOR: {
    PS_KEY: 2.9,
    PE_KEY: 25,
    PB_KEY: 2.19,
    PFCF_KEY: 10,
    POCF_KEY: 11.5,
  },
  CONSUMER_DISCRETIONARY_SECTOR: {
    PS_KEY: .97,
    PE_KEY: 18,
    PB_KEY: 8.22,
    PFCF_KEY: 1/3.61,
    POCF_KEY: 10.3,
  },
  CONSUMER_STAPLES_SECTOR: {
    PS_KEY: 1.1,
    PE_KEY: 23,
    PB_KEY: 5.26, 
    PFCF_KEY: 1/.0419,
    POCF_KEY: 13.7,
  },
  ENERGY_SECTOR: {
    PS_KEY: 1.06,
    PE_KEY: 11.1,
    PB_KEY: 1.67, 
    PFCF_KEY: 1/.0433,
    POCF_KEY: 3.88,
  },
  COMMUNICATIONS_SECTOR: {
    PS_KEY: 1.47,
    PE_KEY: 22,
    PB_KEY: 3.36, 
    PFCF_KEY: 1/.0471,
    POCF_KEY: 7.9,
  }


}
