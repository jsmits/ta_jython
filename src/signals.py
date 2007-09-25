import random
r = random.Random()

def ma_co(candles, ma_type, params, direction):
    "MA cross-over signal"
    if len(candles) > params: # pre-condition
        ma = getattr(candles, ma_type)(params)
        if direction == 1: # up
            if candles[-2][4] < ma[-2]: # cascading conditions
                if candles[-1][4] > ma[-1]:
                    return True
            return False
        if direction == -1: # down
            if candles[-2][4] > ma[-2]: # cascading conditions
                if candles[-1][4] < ma[-1]:
                    return True
            return False
        
def macd_co(candles, params, direction):
    "MACD cross-over"
    pass        

def tick_co(ticks, entry_time, entry_value, border):
    last_tick = ticks[-1].value
    if border == abs(border): # positive border
        if last_tick >= entry_value + border:
            return True
        else:
            return False
    if not border == abs(border): # negative border
        if last_tick <= entry_value + border:
            return True
        else:
            return False
        
def entry_long_tops_generic_1(ticker, l, s):
    ticks = ticker.ticks
    tl = ticks.cs(l).tops()
    if len(tl) >= 2: # pre-condition
        if tl[-2].is_high and tl[-1].is_HL: # condition 1
            ts = ticks.cs(s).tops()
            if ts[-2].is_high and ts[-1].is_low: # condition 2
                if tl[-2].high > ts[-2].high and tl[-1].low < ts[-1].low: # condition 3
                    for i in range(2, len(ticks)): # very important -2 not -1
                        if ticks[-i].date <= ts[-1].date: break 
                        if ticks[-i].value >= ts[-2].high or ticks[-i].value <= ts[-1].low: # condition 4
                            return False
                    if ticks[-1].value >= ts[-2].high: # final condition 5
                        return True
    return False

def entry_long_tops_generic_2(ticker, l, s):
    ticks = ticker.ticks
    tl = ticks.cs(l).tops()
    if len(tl) >= 2: # pre-condition
        if tl[-2].is_low and tl[-1].is_high: # condition 1
            candles = ticks.cs(s)
            ts = ticks.cs(s).tops()
            if ts[-1].is_low and ts[-1].low > tl[-2].low: # condition 2 and 3
                if candles[-2][0] == ts[-1].date and ts[-1].no_tops == 1: # condition 4 and 5
                    print "long generic 2, date=%s, l=%s, s=%s" % (str(ticks[-1].date), l, s)
                    return True
    return False

def entry_short_tops_generic_1(ticker, l, s):
    ticks = ticker.ticks
    tl = ticks.cs(l).tops()
    if len(tl) >= 2: # pre-condition
        if tl[-2].is_low and tl[-1].is_LH: # condition 1
            ts = ticks.cs(s).tops()
            if ts[-2].is_low and ts[-1].is_high: # condition 2
                if tl[-2].low < ts[-2].low and tl[-1].high > ts[-1].high: # condition 3
                    for i in range(2, len(ticks)): # very important -2 not -1
                        if ticks[-i].date <= ts[-1].date: break 
                        if ticks[-i].value >= ts[-1].high or ticks[-i].value <= ts[-2].low: # condition 4
                            return False
                    if ticks[-1].value <= ts[-2].low: # final condition 5
                        return True
    return False

def entry_short_tops_generic_2(ticker, l, s):
    ticks = ticker.ticks
    tl = ticks.cs(l).tops()
    if len(tl) >= 2: # pre-condition
        if tl[-2].is_high and tl[-1].is_low: # condition 1
            candles = ticks.cs(s)
            ts = ticks.cs(s).tops()
            if ts[-1].is_high and ts[-1].high < tl[-2].high: # condition 2 and 3
                if candles[-2][0] == ts[-1].date and ts[-1].no_tops == 1: # condition 4 and 5
                    print "short generic 2, date=%s, l=%s, s=%s" % (str(ticks[-1].date), l, s)
                    return True
    return False

# custom signals
def entry_long_signal_A(ticker):
    candles = ticker.ticks.cs(5)
    return ma_co(candles, 'ema', 12, 1)

def entry_short_signal_B(ticker):
    candles = ticker.ticks.cs(3)
    return ma_co(candles, 'sma', 3, -1)

def entry_short_signal_C(ticker):
    candles = ticker.ticks.cs(15)
    return ma_co(candles, 'ema', 11, -1)

def entry_long_random(ticker):
    if r.random() > 0.95:
        return True
    
def entry_short_random(ticker):
    if r.random() > 0.95:
        return True

def exit_long_stop_cross_value_A(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, -0.75)

