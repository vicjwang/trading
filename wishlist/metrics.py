from constants import MEAN_RATIOS, PS_KEY, PE_KEY, PB_KEY, PFCF_KEY, POCF_KEY



def calc_mean_price(sps, eps, ocfps, fcfps, bps, sector):
    mean_ratios = MEAN_RATIOS[sector]
    return (max(sps, 1) * mean_ratios[PS_KEY]
            * max(eps, 1) * mean_ratios[PE_KEY]
            * max(ocfps, 1) * mean_ratios[POCF_KEY]
            * max(fcfps, 1) * mean_ratios[PFCF_KEY]
            * max(bps, 1) * mean_ratios[PB_KEY]) ** (1.0/5.0)

