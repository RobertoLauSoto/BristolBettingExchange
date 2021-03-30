import numpy as np
import time
from horse import Horse
from race import Race
import copy
class Bettor:
    def __init__(self, name, balance, betType, time, race):
        self.id            = name                    # id of bettor
        self.balance       = balance                 # starting balance in bettor's wallet
        self.betType       = betType                 # type of strategy the bettor is taking
        self.birthTime     = time                    # age/time of bettor from init
        self.race          = race                    # Race object bettor is placing bets on
        self.bet           = {}                      # dictionary to represent a bet that the bettor wants to place, will have keys indicating: BettorID, Back/Lay, HorseName (will get deleted as LOB will be indexed by HorseName), Odds, Stake
        self.numSims       = 0                       # number of simulations made by bettor to create starting odds
        self.racePlacings  = [None] * race.numHorses # list of lists to record history of placings of each horse after simulations
        self.raceTimings   = [None] * race.numHorses # list of lists to record finish times of each horse after simulations
        self.racePrefs     = [None] * race.numHorses # list of lists to measure/guess preferences of each horse
        self.horseResults  = [None] * race.numHorses # list of lists of results of each horse after a number of simulations, recording probabilites to win/average position etc.
        self.oddsWeight    = 0
        self.startOdds     = [None] * race.numHorses # list of starting odds calculated by bettors, based on placings/timings/prefs etc.
        self.currentOdds   = [None] * race.numHorses # list of currentOdds calculated by bettors, based on live race
        self.unmatchedBets = []
        self.matchedBets   = []

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
        self.oddsWeight = np.random.uniform(0.5, 0.95)
        print('Bettor {0} Odds weight: {1}'.format(self.id, self.oddsWeight))
        for i in range(len(self.racePlacings)):
            numberWins = 0
            totalPosition = 0
            avgPosition = 0
            for j in range(len(self.racePlacings[i])):
                if self.racePlacings[i][j] == 1:
                    numberWins += 1
                totalPosition += self.racePlacings[i][j]
            probPlacingFirst = (numberWins / self.numSims) * 100
            avgPosition = totalPosition / self.numSims
            probFromAvgPosition = ((1 - (avgPosition / self.race.numHorses)) / ((self.race.numHorses - 1) / 2)) * 100
            finalProb = self.oddsWeight*probPlacingFirst + (1-self.oddsWeight)*probFromAvgPosition
            self.horseResults[i] = [probPlacingFirst, avgPosition, probFromAvgPosition, finalProb, self.oddsWeight]
            # print('Bettor {0} Probability of Horse {1} placing 1st is: {2}'.format(self.id, i+1, self.horseResults[i][0]))
            # print('Bettor {0} Average position of Horse {1}: {2}'.format(self.id, i+1, avgPosition))
            # print('Bettor {0} Average Position Probability of Horse {1}: {2}'.format(self.id, i+1, self.horseResults[i][3]))
            # print('Bettor {0} Final Probability of Horse {1}: {2}'.format(self.id, i+1, finalProb))
            # print('Bettor {0}, Horse {1}: probPlacingFirst = {2}, probAvgPosition = {3}, finalProb = {4}'.format(self.id, i+1, self.horseResults[i][0], self.horseResults[i][2], self.horseResults[i][3]))
            if finalProb != 0:
                decimalOddsToWin = 1 / (finalProb / 100)
            else:
                decimalOddsToWin = 1 / (0.1 / 100)
            self.startOdds[i] = decimalOddsToWin
            # print('Bettor {0} odds for Horse {1}: {2}'.format(self.id, i+1, self.startOdds[i]))
            print('Bettor {0}, Horse {1}: probPlacingFirst = {2}, probAvgPosition = {3}, finalProb = {4}, decimalOddsToWin = {5}'.format(
                        self.id, i+1, round(self.horseResults[i][0], 2), round(self.horseResults[i][2], 2), round(self.horseResults[i][3], 2), round(self.startOdds[i], 2)))

    def startOddsTimings(self):
        pass

    def predictPrefs(self, horses):
        pass

    def runSimulations(self, numSims):
        self.numSims = numSims
        simulation = copy.deepcopy(self.race)
        for i in range(self.numSims):
            simulation.id = 'Simulation {0} by Bettor {1}'.format(i+1, self.id)
            simulation.runRace()
            # for i in range(len(simulation.winner)):
            #     print('Winner {}'.format(simulation.winner[i]))
            # for i in range(len(simulation.top3)):
            #     print('Placed in {0} place {1}'.format(i+1, simulation.top3[i]))
            # for i in range(len(simulation.finalStandings)):
            #     print(simulation.finalStandings[i])
            # simulation.plotRaceGraph(simulationId)
            # print('{} complete'.format(simulation.id))
            self.recordPlacings(simulation.finalStandings)
            self.recordTimings(simulation.finalStandings)
            simulation.reset()
        # print(self.racePlacings)
        # print(self.raceTimings)
        self.startOddsPlacings()

    def placeStartBet(self, horseName, betType):
        # figure out odds and stake given the horse being analysed
        # currently all it does is that it trys to back a horse at slightly longer odds, vice versa for lays
        if betType == 'Back':
            odds = round(self.startOdds[horseName] * np.random.uniform(1.01, 1.1), 2)
            # figure out stake
            # currently always bets 2 pounds
            stake = 2
            profit = round((odds * stake) - stake, 2)
            self.balance -= stake
            bet = {'BettorID': self.id, 'BetType': betType, 'HorseName': horseName+1, 'Odds': odds, 'Stake': stake, 'Profit': profit}
        elif betType == 'Lay':
            odds = round(self.startOdds[horseName] * np.random.uniform(0.9, 0.99), 2)
            stake = 2
            liability = round((odds * stake) - stake, 2)
            bet = {'BettorID': self.id, 'BetType': betType, 'HorseName': horseName+1, 'Odds': odds, 'Stake': stake, 'Liability': liability}
        
        return bet

if __name__ == "__main__":
    testRace = Race("Test Race", 2000, 10)
    testRace.createHorses() # create competitors
    numBettors = 10
    bettors = [None] * numBettors
    for i in range(numBettors):
        bettors[i] = Bettor(i+1, 500, 'Test', 0, testRace)
        bettors[i].runSimulations(100)