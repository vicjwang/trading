from constants import MEAN_RATIOS, PS_KEY, PE_KEY, PB_KEY, PFCF_KEY, POCF_KEY



def calc_mean_price(sps, eps, ocfps, fcfps, bps, sector):
    mean_ratios = MEAN_RATIOS[sector]
    return (max(sps, 1) * mean_ratios[PS_KEY]
            * max(eps, 1) * mean_ratios[PE_KEY]
            * max(ocfps, 1) * mean_ratios[POCF_KEY]
            * max(fcfps, 1) * mean_ratios[PFCF_KEY]
            * max(bps, 1) * mean_ratios[PB_KEY]) ** (1.0/5.0)


def get_google_attr(ticker, attr):
    return '=GOOGLEFINANCE("{}", "{}")'.format(ticker, attr)


def get_google_price(ticker):
    return '=GOOGLEFINANCE("{}", "price")'.format(ticker)


def calc_10cap_fcfps(fcfps):
    return 10.0*fcfps


def calc_reverse_dcf_growth(ticker, cf, mean_pe):
    return '=1.15*(GOOGLEFINANCE("{}", "price")/max(1, GOOGLEFINANCE("{}", "eps"))/{})^0.2-1'.format(ticker, ticker, mean_pe)


def get_google_low52(ticker):
    return '=GOOGLEFINANCE("{}", "low52")'.format(ticker)


def get_google_high52(ticker):
    return '=GOOGLEFINANCE("{}", "high52")'.format(ticker)


def calc_mean_price_by_attr(sector, key, aps):
    """
    param key:= *_KEY from constants
    param aps:= attribute per share
    """
    mean_ratios = MEAN_RATIOS[sector]
    return mean_ratios[key] * aps
