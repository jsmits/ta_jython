from datetime import datetime, timedelta
import time

from java.lang import Runnable, Thread
from com.ib.client import EWrapper, Contract, Order

class IBResponseHandler(EWrapper):
    """Custom wrapper implementation"""
    def __init__(self, tick_queue): 
        self.ticks = tick_queue
        self.account = {'_orders': {}, '_portfolio': {}}
        self.event_handlers = {} # for historical data callback
        self.temp_hist_data = {} # temporary holder for historical data
        
    def nextValidId(self, orderId):
        """This method is only called upon connection."""
        self.account['_nextvalidid'] = orderId

    def tickPrice(self, tickerId, field, price, canAutoExecute):
        time = datetime.now()
        if field == 4:
            self.ticks.put((tickerId, time, price))
    
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, 
        permId, parentId, lastFillPrice, clientId): 
        time = datetime.now()
        order_entry = self.account['_orders'][orderId]
        order_entry['status'] = status
        order_entry['time'] = time
        if filled and avgFillPrice:
            order_entry['fill_value'] = avgFillPrice
    
    def openOrder(self, orderId, contract, order):
        print "open order", orderId, contract, order
    
    def updateAccountValue(self, key, value, currency, accountName):
        try:
            value = float(value)
        except ValueError:
            pass
        if currency:
            d = self.account.get(key, {})
            d[currency] = value
            self.account[key] = d
        else:
            self.account[key] = value
            
    def updatePortfolio(self, contract, position, marketPrice, marketValue, 
        averageCost, unrealizedPNL, realizedPNL, accountName): 
        key = contract.m_symbol
        if contract.m_expiry:
            key += "_%s" % contract.m_expiry
        self.account['_portfolio'][key] = {'contract'     : contract,
                                           'position'     : position,
                                           'marketPrice'  : marketPrice,
                                           'marketValue'  : marketValue,
                                           'averageCost'  : averageCost,
                                           'unrealizedPNL': unrealizedPNL,
                                           'realizedPNL'  : realizedPNL,
                                           'accountName'  : accountName}
    
    def historicalData(self, reqId, date, open, high, low, close, volume, 
                       count, WAP, hasGaps): 
        holder = self.temp_hist_data.get(reqId)
        if not holder: 
            self.temp_hist_data[reqId] = holder = []
        holder.append((date, open, high, low, close, volume))
        if date.startswith("finished"): 
            # call historical data callback here with reqId (=ticker_id) and/or 
            # data
            handler = self.event_handlers.get('historical_data_handler')
            if handler: 
                handler(reqId, self.temp_hist_data[reqId])
                del self.temp_hist_data[reqId]
            else:
                print "error :: historical data requested without handler"
                    
    def tickSize(self, tickerId, field, size): pass
    def tickOptionComputation(self, tickerId, field, impliedVol, delta, 
        modelPrice, pvDividend): 
        pass
    def updateAccountTime(self, timeStamp): pass
    def contractDetails(self, contractDetails): pass
    def bondContractDetails(self, contractDetails): pass
    def execDetails(self, orderId, contract, execution): pass
    def updateMktDepth(self, tickerId, position, operation, side, price, size): 
        pass
    def updateMktDepthL2(self, tickerId, position, marketMaker, operation, 
        side, price, vsize): 
        pass
    def updateNewsBulletin(self,msgId, msgType, message, origExchange): pass
    def managedAccounts(self,accountsList): pass
    def receiveFA(self, faDataType, xml): pass
    def scannerParameters(self, xml): pass
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, 
        projection): 
        pass
    def tickGeneric(self, tickerId, tickType, value): pass
    def tickString(self, tickerId, tickType, value): pass

    def error(self, *args):
        if args and len(args) == 3: 
            args = list(args)
            args.insert(0, datetime.now())
            print "%s, error :: id: %s, code: %s, message: %s" % tuple(args)
        elif args and len(args) == 1:
            print "%s, exception :: %s" % (datetime.now(), args)
        elif args:
            print args
        else:
            print "%s, error method called without arguments" % str(datetime.now())

    def connectionClosed(self): 
        print "Connection closed: %s." % str(datetime.now())
        
