from datetime import datetime, timedelta

import indicators

class Candles(list):
    """Hold the candles"""
    def __init__(self, period):
        self.period = period
        self.current = None # current virtual candle
                
    def process_tick(self, tick):
        time, value = tick
        self.current = self.current or [self.__time_boundaries(time), 
            value, value, value, value]
        if time <= self.current[0]:
            self.current[4] = value # reset close
            if value > self.current[2]: # compare with high
                self.current[2] = value # update high
            elif value < self.current[3]: # compare with low
                self.current[3] = value # update low
        else:
            self.append(tuple(self.current))
            if time.date() > self.current[0].date():
                # next day, do not fill gap
                self.current = [self.__time_boundaries(time), value, value, 
                                value, value]
            else:
                # same day, fill gaps if needed
                candle_time = self.current[0] + timedelta(minutes=self.period)
                while time > candle_time: # fill gaps
                    close = self.current[4]
                    self.append((candle_time, close, close, close, close))
                    candle_time += timedelta(minutes=self.period)
                self.current = [candle_time, value, value, value, value]
        
    def __time_boundaries(self, time):
        minute = time.minute
        sm = minute - minute % self.period
        st = datetime(time.year, time.month, time.day, time.hour, sm, 0)
        et = st + timedelta(minutes=self.period)
        return et
    
    def __getattr__(self, name):
        # gets the indicators and calculates them
        # example on: 
        # http://mail.python.org/pipermail/python-list/2002-April/141153.html
        func = getattr(indicators, name)
        if func:
            c = self.__class__
            c.temp_method = func
            meth = self.temp_method
            del c.temp_method
            self.__setattr__(name, meth)
            return getattr(self, name)
        
class TickWrapper(object):
    """wrap a tick so that the date can be accessed by tick.date and
       the value can be accessed by date.value
    """
    def __init__(self, ticks, index):
        ticks = ticks[:] # make a copy otherwise it becomes recursive
        self.date = ticks[index][0]
        self.value = ticks[index][1]
    
    def __getitem__(self, i):
        if i == 0: return self.date
        elif i == 1: return self.value
        else:
            raise IndexError, "index out of range: %s" % i
    
class Ticks(list):
    """Define a tick list"""
    def __init__(self):
        self.cache = {}
        
    def candles(self, period):
        candles_key = period
        cs, start_index = self.cache.get(candles_key, (Candles(period), 0))
        for tick in self[start_index:]:
            cs.process_tick(tick)
        self.cache[candles_key] = cs, len(self)
        return cs
    
    def cs(self, period):
        """Alias for candles(self, ...)"""
        return self.candles(period)
    
    def __getitem__(self, i):
        return TickWrapper(self, i) 
    
class Ticker(object):
    """Hold ticker data"""
    def __init__(self, *args, **kwargs):
        self.ticks = Ticks()
        for key, value in kwargs.items():
            self.__setattr__(key, value)
        # PM add strategy validation, portfolio link, and orders
    
if __name__=='__main__':
    
    ticks = [(datetime(2006,12,5,9,30,0), 12.55),
             (datetime(2006,12,5,9,30,15), 13.02),
             (datetime(2006,12,5,9,30,30), 12.53),
             (datetime(2006,12,5,9,30,45), 13.04),
             (datetime(2006,12,5,9,31,5), 13.08),
             (datetime(2006,12,5,9,34,15), 13.28),
             (datetime(2006,12,5,9,34,30), 13.05),
             (datetime(2006,12,5,9,34,35), 13.02),
             (datetime(2006,12,5,9,34,43), 12.53),
             (datetime(2006,12,5,9,35,45), 13.04),
             (datetime(2006,12,5,9,36,5), 13.08),
             (datetime(2006,12,5,9,38,15), 13.28)]
    
    start = datetime(2006,12,5,9,30)
    end = datetime(2007, 12, 5, 9, 30)
    
    def tick_generator(start=datetime(2006,12,5,9,30), 
        end=datetime(2006,12,8,9,30)):
        from random import random
        value = 12.55
        while start < end:
            yield start, value
            start += timedelta(seconds=13)
            sign = random()
            if sign > 0.5 or value < 2:
                value += random()
            elif sign < 0.5:
                value -= random()
    
    t = Ticks()
    signal_count = 0
    from signals import entry_signal_A, entry_signal_B, entry_signal_C
    import time
    
    tl = [tick for tick in tick_generator()]
    sl = [entry_signal_A, entry_signal_B, entry_signal_C]
    
    start = datetime.now()
    for tick in tl[:2000]:
        t.append(tick)
        for si in sl:
            if si(t):
                signal_count +=1
        #time.sleep(0.001)
    end = datetime.now()
    
    print end - start
    print signal_count
        
    def update_ticks():
        for tick in tick_generator(start=datetime(2006,12,9,9,30), 
                end=datetime(2006,12,9,15,30)):
            t.append(tick)
    
    
        