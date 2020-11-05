"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import quantopian.algorithm as algo
import numpy as np
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS
from quantopian.pipeline.classifiers.fundamentals import Sector
from quantopian.pipeline.data import morningstar, Fundamentals
from quantopian.pipeline.factors import SimpleMovingAverage


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    context.capacity = 30
    context.annual_add = 10000
    
    #schedule for buying a week after the year start
    algo.schedule_function(func=schedule_task_a,
                      date_rule=date_rules.month_start(4),
                      time_rule=time_rules.market_open())
    #schedule for selling losers a week before the year start
    algo.schedule_function(func=schedule_task_b,
                      date_rule=date_rules.month_end(4),
                      time_rule=time_rules.market_open())
    '''
    #schedule for selling winners on the 7th day of year start
    algo.schedule_function(func=schedule_task_c,
                      date_rule=date_rules.month_start(3),
                      time_rule=time_rules.market_close())
    '''
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
    mask = QTradableStocksUS() & Sector().notnull()
    mask &= (Fundamentals.market_cap.latest > 1000000000)
    mask &= (
        (Fundamentals.morningstar_sector_code.latest != 103) &
        (Fundamentals.morningstar_sector_code.latest != 207) &
        (Fundamentals.morningstar_sector_code.latest != 206) &
        (Fundamentals.morningstar_sector_code.latest != 309) &
        (Fundamentals.morningstar_industry_code.latest != 20533080) &
        (Fundamentals.morningstar_industry_code.latest != 10217033) &
        (Fundamentals.morningstar_industry_group_code != 10106) &
        (Fundamentals.morningstar_industry_group_code != 10104)
    )
    
    #mask &= (Fundamentals.total_debt_equity_ratio.latest < 1.0)
    
    earnings_yield = Fundamentals.ebit.latest/Fundamentals.enterprise_value.latest
    EY_rank   = earnings_yield.rank(ascending=False, mask=mask)
    
    roic      = Fundamentals.roic.latest
    roic_rank = roic          .rank(ascending=False, mask=mask)
    
    debt_equity = Fundamentals.total_debt_equity_ratio.latest
    debt_equity_rank = debt_equity.rank(ascending=True, mask=mask)  # lower is better
    
    div_yield = Fundamentals.trailing_dividend_yield.latest
    div_rank = div_yield.rank(ascending=False, mask=mask)  # higher is better
    
    gross_margin = Fundamentals.gross_margin.latest
    gross_margin_rank = gross_margin.rank(ascending=False, mask=mask)
    
    rnd_ocf = Fundamentals.research_and_development.latest / Fundamentals.operating_cash_flow.latest
    rnd_ocf_rank = rnd_ocf.rank(ascending=False, mask=mask)
    
    total_yield = Fundamentals.total_yield.latest
    total_yield_rank = total_yield.rank(ascending=False, mask=mask)
    
    ma50 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=50, mask=mask)
    ma200 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=200, mask=mask)
    mv_yield = ma50 / ma200
    mv_yield_rank = mv_yield.rank(ascending=False, mask=mask)
    
    revenue_growth = Fundamentals.revenue_growth.latest
    revenue_growth_rank = revenue_growth.rank(ascending=False, mask=mask)
    
    
    mf_rank   = np.sum([
                        EY_rank,
                        roic_rank,  # returns = 24.12%, alpha = -.09, beta = 1.3, sharpe = .47, drawdown = -27.95%
                        #debt_equity_rank, # returns = 35.45%, alpha = -.04, beta = 1.18, sharpe = .65, drawdown = -30.26%
                        #div_rank,  # returns = 30.44%, alpha = -.05, beta = 1.07, sharpe = .65, drawdown = -22.73%
                        #gross_margin_rank,
                        #rnd_ocf_rank,
                        #total_yield_rank,
                        #revenue_growth_rank,
                        #
                       ])

    
    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest

    pipe = Pipeline(
        columns={
            'mf_rank'       : mf_rank,
        },
        screen=mask
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = algo.pipeline_output('pipeline').sort_values(by='mf_rank', ascending=True).head(int(context.capacity)).dropna()
    # context.stocks = sorted_rank[0:int(context.capacity)]
    
    # weight as rank normalize 0 to 1
    context.output['weight'] = np.array(context.output.reset_index()['mf_rank'].sort_values(ascending=False) / context.output['mf_rank'].sum())



def schedule_task_a(context, data):
    today = get_datetime('US/Eastern')
    if today.month == 1:
        for stock in context.portfolio.positions:
            position = context.portfolio.positions[stock]
            log.info('{}: {} shares'.format(stock, position.amount))
        for stock in context.output.index:
            weight = context.output.T[stock]['weight']
            alloc = weight * context.annual_add
            price = data.current(stock, 'price')
            shares = alloc / price
            order(stock, shares)

            #order_target_percent(stock, weight)    

            
#selling losers
def schedule_task_b(context, data):
    today = get_datetime('US/Eastern')
    if today.month == 12 and context.portfolio.positions_value != 0:
        for stock in context.portfolio.positions:
            if context.portfolio.positions[stock].cost_basis > data.current(stock, 'price'):
                order_target_percent(stock, 0)            
                log.info('sold {}'.format(stock))
 
#selling winners
def schedule_task_c(context, data):
    today = get_datetime('US/Eastern')
    if today.month == 1:
        for stock in context.portfolio.positions:
            order_target_percent(stock, 0)
 

def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    portfolio = context.portfolio
    record(positions_value=portfolio.positions_value)
    record(actual_returns=(portfolio.positions_value + portfolio.capital_used)/max(1, abs(portfolio.capital_used)))
    record(capital_used=portfolio.capital_used)


def handle_data(context, data):
    """
    Called every minute.
    """
    pass