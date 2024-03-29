import numpy as np
import time
import copy
from horse import Horse
from race import Race
from bettor import Bettor

class OrderBook:
    def __init__(self, orderBookType):
        self.orderBookType   = orderBookType # backs or lays
        self.bets      = {}                  # dictionary of list of bets on this orderBook, to be anonymized
        self.anonBets  = {}                  # list of anonymised bets, made public to all bettors (keep as dictionary?)
        self.bestOdds  = None                # best odds offered on the orderBook, including stake
    
    def addBet(self, bet):
        #bet is a dictionary, taken from bettor.bet
        index = bet['HorseName']
        if self.bets.get(index) == None:
            self.bets[index] = [bet]
        else:
            self.bets[index].append(bet)
    
    def queryBet(self, index):
        pass

    def removeBet(self, horseID, bettorID):
        self.bets[horseID] = [bet for bet in self.bets[horseID] if not (bet['BettorID'] == bettorID)]

    def matchBet(self, horseID, bettorIndex, bet, bestOddsIndex, bestOddsBet, bettors):
        bet['Matched'] = True
        bet['Odds'] = bestOddsBet['Odds']
        if bet['BetType'] == 'Back':
            bet['Profit'] = copy.deepcopy(bestOddsBet['Liability'])
        if bet['BetType'] == 'Lay':
            bettors[bettorIndex].balance += bet['Liability'] # add old liability back
            bettors[bettorIndex].balance -= bestOddsBet['Profit'] # take away new liability
            bet['Liability'] = copy.deepcopy(bestOddsBet['Profit'])
        # bettors[bettorIndex].placedBets.append(bet)
        bettors[bettorIndex].matchedBets.append(bet)
        bestOddsBet['Matched'] = True
        bettors[bestOddsIndex].matchedBets.append(bestOddsBet)
        # changed flag of the bet in the bettors placed bet array to True

        self.removeBet(horseID, bestOddsIndex+1)
    
    def anonOrderBook(self):
        self.anonBets = copy.deepcopy(self.bets)
        for i in range(len(self.anonBets)):
            for j in range(len(self.anonBets[i+1])):
                if len(self.anonBets[i+1]) != 0:
                    self.anonBets[i+1][j].pop('BettorID')

    def sortOrderBook(self):
        for i in range(len(self.bets)):
            if len(self.bets[i+1]) != 0:
                if self.bets[i+1][0]['BetType'] == 'Back':  
                    self.bets[i+1].sort(key=lambda x: x['Odds'])
                elif self.bets[i+1][0]['BetType'] == 'Lay':
                    self.bets[i+1].sort(key=lambda x: x['Odds'], reverse=True)

if __name__ == "__main__":
    pass
