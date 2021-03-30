from random import random
import numpy as np
import time
import copy
from horse import Horse
from race import Race
from bettor import Bettor
from lob import LOB
class BBE:
    def __init__(self, name, raceName, raceDistance, numHorses, numBettors):
        self.id = name # name of betting exchange
        self.race = None # Race object that will take place and bets placed on
        self.raceName = raceName
        self.raceDistance = raceDistance
        self.numHorses = numHorses
        self.numBettors = numBettors # number of bettors placing bets on the race
        self.bettors = [None] * numBettors # list of Bettor objects that will populate this betting exchange
        self.lob = [] # LOB of betting exchange, made up of backs and lays LOBs (essentially an array of two LOB objects)
        self.unsortedLOB = []
        self.backs = None # LOB offered to back a horse
        self.lays = None # LOB offered to lay a horse
        self.maxStake = 20 # maximum stake allowed on the exchange

    def prepareRace(self):
        self.race = Race(self.raceName, self.raceDistance, self.numHorses) # create race
        self.race.createHorses() # create competitors
        for i in range(self.numBettors): # for each bettor in array
            self.bettors[i] = Bettor(i+1, 10000, 'Back/Lay', 0, self.race) # create bettor
            self.bettors[i].runSimulations(100) # run simulations

    def populateLob(self):
        # create two empty LOB objects for the backs and lays and create whole LOB from there
        self.backs = LOB('Backs')
        self.lays  = LOB('Lays')
        
        
        for horse in range(self.race.numHorses):
            listOfBettors = list(range(1, self.numBettors+1))
            print('HORSE {}'.format(horse+1))
            for bettor in range(self.numBettors):
                # get best odds currently on LOB, depends on what action is to be taken by the bettor
                # for the backs LOB, bettor wants to get matched with lowest odds available - therefore best odds is the min value on the LOB
                # for the lays LOB, vice versa - best odds is the max value as the bettor would like to make as much money as possible
                if bettor != 0:
                    bestBackOddsBet = min(self.backs.bets[horse+1], key=lambda x: x['Odds'])
                    self.backs.bestOdds = bestBackOddsBet['Odds']
                    bestbackOddsID = bestBackOddsBet['BettorID']
                if bettor != 0:
                    bestLayOddsBet = max(self.lays.bets[horse+1], key=lambda x: x['Odds'])
                    self.lays.bestOdds = bestLayOddsBet['Odds']
                    bestlayOddsID = bestLayOddsBet['BettorID']
                randomBettorId = np.random.choice(listOfBettors)
                listOfBettors.remove(randomBettorId)
                backBet = self.bettors[randomBettorId-1].placeStartBet(horse, 'Back')
                layBet = self.bettors[randomBettorId-1].placeStartBet(horse, 'Lay')
                backMatched = False
                layMatched = False
                # check if LOB is empty; if not, see if a bet on there can be matched
                if self.lays.bestOdds != None:
                    # figure out if a lay can be matched
                    if self.lays.bestOdds >= backBet['Odds']:
                        layMatched = True
                        if randomBettorId == 1 or bestlayOddsID == 1:
                            print('layMatched {0}, {1}, {2}'.format(bettor, randomBettorId, bestlayOddsID))
                        #remove best odds from LOB
                        self.lays.matchBet(horse+1, randomBettorId-1, backBet, bestlayOddsID-1, bestLayOddsBet, self.bettors)
                if self.backs.bestOdds != None:
                    #figure out if a back can be matched
                    if self.backs.bestOdds <= layBet['Odds']:
                        backMatched = True
                        if randomBettorId == 1 or bestbackOddsID == 1:                        
                            print('backMatched {0}, {1}, {2}'.format(bettor, randomBettorId, bestbackOddsID))
                        self.backs.matchBet(horse+1, randomBettorId-1, layBet, bestbackOddsID-1, bestBackOddsBet, self.bettors)
                # if the LOB is empty, or if no good odds available on the LOB, place a new bet on the LOB
                if self.backs.bestOdds == None or layMatched != True:
                    # first place back bet
                    self.backs.addBet(backBet)
                if self.lays.bestOdds == None or backMatched != True:
                    # then place lay bet
                    self.lays.addBet(layBet)            
                if bettor+1 == self.numBettors:
                    #reset best odds
                    bestBackOddsBet = None
                    bestLayOddsBet = None
                    self.backs.bestOdds = None
                    self.lays.bestOdds = None

        self.lob.append(self.backs)
        self.lob.append(self.lays) 
        self.unsortedLOB = copy.deepcopy(self.lob)
        self.lob[0].sortLOB()
        self.lob[1].sortLOB()
        self.lob[0].anonLOB()
        self.lob[1].anonLOB()

    def runRace(self):
        pass

    def payoutWinners(self):
        pass

if __name__ == "__main__":
    testBBE = BBE('Test', 'Test Race', 2000, 10, 10)
    testBBE.prepareRace()
    testBBE.populateLob()
    # print(testBBE.unsortedLOB[0].bets[1])
    # print(testBBE.unsortedLOB[1].bets[1])
    # print(testBBE.lob[0].bets[1])
    # print(testBBE.lob[1].bets[1])
    # print(testBBE.lob[0].anonBets[1])
    # print(testBBE.lob[1].anonBets[1])
    print(testBBE.bettors[0].matchedBets)