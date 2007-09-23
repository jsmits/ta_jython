def sma(self, params):
    input = []
    output = []
    for candle in self:
        value = candle[4]
        input.append(value)
        outputvalue = None
        if len(input) >= params:
            outputvalue = sum(input[(len(input)-params):len(input)]) / params
        output.append(outputvalue)
    return output

def ema(self, params):
    input = []
    output = []
    for candle in self:
        value = candle[4]
        input.append(value)
        outputvalue = None
        if len(input) == params: # first one is a sma
            outputvalue = sum(input[(len(input)-params):len(input)]) / params
        if len(input) > params:
            outputvalue = ((value-output[-1]) * (2.0/(1+params))) + output[-1]
        output.append(outputvalue)
    return output

class MacdWrapper(list):
    
    def __init__(self, params, short_ema, long_ema, macd):
        self.params = params
        self.short_ema = short_ema
        self.long_ema = long_ema
        self.extend(macd)
        
    def __ema(self):
        params = self.params
        input = []
        output = (params[1]-1) * [None]
        for value in self[params[1]-1:]:
            input.append(value)
            outputvalue = None
            if len(input) == params[2]: # first one is a sma
                outputvalue = (sum(input[(len(input)-params[2]):len(input)]) / 
                               params[2])
            if len(input) > params[2]:
                outputvalue = (((value - output[-1]) * (2.0 / (1+params[2]))) + 
                               output[-1])
            output.append(outputvalue)
        return output
    
    def __getattr__(self, name):
        if name == 'ema':
            return self.__ema()
        

def macd(self, params):
    short_ema = ema(self, params[0])
    long_ema = ema(self, params[1])
    output = []
    for i in range(len(self)):
        outputvalue = None
        if i+1 >= params[1]:
            outputvalue = short_ema[i] - long_ema[i]
        output.append(outputvalue)
    return MacdWrapper(params, short_ema, long_ema, output)

def atr(self, params):
    tr_output = []
    output = []
    for i in range(len(self)):
        candle = self[i]
        high = candle[2]
        low = candle[3]
        if i == 0:
            tr = high - low # (high - low) = initial tr
        else:
            pclose = self[i-1][4]
            tr = max(high - low, abs(high - pclose), abs(low - pclose))
        tr_output.append(tr)
        outputvalue = tr
        if len(tr_output) >= params:
            patr = output[-1]
            atr = ((patr * (params - 1)) + tr_output[-1]) / params
            outputvalue = atr
        output.append(outputvalue)
    return output

class TopCandleWrapper(object):
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index
        self.top = parent.tops[index]
        self.candle = parent.candles[index]
        
    def ux_is_high(self):
        return self.top in [2,12,22,32]
    
    def ux_is_HH(self):
        return self.top == 32
    
    def ux_is_LH(self):
        return self.top == 12
    
    def ux_is_low(self):
        return self.top in [1,11,21,31]
    
    def ux_is_HL(self):
        return self.top == 31
    
    def ux_is_LL(self):
        return self.top == 11
    
    def ux_date(self):
        return self.candle[0]
    
    def ux_open(self):
        return self.candle[1]
    
    def ux_high(self):
        return self.candle[2]
    
    def ux_low(self):
        return self.candle[3]
    
    def ux_close(self):
        return self.candle[4]
    
    def ux_no_tops(self):
        """trailing non-tops after this top"""
        tops = self.parent.tops
        index =  self.index
        no_tops = 0
        while True:
            index += 1
            try:
                if tops[index] == 0: no_tops += 1
                else: break
            except IndexError:
                break
        return no_tops
    
    def __getattr__(self, name):
        """utility methods need a none __ prefix because with __ they are 
        considered private and then they are not accessible!
        """
        method = self.__getattribute__("ux_%s" % name)
        return method()

class TopsWrapper(list):
    """Wrap the tops output and provide some utlity methods"""
    def __init__(self, candles, all_tops):
        self.candles = candles
        self.tops = all_tops
        self.top_indexes = []
        
    def __top_indexes(self):
        indexes = []
        for i in range(len(self.tops)):
            if self.tops[i] != 0: 
                indexes.append(i)
        return indexes
    
    def __getitem__(self, i):
        if not self.top_indexes: 
            self.top_indexes = self.__top_indexes()
        index = self.top_indexes[i]
        return TopCandleWrapper(self, index) 
    
    def __len__(self):
        if not self.top_indexes: 
            self.top_indexes = self.__top_indexes()
        return len(self.top_indexes)