class TradingEngine(Runnable):
    """Consume the tick queue and process the tick"""
    def __init__(self, tick_queue, tickers, order_engine):
        self.ticks = tick_queue
        self.tickers = tickers
        self.order_engine = order_engine
        
    def run(self):
        print "Trading engine started: %s." % str(datetime.now())
        print "Queue size: %s." % self.ticks.size()
        while True:
            tick = self.ticks.take()
            self.__process_tick(tick)
    
    def __process_tick(self, tick):
        id = tick[0]
        ticker = self.tickers.get(id)
        ticker.ticks.append(tick[1:3]) # only time and value
        
        strategy = ticker.strategy
        if not strategy: return
        position = self.order_engine.has_position(ticker)
        last_order = self.order_engine.last_order(id)
        signal = None
        if not strategy.inside_trading_time(tick[1]):
            # PM determine if pending request -> cancel
            if position < 0: signal = 'exit_short_TIME_EXIT'
            elif position > 0: signal = 'exit_long_TIME_EXIT'
        else:
            if not position:
                if not last_order or not 'Submit' in last_order['status']:
                    signal = strategy.check_entry(ticker)
            else:
                if last_order and last_order['status'] == 'Filled':
                    if position < 0: exit = 'short'
                    elif position > 0: exit = 'long'
                    signal = strategy.check_exit(ticker, last_order['time'], 
                        last_order['fill_value'], exit)
                if not last_order:
                    if position < 0: signal = 'exit_short_SAFETY'
                    elif position > 0: signal = 'exit_long_SAFETY'
        # PM check if there is a pending request -> do nothing or cancel pending
        self.order_engine.handle_signal(tick, signal)

class SimConnection(object):
    """Instance of this class can be used for a simulation"""
    def __init__(self, handler):
        self.handler = handler
        self.account = self.handler.account
        self.account['_nextvalidid'] = 1
        self.simulation = True

    # override the used EClientSocket's methods
    def placeOrder(self, order_id, contract, order):
        """Simulate an immediate fill against the trigger value"""
        order_entry = self.account['_orders'][order_id]
        trigger_value = order_entry['trigger_value']
        self.handler.orderStatus(order_id, 'Filled', order.m_totalQuantity, 0, 
            trigger_value, 0, 0, trigger_value, 0)
        # now determine the protfolion position after the order
        signal = order_entry['signal']
        if signal.startswith('entry_long'): position = order.m_totalQuantity
        if signal.startswith('entry_short'): position = -order.m_totalQuantity
        if signal.startswith('exit'): position = 0
        self.handler.updatePortfolio(contract, position, 
            trigger_value, trigger_value, 0.0, 0.0, 0.0, "")
    
    def cancelOrder(self, order_id):
        order_entry = self.account['_orders'][order_id]
        order_entry['status'] = 'Cancelled'
    
    def eConnect(self, *args, **kwargs): pass
    def eDisconnect(self): pass
    def reqAccountUpdates(self, *args, **kwargs): pass
    def reqOpenOrders(self): pass
    
    def wrapper(self):
        return self.handler
            
