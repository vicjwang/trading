"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import numpy as np
import quantopian.algorithm as algo
import quantopian.pipeline.filters as Filters
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.factors import SimpleMovingAverage, CustomFactor


UNIVERSE = symbols('AAPL',
                   'GOOG',
                   'MSFT',
                   'AMZN',
                   'NFLX',
                   'TSLA')


MATERIALS_SECTOR = 101                                                                            
INDUSTRIALS_SECTOR = 310                                                                     
FINANCIALS_SECTOR = 103                                                               
UTILITIES_SECTOR = 207                                                                         
CONSUMER_DISCRETIONARY_SECTOR = 205                                                 
CONSUMER_STAPLES_SECTOR = 102                                                         
HEALTHCARE_SECTOR = 206                                                                       
TECHNOLOGY_SECTOR = 311                                                                       
ENERGY_SECTOR = 309                                                                               
COMMUNICATIONS_SECTOR = 308                                                       
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


class TTMFactor(CustomFactor):
    inputs = [Fundamentals.basic_eps_earnings_reports, Fundamentals.basic_eps_earnings_reports_asof_date]
    window_length = 400
    window_safe = True
    outputs = ['eps_ttm']

    def compute(self, today, asset_ids, out, eps, eps_asof_date):
        eps_ttm = [
            (v[d + np.timedelta64(52, 'W') > d[-1]])[
                np.unique(
                    d[d + np.timedelta64(52, 'W') > d[-1]],
                    return_index=True
                )[1]
            ].sum()
            for v, d in zip(eps.T, eps_asof_date.T)
        ]
        out.eps_ttm[:] = eps_ttm


class MyFactor(CustomFactor):  
    # assign any default input(s). not required but maybe convenient.  

    # assign a default window_length. again not required  
    window_length = 2  
    # factors can have multiple outs. if so, then give them names  
    outputs = ['implied_earnings_growth', 
               'sector_mean_pe_price',]
    # =1.15*(Price/max(1, eps)/11.1)^0.2-1


    def compute(self, today, asset_ids, out, close, sector, eps_ttm):  
        # do any logic here  
        # the inputs appear in the same order as assigned above  
        # inputs are numpy arrays.  
        # columns are the assets. rows are the days with the earliest first [0] and most recent last [-1]  

        sector_mean_pe = np.array([MEAN_RATIOS.get(s, {}).get(PE_KEY, 1) for s in sector[0]])

        out.implied_earnings_growth[:] = 1.15 * (close[0]/eps_ttm[0]/sector_mean_pe)**.2 - 1
        out.sector_mean_pe_price[:] =  sector_mean_pe * eps_ttm[0]


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    
    # Rebalance every day, 1 hour after market open.
    algo.schedule_function(
        trade,
        algo.date_rules.month_start(),
        algo.time_rules.market_open(hours=1),
    )

    # Record tracking variables at the end of each day.
    algo.schedule_function(
        record_vars,
        algo.date_rules.month_start(),
        algo.time_rules.market_close(),
    )

    # Create our dynamic stock selector.
    algo.attach_pipeline(make_pipeline(), 'pipeline')


def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation
    on pipeline can be found here:
    https://www.quantopian.com/help#pipeline-title
    """

    # Base universe set to the QTradableStocksUS
    base_universe = Filters.StaticAssets(UNIVERSE)

    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest
    
    pe = Fundamentals.pe_ratio.latest
    pe_avg = SimpleMovingAverage(
        inputs = [Fundamentals.pe_ratio],
        window_length=365*5
    )
    eps = Fundamentals.basic_eps_earnings_reports.latest

    ttmfactor = TTMFactor()
    myfactor = MyFactor(inputs=[
            USEquityPricing.close,
            Fundamentals.morningstar_sector_code,
            ttmfactor.eps_ttm
        ])
    implied_earnings_growth = myfactor.implied_earnings_growth
    sector_mean_pe_price = myfactor.sector_mean_pe_price

    pipe = Pipeline(
        columns={
            'close': yesterday_close,
            'pe': pe,
            'pe_avg': pe_avg,
            'implied_earnings_growth': implied_earnings_growth,
            'sector_mean_pe_price': sector_mean_pe_price,
        },
        screen=base_universe
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = algo.pipeline_output('pipeline')

    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index
    

def trade(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    #this_month = get_datetime('US/Eastern').month 
    #if this_month not in (3, 6, 9, 12):
    #    return
    
    cash = context.portfolio.cash
    stocks = context.output.query('close < 0.7 * sector_mean_pe_price').index
    log.info('Buying {}'.format(len(stocks)))
    
    for stock in stocks:
        stock_price = data.current(stock, 'price')
        shares = int(cash/len(UNIVERSE)/stock_price)
        log.info('Buying {} shares of {}'.format(shares, stock))
        order(stock, shares)
    
    '''
    stocks = context.output.query('pe > 25 & pe > pe_avg').index
    log.info('Selling {}'.format(len(stocks)))
    for stock in stocks:
        if stock in context.portfolio.positions:
            log.info('Selling {}'.format(stock))
            order_target(stock, 0)
    '''
        


def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass


def handle_data(context, data):
    """
    Called every minute.
    """
    pass