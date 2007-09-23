from strategies import strategy_1

definitions = [
    {'symbol': "ES",
    'secType': "FUT",
    'expiry': "200712",
    'exchange': "GLOBEX",
    'currency': "USD",
    'strategy': strategy_1 
    }
]

if __name__ == "__main__":
    
    from java.util.concurrent import LinkedBlockingQueue
    from com.ib.client import EClientSocket
    from wrapper import IBResponseHandler, IBClient, TradingEngine
    from ticker import Ticker
    
    # initialize tickers
    tickers = {}
    id = 0
    for definition in definitions:
        id += 1
        ticker = Ticker(**definition)
        tickers.update({id: ticker})
    
    # start 'engines'
    tick_queue = LinkedBlockingQueue()
    response_handler = IBResponseHandler(tick_queue)
    connection = EClientSocket(response_handler)
    client = IBClient(connection, tickers)
    # initialize trader
    trader = TradingEngine(tick_queue, tickers, client)
    # initialize client
    client.start(trader)

