from java.lang import Runnable, Thread
from math import sqrt

class MyRunnable(Runnable):
    
    def __init__(self):
        self.count = 1
    
    def run(self):
        while True:
            self.count += 1
            sqrt(self.count)
            
            
if __name__ == '__main__':
    
    r1 = MyRunnable()
    r2 = MyRunnable()
    Thread(r1).start()
    Thread(r2).start()