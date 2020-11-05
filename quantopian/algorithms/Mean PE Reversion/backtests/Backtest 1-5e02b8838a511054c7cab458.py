"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import quantopian.algorithm as algo
import quantopian.pipeline.filters as Filters
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS
from quantopian.pipeline.data import Fundamentals
from quantopian.pipeline.factors import SimpleMovingAverage 


UNIVERSE = symbols('AAPL',
                   'GOOG',
                   'MSFT',
                   'AMZN',
                   'NFLX',
                   'TSLA')


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
        algo.date_rules.every_day(),
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
    #pe_avg = Fundamentals.pe_ratio10_year_average.latest
    pe_avg = SimpleMovingAverage(
        inputs = [Fundamentals.pe_ratio],
        window_length=365*5
    )

    pipe = Pipeline(
        columns={
            'close': yesterday_close,
            'pe': pe,
            'pe_avg': pe_avg,
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
    cash = context.portfolio.cash
    stocks = context.output.query('pe < pe_avg').index
    log.info('Buying {}'.format(len(stocks)))
    
    for stock in stocks:
        log.info('Buying {}'.format(stock))
        order(stock, cash/len(UNIVERSE))
        
    stocks = context.output.query('pe > 25 & pe > pe_avg').index
    log.info('Selling {}'.format(len(stocks)))
    for stock in stocks:
        if stock in context.portfolio.positions:
            log.info('Selling {}'.format(stock))
            order_target(stock, 0)
        


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