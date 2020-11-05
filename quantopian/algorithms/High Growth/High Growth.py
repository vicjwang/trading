"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import numpy as np
import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline, CustomFactor
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.classifiers.fundamentals import Sector
from quantopian.pipeline.filters import QTradableStocksUS
from quantopian.pipeline.data import morningstar, Fundamentals as F



class MeanPS(CustomFactor):
    window_length = 252*3 # ~52 weeks * n years
    inputs = [F.ps_ratio]
    
    def compute(self, today, asset_ids, out, ps_ratios):
        ps_mean = np.mean(ps_ratios, axis=0)
        out[:] = ps_mean



def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    context.capacity = 30
    context.annual_add = 10000 # must be >0
    
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
        # Base universe set to the QTradableStocksUS
    mask = QTradableStocksUS() & Sector().notnull()
    mask &= (F.market_cap.latest > 1000000000)
    mask &= (
        (F.morningstar_sector_code.latest != 103) &
        (F.morningstar_sector_code.latest != 207) &
        (F.morningstar_sector_code.latest != 206) &
        (F.morningstar_sector_code.latest != 309) &
        (F.morningstar_industry_code.latest != 20533080) &
        (F.morningstar_industry_code.latest != 10217033) &
        (F.morningstar_industry_group_code != 10106) &
        (F.morningstar_industry_group_code != 10104)
    )
    mask &= (F.morningstar_sector_code.latest == 311)
    revenue_growth = F.revenue_growth.latest
    revenue_growth_rank = revenue_growth.rank(ascending=False, mask=mask)  # higher is better
    
    rule_40 = F.revenue_growth.latest + F.net_margin.latest
    rule_40_rank = rule_40.rank(ascending=False, mask=mask)  # higher is better
    
    ps_ratio = F.ps_ratio.latest
    ps_ratio_rank = ps_ratio.rank(ascending=True, mask=mask)  # lower is better
        
    # relative historical self price to sales
    mean_ps = MeanPS()
    rel_ps = F.ps_ratio.latest / mean_ps 
    rel_ps_rank = rel_ps.rank(ascending=True, mask=mask)  # lower is better
    
    # run rate := cash on hand / operating expense
    run_rate = F.cash_and_cash_equivalents.latest / F.operating_expense
    run_rate_rank = run_rate.rank(ascending=False, mask=mask)  # higher is better
    
    gross_margin = F.gross_margin.latest
    gross_margin_rank = gross_margin.rank(ascending=False, mask=mask)
  

    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest
    
    rank = np.sum([
                   #rule_40_rank,
                   #rel_ps_rank,
                   #run_rate_rank,
                   #revenue_growth_rank,
                   ps_ratio_rank,
                   gross_margin_rank,
                  ])

    pipe = Pipeline(
        columns={
            'close': yesterday_close,
            'rank': rank,
        },
        screen=mask
    )
    return pipe


def before_trading_start(context, data):
    """
    Called every day before market open.
    """

    context.output = algo.pipeline_output('pipeline').sort_values(by='rank', ascending=True).head(int(context.capacity)).dropna()
    # context.stocks = sorted_rank[0:int(context.capacity)]
    
    # weight as rank normalize 0 to 1
    context.output['weight'] = np.array(context.output.reset_index()['rank'].sort_values(ascending=False) / context.output['rank'].sum())



# buying
def schedule_task_a(context, data):
    today = get_datetime('US/Eastern')
    if today.month == 1:
        for stock in context.portfolio.positions:
            position = context.portfolio.positions[stock]
            log.info('{}: {} shares'.format(stock, position.amount))
        log.info(context.output.index)
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