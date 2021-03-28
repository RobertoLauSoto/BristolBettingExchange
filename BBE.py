import numpy as np
import time
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
        self.backs = None # LOB offered to back a horse
        self.lays = None # LOB offered to lay a horse
        self.maxStake = 20 # maximum stake allowed on the exchange

    def prepareRace(self):
        self.race = Race(self.raceName, self.raceDistance, self.numHorses) # create race
        self.race.createHorses() # create competitors
        for i in range(self.numBettors): # for each bettor in array
            self.bettors[i] = Bettor(i+1, 500, 'Back/Lay', 0, self.race) # create bettor
            self.bettors[i].runSimulations(100) # run simulations

    def populateLob(self):
        pass

    def runRace(self):
        pass

    def payoutWinners(self):
        pass

if __name__ == "__main__":
    testBBE = BBE('Test', 'Test Race', 2000, 10, 10)
    testBBE.prepareRace()