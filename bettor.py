import numpy as np
import time
from horse import Horse
from race import Race
import copy
class Bettor:
    def __init__(self, name, balance, betType, time, race, inPlayCheck):
        self.id               = name                    # id of bettor
        self.balance          = balance                 # starting balance in bettor's wallet
        self.betType          = betType                 # type of strategy the bettor is taking
        self.birthTime        = time                    # age/time of bettor from init
        self.race             = race                    # Race object bettor is placing bets on
        self.inPlayCheck      = inPlayCheck             # int representing how often a bettor updates their odds to decide in-play bets - 0 implies no in-play bets, 1 means every timestep, 10 every 10 timesteps etc.
        self.bet              = {}                      # dictionary to represent a bet that the bettor wants to place, will have keys indicating: BettorID, Back/Lay, HorseName, Odds, Stake
        self.numSims          = 0                       # number of simulations made by bettor to create starting odds
        self.racePlacings     = [None] * race.numHorses # list of lists to record history of placings of each horse after simulations
        self.raceTimings      = [None] * race.numHorses # list of lists to record finish times of each horse after simulations
        self.racePrefs        = [None] * race.numHorses # list of lists to measure/guess preferences of each horse
        self.horseResults     = [None] * race.numHorses # list of dicts of results of each horse after a number of simulations, recording probabilites to win/average position etc.
        self.oddsWeight       = 0                       # float representing the weight used to determine weighted average between horse probabilities, e.g. probability from the number of wins, from average finish position etc.
        self.startOdds        = [None] * race.numHorses # list of starting odds calculated by bettor, based on placings/timings/prefs etc.
        self.projStandings    = [None] * race.numHorses # projected final standings calculated by bettor based on their simulations, used to compare to live standings to decide in play bets
        self.currentOdds      = []                      # list of current odds calculated by bettor, based on live race
        self.placedBets       = []                      # list of all bets placed by the bettor, matched or unmatched
        self.matchedBets      = []                      # list of matched bets only, to calculate winnings/losses at the end of the race
        self.oddsHistory      = []                      # array of odds that update during the race
        self.numChecksDone    = 0                       # number of observations taken by the bettor of the race
        self.unmatchedBacks   = 0                       # number of unmatched backs for a bettor after a session of BBE
        self.updateOddsWeight = 0                       # weight used in updateOdds function
        self.oddsWeightChosen = False                   # boolean flag to check if updateOddsWeight has been assigned

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
        # print('Bettor {0} Odds weight: {1}'.format(self.id, self.oddsWeight))
        for i in range(len(self.racePlacings)):
            horseName = i+1
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
            self.horseResults[i] = {'probPlacingFirst': round(probPlacingFirst, 2), 'avgPosition': round(avgPosition, 2), 'probAvgPosition': round(probFromAvgPosition, 2),
                                    'finalProb': round(finalProb, 2), 'oddsWeight': round(self.oddsWeight, 2), 'HorseName': horseName}
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
            # self.oddsHistory[horseName].append(round(decimalOddsToWin, 2))
            self.horseResults[i]['startOdds'] = round(decimalOddsToWin, 2)
            # print('Bettor {0} odds for Horse {1}: {2}'.format(self.id, i+1, round(self.startOdds[i], 2)))
            # print('Bettor {0}, Horse {1}: probPlacingFirst = {2}, probAvgPosition = {3}, finalProb = {4}, startOdds = {5}'.format(
                        # self.id, horseName, self.horseResults[i]['probPlacingFirst'], self.horseResults[i]['probAvgPosition'], self.horseResults[i]['finalProb'], self.horseResults[i]['startOdds']))
        self.oddsHistory.append(self.startOdds)
    
    def projectFinalStandings(self):
        self.projStandings = copy.deepcopy(self.horseResults)
        self.projStandings.sort(key=lambda x: x['finalProb'], reverse=True)
        # for i in range(len(self.projStandings)):
        #     print(self.projStandings[i])

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
        self.projectFinalStandings()

    def placeBet(self, horseIndex, betType):
        # figure out odds and stake given the horse being analysed
        # currently all it does is that it trys to back a horse at slightly longer odds, vice versa for lays
        if betType == 'Back':
            odds = round(self.startOdds[horseIndex] * np.random.uniform(1.01, 1.1), 2)
            # figure out stake
            # currently always bets 2 pounds
            stake = 2
            profit = round((odds * stake) - stake, 2)
            self.balance -= stake
            bet = {'BettorID': self.id, 'BetType': betType, 'HorseName': horseIndex+1, 'Odds': odds, 'Stake': stake, 'Profit': profit, 'Matched': False}
        elif betType == 'Lay':
            odds = round(self.startOdds[horseIndex] * np.random.uniform(0.9, 0.99), 2)
            stake = 2
            liability = round((odds * stake) - stake, 2)
            self.balance -= liability
            bet = {'BettorID': self.id, 'BetType': betType, 'HorseName': horseIndex+1, 'Odds': odds, 'Stake': stake, 'Liability': liability, 'Matched': False}
        
        return bet

    def placeInPlayBet(self, horseIndex, betType, time):
        if betType == 'Back':
            odds = round(self.currentOdds[horseIndex] * np.random.uniform(1.01, 1.1), 2)
            stake = 2
            profit = round((odds * stake) - stake, 2)
            self.balance -= stake
            bet = {'BettorID': self.id, 'BetType': betType, 'HorseName': horseIndex+1, 'Odds': odds, 'Stake': stake, 'Profit': profit, 'Matched': False, 'Time': time}
        elif betType == 'Lay':
            odds = round(self.currentOdds[horseIndex] * np.random.uniform(0.9, 0.99), 2)
            stake = 2
            liability = round((odds * stake) - stake, 2)
            self.balance -= liability
            bet = {'BettorID': self.id, 'BetType': betType, 'HorseName': horseIndex+1, 'Odds': odds, 'Stake': stake, 'Liability': liability, 'Matched': False, 'Time': time}
        
        return bet

    def updateLeaderOdds(self, currentStandings, time, currentLeaderID, projWinnerID):
        # bettor will compare their own projected final standings against the race's current standings and decide if it wants to place an in-play bet
        # could also use responsiveness / current speed / ground lost etc. to determine how it wants to update odds
        # how often it does this is determined by the bettor's inPlayCheck attribute - some may check at every timestep, others will check less regularly or not at all
        # need to be careful not to let it bet with itself
        updateBets = False
        oddsArray = copy.deepcopy(self.oddsHistory[self.numChecksDone])
        self.numChecksDone += 1

        if currentStandings[0].name != self.projStandings[0]['HorseName']:
            updateBets = True
            oddsWeight = np.random.uniform(0.9, 1.0)
            probFromCurrentPositionCurrentLeader = ((1 - (currentStandings[0].currPosition / self.race.numHorses)) / ((self.race.numHorses - 1) / 2)) * 100
            newFinalProbCurrentLeader = oddsWeight * probFromCurrentPositionCurrentLeader + (1-oddsWeight) * oddsArray[currentLeaderID-1]
            currentLeaderOdds = 1 / (newFinalProbCurrentLeader / 100)
            oddsArray[currentLeaderID-1] = currentLeaderOdds
            # get current position of projected winner
            for i in range(len(currentStandings)):
                if currentStandings[i].name == projWinnerID:
                    projWinnerCurrentPosition = currentStandings[i].currPosition
            probFromCurrentPositionProjectedWinner = ((1 - (projWinnerCurrentPosition / self.race.numHorses)) / ((self.race.numHorses - 1) / 2)) * 100
            newFinalProbProjWinner = oddsWeight * probFromCurrentPositionProjectedWinner + (1-oddsWeight) * oddsArray[projWinnerID-1]
            projWinnerNewOdds = 1 / (newFinalProbProjWinner / 100)
            oddsArray[projWinnerID-1] = projWinnerNewOdds
            # print('I should update odds - Horse {0} winning, Horse {1} projected, Time checked was {2}'.format(currentStandings[0].name, self.projStandings[0]['HorseName'], time))
        
        self.currentOdds = copy.deepcopy(oddsArray)
        self.oddsHistory.append(oddsArray)    
            
        return updateBets
    
    def calcOddsWeight(self, currentStandings, time):
        # this should determine an odds weight depending on how much of the race is left
        percentDistCovered = currentStandings[0].currDistance / self.race.distance
        self.updateOddsWeight = percentDistCovered 

    def calcProbFromCurrentDistance(self, horseCurrentPostion, horseCurrentDistance, invTotalDistancesLeft):
        positionWeight = self.race.numHorses + 1 - horseCurrentPostion
        probability = ((positionWeight * (1 / (self.race.distance - horseCurrentDistance))) / invTotalDistancesLeft) * 100
        
        return probability

    def updateAllOdds(self, currentStandings, time):
        oddsArray = copy.deepcopy(self.oddsHistory[self.numChecksDone])
        self.numChecksDone += 1
        self.calcOddsWeight(currentStandings, time)
        for horseIndex in range(len(currentStandings)):
            # get horse's current position
            invTotalDistancesLeft = 0
            for i in range(len(currentStandings)):
                invTotalDistancesLeft += (1 / (self.race.distance - currentStandings[i].currDistance))
                if currentStandings[i].name == horseIndex+1:
                    horseCurrentPosition = currentStandings[i].currPosition
                    horseCurrentDistance = currentStandings[i].currDistance
                    
            prevProb = 100 / oddsArray[horseIndex]
            probFromCurrentPosition = ((1 - (horseCurrentPosition / self.race.numHorses)) / ((self.race.numHorses - 1) / 2)) * 100
            probFromCurrentDistance = self.calcProbFromCurrentDistance(horseCurrentPosition, horseCurrentDistance, invTotalDistancesLeft)
            newFinalProb = self.updateOddsWeight * probFromCurrentDistance + (
                            (1 - self.updateOddsWeight) / 2) * prevProb + (
                            (1 - self.updateOddsWeight) / 2) * (100 / self.startOdds[horseIndex])
            if newFinalProb == 0:
                newFinalProb = 0.1
            newOdds = 1 / (newFinalProb / 100)
            # limit odds to fall within 1.01 or 1000
            if newOdds < 1.01:
                newOdds = 1.01
            elif newOdds > 1000:
                newOdds = 1000
            oddsArray[horseIndex] = newOdds
        
        self.currentOdds = copy.deepcopy(oddsArray)
        self.oddsHistory.append(oddsArray)
            
if __name__ == "__main__":
    testRace = Race("Test Race", 2000, 10)
    testRace.createHorses() # create competitors
    numBettors = 10
    bettors = [None] * numBettors
    for i in range(numBettors):
        bettors[i] = Bettor(i+1, 500, 'Test', 0, testRace)
        bettors[i].runSimulations(100)