from random import randrange, shuffle
from signals import entry_long_signal_A, entry_long_random, exit_long_stop_cross_value_A, exit_long_take_cross_value_B, exit_long_random 
from signals import entry_short_signal_B, entry_short_signal_C, entry_short_random
from signals import exit_short_take_cross_value_A, exit_short_stop_cross_value_B, exit_short_random

class Strategy(object):
    """Strategy holder and evaluator"""
    def __init__(self, signals=[], start=None, end=None):
        self.signals = signals
        self.start = start
        self.end = end
        
    def check_entry(self, ticker):
        signals = [s for s in self.signals if s.__name__.startswith("entry_")]
        for signal in signals:
            if signal(ticker): return signal.__name__

    def check_exit(self, ticker, entry_time, entry_value, entry_direction):
        signals = [s for s in self.signals 
                   if s.__name__.startswith("exit_%s" % entry_direction)]
        for signal in signals:
            if signal(ticker, entry_time, entry_value): return signal.__name__
            
    def inside_trading_time(self, d):
        if self.start and self.end:
            if d.time() >= self.start and d.time() < self.end:
                return True
            else: 
                return False
        return True
            
strategy_1 = Strategy(signals=[
    entry_long_signal_A, entry_long_random, 
    exit_long_stop_cross_value_A, exit_long_take_cross_value_B, exit_long_random, 
    entry_short_signal_B, entry_short_signal_C, entry_short_random,
    exit_short_take_cross_value_A, exit_short_stop_cross_value_B, exit_short_random]
)

def random_signal_combos_generator(signals, output=100, exclude_combos=[]):
    """Return a list of unique signal combinations."""
    entry_signals = [s for s in signals if s.__name__.startswith('entry')]
    exit_signals = [s for s in signals if s.__name__.startswith('exit')]
    exit_long_takes = [s for s in exit_signals if s.__name__.startswith('exit_long_take')]
    exit_long_stops = [s for s in exit_signals if s.__name__.startswith('exit_long_stop')]
    exit_short_takes = [s for s in exit_signals if s.__name__.startswith('exit_short_take')]
    exit_short_stops = [s for s in exit_signals if s.__name__.startswith('exit_short_stop')]
    
    signal_combos = []
    tried = 0
    while not len(signal_combos) == output:
        ens, exs = [], []
        entry_signals_copy = entry_signals[:] # make a copy
        for j in range(randrange(1, 6)): # choose nr of entry signals, min 1, max 5
            # now pick the signals
            l = len(entry_signals_copy)
            if l == 0: break
            index = randrange(l)
            es = entry_signals_copy.pop(index)
            ens.append(es)
        enls = len([s for s in ens if s.__name__.startswith('entry_long')])
        enss = len([s for s in ens if s.__name__.startswith('entry_short')])
        if enls:
            exit_long_takes_copy = exit_long_takes[:]
            for k in range(randrange(1, 4)):
                l = len(exit_long_takes_copy)
                if l == 0: break
                index = randrange(l)
                ees = exit_long_takes_copy.pop(index)
                exs.append(ees)
            exit_long_stops_copy = exit_long_stops[:]
            for k in range(randrange(1, 4)):
                l = len(exit_long_stops_copy)
                if l == 0: break
                index = randrange(l)
                ees = exit_long_stops_copy.pop(index)
                exs.append(ees)
        if enss:
            exit_short_takes_copy = exit_short_takes[:]
            for k in range(randrange(1, 4)):
                l = len(exit_short_takes_copy)
                if l == 0: break
                index = randrange(l)
                ees = exit_short_takes_copy.pop(index)
                exs.append(ees)
            exit_short_stops_copy = exit_short_stops[:]
            for k in range(randrange(1, 4)):
                l = len(exit_short_stops_copy)
                if l == 0: break
                index = randrange(l)
                ees = exit_short_stops_copy.pop(index)
                exs.append(ees)
        if len(exs) > 1:
            shuffle(exs) # shuffle the exit signals
        sss = ens + exs
        if not sss in signal_combos and not sss in exclude_combos:
            signal_combos.append(sss)
        tried += 1
        if tried > 10000 * output:
            print "tried too many times"
            break
    return signal_combos

if __name__ == '__main__':
    from signals import available_signals
    
    signal_combos = random_signal_combos_generator(available_signals, 50)
                
        