def exit_long_take_cross_value_B(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, 1.00)

def exit_long_stop_cross_value_AA(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, -1.00)

def exit_long_take_cross_value_BA(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, 1.25)

def exit_long_random(ticker, entry_time, entry_value):
    if r.random() < 0.02:
        return True
    
def exit_short_take_cross_value_A(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, -1.00)

def exit_short_stop_cross_value_B(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, 0.75)

def exit_short_take_cross_value_AA(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, -1.25)

def exit_short_stop_cross_value_BA(ticker, entry_time, entry_value):
    ticks = ticker.ticks
    return tick_co(ticks, entry_time, entry_value, 1.00)

def exit_short_random(ticker, entry_time, entry_value):
    if r.random() < 0.02:
        return True

# tops entries long, generic 1  
def entry_long_tops_1_1(ticker):
    l = 5
    s = 1
    return entry_long_tops_generic_1(ticker, l, s)
  
def entry_long_tops_1_2(ticker):
    l = 10
    s = 1
    return entry_long_tops_generic_1(ticker, l, s)

def entry_long_tops_1_3(ticker):
    l = 15
    s = 1
    return entry_long_tops_generic_1(ticker, l, s)

def entry_long_tops_1_4(ticker):
    l = 20
    s = 1
    return entry_long_tops_generic_1(ticker, l, s)

def entry_long_tops_1_5(ticker):
    l = 30
    s = 1
    return entry_long_tops_generic_1(ticker, l, s)

# tops entries long, generic 2  
def entry_long_tops_2_1(ticker):
    l = 5
    s = 1
    return entry_long_tops_generic_2(ticker, l, s)
  
def entry_long_tops_2_2(ticker):
    l = 10
    s = 1
    return entry_long_tops_generic_2(ticker, l, s)

def entry_long_tops_2_3(ticker):
    l = 15
    s = 1
    return entry_long_tops_generic_2(ticker, l, s)

def entry_long_tops_2_4(ticker):
    l = 20
    s = 1
    return entry_long_tops_generic_2(ticker, l, s)

def entry_long_tops_2_5(ticker):
    l = 30
    s = 1
    return entry_long_tops_generic_2(ticker, l, s)

# tops entries short, generic 1
def entry_short_tops_1_1(ticker):
    l = 5
    s = 1
    return entry_short_tops_generic_1(ticker, l, s)
  
def entry_short_tops_1_2(ticker):
    l = 10
    s = 1
    return entry_short_tops_generic_1(ticker, l, s)

def entry_short_tops_1_3(ticker):
    l = 15
    s = 1
    return entry_short_tops_generic_1(ticker, l, s)

def entry_short_tops_1_4(ticker):
    l = 20
    s = 1
    return entry_short_tops_generic_1(ticker, l, s)

def entry_short_tops_1_5(ticker):
    l = 30
    s = 1
    return entry_short_tops_generic_1(ticker, l, s)

# tops entries short, generic 2
def entry_short_tops_2_1(ticker):
    l = 5
    s = 1
    return entry_short_tops_generic_2(ticker, l, s)
  
def entry_short_tops_2_2(ticker):
    l = 10
    s = 1
    return entry_short_tops_generic_2(ticker, l, s)

def entry_short_tops_2_3(ticker):
    l = 15
    s = 1
    return entry_short_tops_generic_2(ticker, l, s)

def entry_short_tops_2_4(ticker):
    l = 20
    s = 1
    return entry_short_tops_generic_2(ticker, l, s)

def entry_short_tops_2_5(ticker):
    l = 30
    s = 1
    return entry_short_tops_generic_2(ticker, l, s)

available_signals = [
    #entry_long_tops_1_1, entry_long_tops_1_2, entry_long_tops_1_3, entry_long_tops_1_4, entry_long_tops_1_5,
    #entry_short_tops_1_1, entry_short_tops_1_2, entry_short_tops_1_3, entry_short_tops_1_4, entry_short_tops_1_5, 
    entry_long_tops_2_1, entry_long_tops_2_2, entry_long_tops_2_3, entry_long_tops_2_4, entry_long_tops_2_5,
    entry_short_tops_2_1, entry_short_tops_2_2, entry_short_tops_2_3, entry_short_tops_2_4, entry_short_tops_2_5,     
    exit_long_stop_cross_value_A, exit_long_take_cross_value_B, exit_long_stop_cross_value_AA, exit_long_take_cross_value_BA,
    exit_short_take_cross_value_A, exit_short_stop_cross_value_B, exit_short_take_cross_value_AA, exit_short_stop_cross_value_BA
]

