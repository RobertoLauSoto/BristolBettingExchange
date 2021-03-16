import numpy as np
import time
from horse import Horse
from race import Race

class Bettor:
    def __init__(self, name, balance, betType, time, race):
        self.id           = name                    # id of bettor
        self.balance      = balance                 # starting balance in bettor's wallet
        self.betType      = betType                 # type of strategy the bettor is taking
        self.birthTime    = time                    # age/time of bettor from init
        self.race         = race                    # Race object bettor is placing bets on
        self.numSims      = 0                       # number of simulations made by bettor to create starting odds
        self.racePlacings = [None] * race.numHorses # list of lists to record history of placings of each horse after simulations
        self.raceTimings  = [None] * race.numHorses # list of lists to record finish times of each horse after simulations
        self.racePrefs    = [None] * race.numHorses # list of lists to measure/guess preferences of each horse
        self.startOdds    = [None] * race.numHorses # list of starting odds calculated by bettors, based on placings/timings/prefs etc.

    def __str__(self) -> str:
        pass

    def recordPlacings(self, standings):
        standings.sort(key=lambda x: x.name)
        for i in range(len(standings)):
            horsePlacing = []
            horsePlacing.append(standings[i].currPosition)
            if self.racePlacings[i] == None:
                self.racePlacings[i] = horsePlacing
            else:
                self.racePlacings[i].append(standings[i].currPosition)

    def recordTimings(self, standings):
        standings.sort(key=lambda x: x.name)
        for i in range(len(standings)):
            horseTiming = []
            horseTiming.append(round(standings[i].currTime, 5))
            if self.raceTimings[i] == None:
                self.raceTimings[i] = horseTiming
            else:
                self.raceTimings[i].append(round(standings[i].currTime, 5))

    def startOddsPlacings(self):
        pass

    def startOddsTimings(self):
        pass

    def predictPrefs(self, horses):
        pass

    def runSimulations(self, numSims):
        self.numSims = numSims
        simulation = self.race
        for i in range(self.numSims):
            simulation.id = 'Simulation {0} by Bettor {1}'.format(i+1, self.id)
            simulation.runRace()
            # for i in range(len(simulation.winner)):
            #     print('Winner {}'.format(simulation.winner[i]))
            # for i in range(len(simulation.top3)):
            #     print('Placed in {0} place {1}'.format(i+1, simulation.top3[i]))
            for i in range(len(simulation.finalStandings)):
                print(simulation.finalStandings[i])
            # simulation.plotRaceGraph()
            print('{} complete'.format(simulation.id))
            self.recordPlacings(simulation.finalStandings)
            self.recordTimings(simulation.finalStandings)
            simulation.reset()
        print(self.racePlacings)
        print(self.raceTimings)

if __name__ == "__main__":
    testRace = Race("Test Race", 2000, 10)
    testRace.createHorses() # create competitors
    numBettors = 10
    bettors = [None] * numBettors
    for i in range(numBettors):
        bettors[i] = Bettor(i+1, 500, 'Test', 0, testRace)
        bettors[i].runSimulations(2)
    