class IBClient(object):
    """Handle the orders"""
    def __init__(self, connection, tickers, client_id=0):
        self.connection = connection
        self.tickers = tickers
        self.handler = self.connection.wrapper()
        self.account = self.handler.account
        self.order_map = {} # maps ticker ids with order ids
        self.client_id = client_id
        self.trading = False
        
    def start(self, trader, *args, **kwargs):
        # check if it is a simualtion connection
        simulation = getattr(self.connection, 'simulation', False)
        if simulation:
            return self.simulate(trader, args, kwargs)
        # initialize the tick feed
        # and request the account, order, and portfolio updates
        self.register_handlers()
        self.connect(client_id=self.client_id)
        self.connection.reqAccountUpdates(True, "")
        self.connection.reqOpenOrders()
        
        # get historical data
        self.requested_ticks = []
        for id, ticker in self.tickers.items():
            self.historical_data(id, ticker)
            self.requested_ticks.append(id)
        while self.requested_ticks:
            # requested ticks is consumed by historical data response
            time.sleep(1)
            
        # now start the trader
        Thread(trader).start()
        # clearing tick queue without trading
        ts = self.handler.ticks.size()
        print "Pausing 5 seconds to clear the tick queue, size: %s." % ts
        time.sleep(5)
        ts = self.handler.ticks.size()
        print "Queue 'hopefully' cleared, size: %s." % ts
        self.trading = True # now enable trading
        
    def simulate(self, trader, start=None, end=None):
        # fill the ticks with historical data
        Thread(trader).start()
        self.trading = True
        # fill the queue throught the handler
        # load the data and fill the queue, that should be it
        # self.handler.ticks.put((tickerId, time, price))
    
    def connect(self, host="127.0.0.1", port=7496, client_id=0):
        print "Connecting client..."
        self.connection.eConnect(host, port, client_id)
        
    def disconnect(self):
        print "Disconnecting client..."
        self.connection.eDisconnect()
        
    def __next_id(self):
        id = self.account['_nextvalidid']
        self.account['_nextvalidid'] = id + 1 # update to next order id
        return id
    
    def register_handlers(self):
        self.handler.event_handlers['historical_data_handler'] = \
            self.historical_data_handler
    
    def has_position(self, ticker):
        for key in self.account['_portfolio'].keys():
            if key == ticker.symbol or key.startswith("%s_" % ticker.symbol):
                position = self.account['_portfolio'][key]['position']
                return position
            
    def last_order(self, ticker_id):
        order_ids = self.order_map.get(ticker_id)
        if order_ids:
            last_order_id = order_ids[-1]
            order_entry = self.account['_orders'][last_order_id]
            return order_entry
    
    def __create_contract(self, ticker):
        contract = Contract()
        contract.m_symbol = ticker.symbol
        contract.m_secType = ticker.secType
        contract.m_expiry = getattr(ticker, 'expiry', None)
        contract.m_exchange = ticker.exchange
        contract.m_currency = ticker.currency
        return contract
    
    def __create_order(self, order_id, ticker, action):
        # action can be 'BUY', 'SELL' for futures
        order = Order()
        order.m_orderId = order_id
        order.m_clientId = self.client_id
        order.m_action = action
        order.m_totalQuantity = getattr(ticker, 'quantity', 1)
        order.m_orderType = 'MKT' # guaranteed execution
        order.m_lmtPrice = 0
        order.m_auxPrice = 0
        return order
    
    def handle_signal(self, trigger_tick, signal):
        if not signal: return
        # this is for futures
        if   signal.startswith('entry_long'):  action = 'BUY'
        elif signal.startswith('exit_long'):   action = 'SELL'
        elif signal.startswith('entry_short'): action = 'SELL'
        elif signal.startswith('exit_short'):  action = 'BUY'
        else:
            print "error :: unknown signal: %s." % signal
            return
        if self.trading:
            self.place_order(trigger_tick, signal, action)
        
    def place_order(self, trigger_tick, signal, action):
        ticker_id = trigger_tick[0]
        ticker = self.tickers.get(ticker_id)
        trigger_time = trigger_tick[1]
        trigger_value = trigger_tick[2]
        order_id = self.__next_id()
        contract = self.__create_contract(ticker)
        order = self.__create_order(order_id, ticker, action)
        order_entry = {'trigger_time': trigger_time,
                       'trigger_value': trigger_value,
                       'signal': signal,
                       'order': order,
                       'status': 'PendingSubmit'}
        self.account['_orders'][order_id] = order_entry
        orders = self.order_map.get(ticker_id, [])
        orders.append(order_id)
        self.order_map[ticker_id] = orders
        self.connection.placeOrder(order_id, contract, order)
        order_entry.update({'order_time': datetime.now()})
        
    def cancel_order(self, order_id):
        order_entry = self.account['_orders'][order_id]
        order_entry['status'] = 'PendingCancel'
        order_entry['time'] = datetime.now()
        self.connection.cancelOrder(order_id)
        
    def historical_data(self, ticker_id, ticker, duration="2 D", 
                        bar_size="1 min"):
        contract = self.__create_contract(ticker)
        now = datetime.now()
        enddate = now + timedelta(hours=1)
        enddatestr = enddate.strftime("%Y%m%d %H:%M:%S")
        self.connection.reqHistoricalData(ticker_id, contract, enddatestr, 
            duration, bar_size, "TRADES", 0, 2)

    def historical_data_handler(self, id, candles):
        print "Processing historical ticks for ticker %s." % id
        ticker = self.tickers.get(id)
        contract = self.__create_contract(ticker)
        self.connection.reqMktData(id, contract, None)
        for candle in candles:
            try:
                date_int = int(candle[0])
            except ValueError:
                continue
            else:
                localtime = time.localtime(date_int)
                date = datetime(*localtime[:-3])
                o, h, l, c = candle[1:5]
                if date.second == 0:
                    ticker.ticks.append((date - timedelta(seconds=57), o))
                    ticker.ticks.append((date - timedelta(seconds=44), h))
                    ticker.ticks.append((date - timedelta(seconds=28), l))
                    ticker.ticks.append((date - timedelta(seconds= 7), c))
                else:
                    base_date = datetime(date.year, date.month, date.day, 
                                         date.hour, date.minute)
                    delta = timedelta(seconds=date.second/5.0)
                    for i in range(1,5):
                        base_date += delta
                        ticker.ticks.append((base_date, candle[i]))
        self.requested_ticks.remove(id)


    