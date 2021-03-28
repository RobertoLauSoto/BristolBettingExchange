import numpy as np
import time
from horse import Horse
from race import Race
from bettor import Bettor

class LOB:
    def __init__(self, lobType):
        self.lobType   = lobType # backs or lays
        self.bets      = {}      # dictionary of bets on this LOB, to be anonymized
        self.anomBets  = []      # list of anonymised bets, made public to all bettors (keep as dictionary?)
        self.worstOdds = None    # worst odds offered on the LOB, including stake
        self.bestOdds  = None    # best odds offered on the LOB, including stake
    
    def addBet(self, bet):
        #bet is a dictionary, taken from bettor.bet
        index = bet['HorseName']
        del bet['HorseName']
        if self.bets.get(index) == None:
            self.bets[index] = [bet]
        else:
            self.bets[index].append(bet)
    
    def queryBet(self, index):
        pass

    def matchBet(self, index):
        pass

    def removeBet(self, index):
        pass

    def anonLOB(self):
        pass

    def sortLob(self):
        pass

if __name__ == "__main__":
    pass
