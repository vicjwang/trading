"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS, StaticAssets
from quantopian.pipeline.factors import SimpleMovingAverage

 
SYMBOLS = symbols('QQQ')
WEIGHTS = (1,)


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    context.can_sell = False
    context.monthly_add = 2000

    context.intervals = 0
    context.net_worth = 0
    context.cash = 0

    context.ticker = symbol('SPY')
    # SPY: 208
    # TQQQ: 237
    
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
    base_universe = StaticAssets(SYMBOLS)

    n = 10
    ma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=n, mask=base_universe)


    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest

    pipe = Pipeline(
        columns={
            'close': yesterday_close,
            'ma'   : ma,
        },
        screen=base_universe
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = algo.pipeline_output('pipeline')
    history = data.history(context.ticker, fields='price', bar_count=200, frequency='1d')
    
    context.security_list = context.output.index
    #context.ma10 = history[-10:].mean()
    #context.ma50 = history[-50:].mean()
    #context.ma200 = history.mean()
    n = -50
    context.ma = history[n:].mean()


def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """    
    #stock = context.ticker
    print(data)
    for i, stock in enumerate(context.security_list):
        price = data.current(stock, 'price')
        pos = context.portfolio.positions[stock]
        pos_shares = pos.amount
    
    #stocks = context.output.query('close > ma25').index
        context.cash += context.monthly_add * WEIGHTS[i]
        context.intervals += 1
    
    # True: 164.4, 1.18; MA50: 154, 1.1; MA10: 117.68, 1.07
    #if price > context.ma:  

        if context.can_sell and price < context.ma and pos_shares > 0:  # and price > pos.cost_basis:
            context.cash += pos_shares * price
            order_target_percent(stock, 0)
        else:
            shares = int(context.cash / price)
            stop_price = .95 * price
            context.cash -= (shares * price)
            order(stock, shares)
        
            
        
    """
    price = data.current(symbol('SPY'), 'price')
    shares = 1*context.monthly_add / price
    order(symbol('SPY'), shares) 
    #"""

def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    p = context.portfolio
    #record(ma10=context.ma10)
    #record(ma=context.ma)
    #record(ma200=context.ma200)
    
    #record(price=data.current(context.ticker, 'price'))
    cost = context.intervals * context.monthly_add/len(WEIGHTS) /1000
    
    #actual_returns = (p.positions_value + p.capital_used)/max(1, abs(p.capital_used))
    actual_returns = (context.cash + p.positions_value) / max(cost, 1)
    #record(actual_returns=actual_returns)
    #record(positions_value=p.positions_value)
    net_worth = (context.cash + p.positions_value) / 1000
    record(net_worth=net_worth)
    record(cash=context.cash/1000)
    record(cost=cost)
    #record(positions_value=p.positions_value)
    #record(capital_used=p.capital_used)


def handle_data(context, data):
    """
    Called every minute.
    """
    pass