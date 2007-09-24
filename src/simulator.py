from datetime import datetime, timedelta

def process_fields(fields):    
    month, day, year = fields[0].split("/")
    hour, minute = fields[1].split(":")
    date = datetime(int(year), int(month), int(day), int(hour), int(minute))
    return date, float(fields[2]), float(fields[3]), float(fields[4]), \
                                                        float(fields[5])
                                                        
def parse_line(line):
    if line[-2:] == '\r\n': # always check this first => CPython newline
        line = line[:-2]
    if line[-1:] == '\n': # jython newline
        line = line[:-1]
    fields = line.split(",")
    candle = process_fields(fields)
    return candle

def tick_list(symbol, start, end):
    #TODO: find the right file for symbol, start and end
    f = open('ES_03U.TXT', 'r')
    title_line = f.readline() # skip first line
    ticks = []
    for line in f.readlines():
        candle = parse_line(line)
        date, o, h, l, c = candle
        if date >= end: break
        if date >= start:
            ticks.append((date - timedelta(seconds=57), o))
            ticks.append((date - timedelta(seconds=44), h))
            ticks.append((date - timedelta(seconds=28), l))
            ticks.append((date - timedelta(seconds= 7), c))
    f.close()
    return ticks

if __name__ == '__main__':
    
    from ticker import Ticker
    
    start = datetime(2003, 6, 9)
    end = datetime(2003, 6, 23)
    ticks = tick_list('ES', start, end)
    
    t = Ticker()
    for tick in ticks:
        t.ticks.append(tick)