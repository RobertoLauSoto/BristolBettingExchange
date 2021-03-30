import numpy as np
import time
import copy
from horse import Horse
from race import Race
from bettor import Bettor

class LOB:
    def __init__(self, lobType):
        self.lobType   = lobType # backs or lays
        self.bets      = {}      # dictionary of bets on this LOB, to be anonymized
        self.anonBets  = {}      # list of anonymised bets, made public to all bettors (keep as dictionary?)
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

    def removeBet(self, horseID, bettorID):
        self.bets[horseID] = [i for i in self.bets[horseID] if not (i['BettorID'] == bettorID)]

    def matchBet(self, horseID, bettorID, backBet, bestOddsID, bestOddsBet, bettors):
        bettors[bettorID].matchedBets.append(backBet)
        bestOddsBet['HorseName'] = horseID
        bettors[bestOddsID].matchedBets.append(bestOddsBet)
        self.removeBet(horseID, bestOddsID+1)
    
    def anonLOB(self):
        self.anonBets = copy.deepcopy(self.bets)
        for i in range(len(self.anonBets)):
            for j in range(len(self.anonBets[i+1])):
                self.anonBets[i+1][j].pop('BettorID')

    def sortLOB(self):
        for i in range(len(self.bets)):
            if self.bets[i+1][0]['BetType'] == 'Back':  
                self.bets[i+1].sort(key=lambda x: x['Odds'])
            elif self.bets[i+1][0]['BetType'] == 'Lay':
                self.bets[i+1].sort(key=lambda x: x['Odds'], reverse=True)


if __name__ == "__main__":
    pass