def tops(self):
    """Calculate tops
    0 - no top 
    1 - L; 11 - LL; 21 - EL; 31 - HL
    2 - H; 12 - LH; 22 - EH; 32 - HH
    """
    # signal constants   
    L  =  1
    LL = 11
    EL = 21
    HL = 31
    H  =  2
    LH = 12
    EH = 22
    HH = 32
    
    inputhigh = []
    inputlow = []
    output = []
    
    mark = 0, 0
    ph = [] # previous high list
    pl = [] # previous low list
    
    for candle in self:
        high = candle[2]
        low = candle[3]
        inputhigh.append(high)
        inputlow.append(low)
        
        if len(inputhigh) == 1: # first entry, can never be determined
            output.append(0)
            continue
        
        if high <= inputhigh[mark[0]] and low >= inputlow[mark[0]]: # inside bar
            output.append(0)
            continue
        
        if high > inputhigh[mark[0]] and low < inputlow[mark[0]]: # outside bar
            if ph == [] and pl == []:
                output.append(0)
                mark = len(output)-1, 0
            else:
                output.append(0) # added new code line 17-7-2006 !!!
                output[mark[0]] = 0
                for j in reversed(range(len(output)-1)):
                    if inputhigh[j] > high or inputlow[j] < low: 
                        # first non-inclusive bar
                        break
                # checking for inbetween tops
                count = 0
                for k in range(j+1, len(output)-1): 
                    if output[k] != 0: # top found
                        count += 1
                        if output[k] in [L, LL, EL, HL]: 
                            pl.remove(k) # removing top indexes from list
                        if output[k] in [H, LH, EH, HH]: 
                            ph.remove(k) # idem
                        output[k] = 0 # reset top
                if count > 0:
                    if len(pl) and len(ph):
                        if (pl[-1] > ph[-1]): # if true, low is most recent
                            mark = len(output)-1, 2
                        elif (ph[-1] > pl[-1]): # high is most recent
                            mark = len(output)-1, 1
                    elif len(pl) and not len(ph):
                        mark = len(output)-1, 2
                    elif len(ph) and not len(pl):
                        mark = len(output)-1, 1
                    elif not len(pl) and not len(ph):
                        # current outside bar has become indifferent
                        mark = len(output)-1, 0 
                if count == 0:
                    # set same signal to current outside bar
                    mark = len(output)-1, mark[1] 
            continue
        
        if high > inputhigh[mark[0]] and low >= inputlow[mark[0]]: # upbar
            if mark[1]  < 2: # upbar with previous indifferent or low mark
                if pl == []: 
                    output[mark[0]] = L # L
                else:
                    if inputlow[mark[0]] < inputlow[pl[-1]]: 
                        output[mark[0]] = LL # LL
                    elif inputlow[mark[0]] == inputlow[pl[-1]]: 
                        output[mark[0]] = EL # EL
                    elif inputlow[mark[0]] > inputlow[pl[-1]]: 
                        output[mark[0]] = HL # HL
                pl.append(mark[0])
                mark = len(output), 2
                output.append(0)
            elif mark[1] == 2: # upbar with previous high mark
                output[mark[0]] = 0 # reset previous mark
                mark = len(output), 2
                output.append(0)
            continue 
        
        if high <= inputhigh[mark[0]] and low < inputlow[mark[0]]: # downbar
            if mark[1] != 1: # downbar with previous indifferent or high mark
                if ph == []: 
                    output[mark[0]] = H # H
                else:
                    if inputhigh[mark[0]] < inputhigh[ph[-1]]: 
                        output[mark[0]] = LH # LH
                    elif inputhigh[mark[0]] == inputhigh[ph[-1]]: 
                        output[mark[0]] = EH # EH
                    elif inputhigh[mark[0]]  > inputhigh[ph[-1]]: 
                        output[mark[0]] = HH # HH
                ph.append(mark[0])
                mark = len(output), 1
                output.append(0)
            elif mark[1] == 1: # downbar with previous low mark
                output[mark[0]] = 0 # reset previous mark
                mark = len(output), 1
                output.append(0)
            continue
        
    return TopsWrapper(self, output)    