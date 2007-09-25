import datetime
import time
from java.util.concurrent import LinkedBlockingQueue
from java.lang import Runnable
from wrapper import IBResponseHandler, IBClient, TradingEngine, SimConnection
from ticker import Ticker
from simulator import tick_list

def test_strategy(definition, strategy):
    sapp = datetime.datetime.now()
    # initialize tickers
    t = Ticker(**definition)
    t.strategy = strategy
    tickers = {1: t}
    
    # fill the tickers with 'historical data'
    start = datetime.datetime(2003, 6, 16)
    end = datetime.datetime(2003, 6, 23)
    ticks = tick_list('ES', start, end)
    first_day = ticks[0][0].day
    index = 0
    for tick in ticks:
        if not tick[0].day == first_day:
            break
        else:
            t.ticks.append(tick)
            index += 1
    
    # start 'engines'
    tick_queue = LinkedBlockingQueue()
    response_handler = IBResponseHandler(tick_queue)
    connection = SimConnection(response_handler)
    client = IBClient(connection, tickers)
    # initialize trader
    trader = TradingEngine(tick_queue, tickers, client)
    # initialize client
    client.start(trader)
    
    # fill the queue and wait for the queue to be empty
    for tick in ticks[index:]:
        qtick = 1, tick[0], tick[1]
        tick_queue.put(qtick)
        # time.sleep(0.002) # to ease a little on the CPU usage
    
    # wait unitl the queue is consumed
    while tick_queue.size():
        time.sleep(1)
    
    # now show some statistics
    report = {}
    order_map = client.order_map[1] # ticker_id = 1
    # check order validity, entry, exit, entry, exit, etc.
    previous_signal = None
    invalid_sequence = 0
    for order_id in order_map:
        order_entry = client.account['_orders'][order_id]
        signal = order_entry['signal']
        if previous_signal:
            if previous_signal.startswith('entry') and \
                                    not signal.startswith('exit'):
                invalid_sequence += 1
            if previous_signal.startswith('exit') and \
                                    not signal.startswith('entry'):
                invalid_sequence += 1
        previous_signal = signal
    if invalid_sequence: 
        report['valid'] = True
    else: 
        report['valid'] = False
        
    # check number of long and short and order result 
    if not invalid_sequence: 
        entry_long = 0
        entry_short = 0
        long_result = []
        short_result = []
        all_result = []
        ratio = 50
        rt_comm = 4 # round trip commission
        for i in range(len(order_map)-1):
            if i < len(order_map) - 1:
                entry_order_id = order_map[i]
                exit_order_id = order_map[i + 1]
                entry_order = client.account['_orders'][entry_order_id]
                exit_order = client.account['_orders'][exit_order_id]
                entry_value = entry_order['fill_value']
                exit_value = exit_order['fill_value']
                signal = entry_order['signal']
                if signal.startswith('entry_long'): 
                    entry_long += 1
                    value = exit_value - entry_value
                    long_result.append(value)
                    all_result.append(value)
                if signal.startswith('entry_short'): 
                    entry_short += 1
                    value = entry_value - exit_value
                    short_result.append(value)
                    all_result.append(value)
                    
        long_result = [r * ratio for r in long_result]
        report['long_results'] = long_result 
        long_comm = [r - rt_comm for r in long_result]
        report['long_results_with_commission'] = long_comm
        short_result = [r * ratio for r in short_result]
        report['short_results'] = short_result 
        short_comm = [r - rt_comm for r in short_result]
        report['short_results_with_commission'] = short_comm
        all_result = [r * ratio for r in all_result]
        report['all_results'] = all_result
        all_comm = [r - rt_comm for r in all_result]
        report['all_results_with_commission'] = all_comm
        
        report['long_trades'] = entry_long
        report['short_trades'] = entry_short
        report['sum_all_results'] = sum(all_result)
        report['sum_all_results_with_commission'] = sum(all_comm)
        report['sum_long_results'] = sum(long_result)
        report['sum_long_results_with_commission'] = sum(long_comm)
        report['sum_short_results'] = sum(short_result)
        report['sum_short_results_with_commission'] = sum(short_comm)
        
        if all_result:
            avg_all_res = sum(all_result)/len(all_result)
            avg_all_res_comm = sum(all_comm)/len(all_comm)
            report['average_all_results'] = avg_all_res
            report['average_all_results_with_commission'] = avg_all_res_comm
        else:
            report['average_all_results'] = None
            report['average_all_results_with_commission'] = None
        if long_result:
            avg_long_res = sum(long_result)/len(long_result)
            avg_long_res_comm = sum(long_comm)/len(long_comm)
            report['average_long_results'] = avg_long_res
            report['average_long_results_with_commission'] = avg_long_res_comm
        else:
            report['average_long_results'] = None
            report['average_long_results_with_commission'] = None
        if short_result:
            avg_short_res = sum(short_result)/len(short_result)
            avg_short_res_comm = sum(short_comm)/len(short_comm)
            report['average_short_results'] = avg_short_res
            report['average_short_results_with_commission'] = avg_short_res_comm
        else:
            report['average_short_results'] = None
            report['average_short_results_with_commission'] = None
        # calculate total capacity
        capacity = 0
        previous_tick_value = 0
        for tick in ticks[index:]:
            tick_value = tick[1]
            if previous_tick_value:
                cap = abs(tick_value - previous_tick_value)
                capacity += cap
            previous_tick_value = tick_value
        total_capacity = capacity * ratio
        report['total_capacity'] = total_capacity
        res_for_cap = sum(all_comm)*100 / total_capacity
        report['result_for_capacity_percentage'] = res_for_cap

        eapp = datetime.datetime.now()
        report['analysis_time'] = eapp - sapp
        return report
        
class TestRunner(Runnable):
    """Runs a strategy for a given ticker definition"""
    def __init__(self, thread_id, definition, strategies):
        self.thread_id = thread_id
        self.definition = definition
        self.strategies = strategies
        self.count = 0
        
    def run(self):
        for strategy in self.strategies:
            report = test_strategy(self.definition, strategy)
            strategy.report = report
            self.count += 1
            print "thread: %s, tested: %s of %s" % (self.thread_id, self.count, 
                                                    len(self.strategies)) 
        
if __name__ == '__main__':
    
    from java.lang import Thread
    import datetime
    from strategies import random_signal_combos_generator, Strategy
    from signals import available_signals
    
    definition = {'symbol'  : "ES",
                  'secType' : "FUT",
                  'expiry'  : "200712",
                  'exchange': "GLOBEX",
                  'currency': "USD"}
    signal_combos = random_signal_combos_generator(available_signals, 50)
    start_time = datetime.time(9, 30) # times for the test data
    end_time = datetime.time(15,45) # should exit after this
    strategies = [Strategy(signals=combo, start=start_time, end=end_time) 
                  for combo in signal_combos] 
    split = len(strategies) / 2 # divide over tasks
    start = datetime.datetime.now()
    t1 = Thread(TestRunner(1, definition, strategies[:split]))
    t1.start()
    t2 = Thread(TestRunner(2, definition, strategies[split:]))
    t2.start()
    t1.join() # join here after t1 has finished
    t2.join() # join here after t2 has finished
    end = datetime.datetime.now()
    print "finished crunching %s strategies, time: %s, %s seconds per "\
        "strategy" % (len(strategies), str(end - start), 
                      round((end - start).seconds * 1.0 / len(strategies), 2))
    
    for sss in strategies:
        rp = sss.report
        print rp['result_for_capacity_percentage'], rp['long_trades'], \
            rp['short_trades'], rp['sum_all_results_with_commission']
        print sss.signals
        
        
    
    