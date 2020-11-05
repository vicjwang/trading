"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    context.ticker = symbol('SPY')
    
    # Rebalance every day, 1 hour after market open.
    algo.schedule_function(
        rebalance,
        algo.date_rules.month_start(4),
        algo.time_rules.market_open(hours=1),
    )
    
    algo.schedule_function(
        rebalance,
        algo.date_rules.month_start(17),
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
    base_universe = QTradableStocksUS()

    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest

    pipe = Pipeline(
        columns={
            'close': yesterday_close,
        },
        screen=base_universe
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    #context.output = algo.pipeline_output('pipeline')

    # These are the securities that we are interested in trading each day.
    #context.security_list = context.output.index
    context.price = data.current(context.ticker, 'price')
    
    history = data.history(context.ticker, 'price', 365, '1d')
    
    context.ma50 = history[-50:].mean()

    context.ma200 = history[-200:].mean()
    
    context.high52 = history.max()

def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    Assuming SPY maxDD is 50%
    50% = rest of cash
    60% = cash / 2
    70% = cash / 4
    80 = cash / 8
    90 = cash / 16
    
    x = (1 - delta) /.1 
    alloc = cash / 2^(5-x) 
    """
    delta = context.price / context.high52
    cash = context.portfolio.cash

    if delta < 1:
        x = (1 - delta) /.1 
        shares = cash /  2**(5-x)  / context.price
        order_target_percent(context.ticker, shares)


def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    record(price=context.price)
    record(ma50=context.ma50)
    record(ma200=context.ma200)
    record(value=context.portfolio.portfolio_value)


def handle_data(context, data):
    """
    Called every minute.
    """
    pass