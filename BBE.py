import numpy as np
import time
import copy
import matplotlib.pyplot as plt
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
        # create bettors
        # select inPlayCheck from random number
        inPlayChecks = [0, 120, 240]
        for i in range(self.numBettors): # for each bettor in array
            inPlayCheck  = np.random.choice(inPlayChecks)
            self.bettors[i] = Bettor(i+1, 10000, 'Back/Lay', 0, self.race, inPlayCheck) # create bettor
            print(inPlayCheck)
            self.bettors[i].runSimulations(100) # run simulations

    def populateLob(self):
        # create two empty LOB objects for the backs and lays and create whole LOB from there
        self.backs = LOB('Backs')
        self.lays  = LOB('Lays')
        
        for horse in range(self.race.numHorses):
            listOfBettors = list(range(1, self.numBettors+1))
            # print('HORSE {}'.format(horse+1))
            for bettor in range(self.numBettors):
                # get best odds currently on LOB, depends on what action is to be taken by the bettor
                # for the backs LOB, bettor wants to get matched with lowest odds available - therefore best odds is the min value on the LOB
                # for the lays LOB, vice versa - best odds is the max value as the bettor would like to make as much money as possible
                if bettor != 0:
                    bestBackOddsBet = min(self.backs.bets[horse+1], key=lambda x: x['Odds'])
                    self.backs.bestOdds = bestBackOddsBet['Odds']
                    bestBackOddsID = bestBackOddsBet['BettorID']
                if bettor != 0:
                    bestLayOddsBet = max(self.lays.bets[horse+1], key=lambda x: x['Odds'])
                    self.lays.bestOdds = bestLayOddsBet['Odds']
                    bestLayOddsID = bestLayOddsBet['BettorID']
                randomBettorId = np.random.choice(listOfBettors)
                listOfBettors.remove(randomBettorId)
                backBet = self.bettors[randomBettorId-1].placeBet(horse, 'Back')
                layBet = self.bettors[randomBettorId-1].placeBet(horse, 'Lay')
                backMatched = False
                layMatched = False
                # check if LOB is empty; if not, see if a bet on there can be matched
                if self.lays.bestOdds != None:
                    # figure out if a lay can be matched
                    if self.lays.bestOdds >= backBet['Odds']:
                        layMatched = True
                        # if randomBettorId == 1 or bestLayOddsID == 1:
                        #     print('layMatched {0}, {1}, {2}'.format(bettor, randomBettorId, bestLayOddsID))
                        #remove best odds from LOB
                        self.lays.matchBet(horse+1, randomBettorId-1, backBet, bestLayOddsID-1, bestLayOddsBet, self.bettors)
                if self.backs.bestOdds != None:
                    #figure out if a back can be matched
                    if self.backs.bestOdds <= layBet['Odds']:
                        backMatched = True
                        # if randomBettorId == 1 or bestBackOddsID == 1:                        
                        #     print('backMatched {0}, {1}, {2}'.format(bettor, randomBettorId, bestBackOddsID))
                        self.backs.matchBet(horse+1, randomBettorId-1, layBet, bestBackOddsID-1, bestBackOddsBet, self.bettors)
                # if the LOB is empty, or if no good odds available on the LOB, place a new bet on the LOB
                if self.backs.bestOdds == None or layMatched != True:
                    # first place back bet
                    self.bettors[randomBettorId-1].placedBets.append(backBet)
                    self.backs.addBet(backBet)
                if self.lays.bestOdds == None or backMatched != True:
                    # then place lay bet
                    self.bettors[randomBettorId-1].placedBets.append(layBet)
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

    def inPlayBetting(self, bettor):
        for horse in range(self.race.numHorses):
            self.bettors[bettor].updateOdds(horse+1, self.race.currStandings)
            bestBackOddsBet = min(self.backs.bets[horse+1], key=lambda x: x['Odds'])
            self.backs.bestOdds = bestBackOddsBet['Odds']
            bestBackOddsID = bestBackOddsBet['BettorID']

            bestLayOddsBet = max(self.lays.bets[horse+1], key=lambda x: x['Odds'])
            self.lays.bestOdds = bestLayOddsBet['Odds']
            bestLayOddsID = bestLayOddsBet['BettorID']

            if bestBackOddsID-1 != bettor:
                pass

            if bestLayOddsID-1 != bettor:
                pass

    def determineCurrentStandings(self):
        self.race.currStandings.sort(key=lambda x: [x.currTime, -x.currDistance]) # sort current standings of horses by time (asc.) and then by distance (dist.) if equal time
        for i in range(len(self.race.currStandings)):
            self.race.currStandings[i].currPosition = i+1 # update position
            # print(self.currStandings[i])

    def runRace(self, inPlay=None):
        if inPlay == True:
            time     = 0 # current race time in 'seconds'
            timestep = 1 # 1 second
            while(self.race.state != 'Finished'): # while race is in running
                time += timestep # race time increases
                self.determineCurrentStandings()
                # do inplay betting stuff
                if len(self.race.currStandings) != 0:
                    for bettor in range(self.numBettors):
                        if self.bettors[bettor].inPlayCheck != 0:
                            if time % self.bettors[bettor].inPlayCheck == 0:
                                #do stuff
                                self.inPlayBetting(bettor)
                self.race.currStandings.clear() # clear array for next iteration
                for i in range(self.race.numHorses): # for each horse
                    self.race.currStandings.append(self.race.horses[i])
                    if self.race.horses[i].state != 'Finished' and self.race.horses[i].state != 'Retired':
                        self.race.horses[i].state = 'Running' # horse is in running
                        self.race.horses[i].currTime = time 
                        self.race.horses[i].prevSpeed = self.race.horses[i].currSpeed # record previous speed
                        self.race.horses[i].currSpeed = self.race.generateForwardStep(self.race.horses[i]) # function to generate forward step at each iteration
                        progress = self.race.horses[i].currSpeed * timestep # progress on this timestep, distance = speed x time
                        self.race.horses[i].currDistance += progress # update current distance of horse along track
                        self.race.horses[i].distanceHistory.append(self.race.horses[i].currDistance)
                        self.race.horseDistances[i] = self.race.horses[i].currDistance
                        if self.race.horses[i].currDistance >= self.race.distance: # horse has crossed finish line
                            self.race.horses[i].state = 'Finished'
                            self.race.horses[i].finishTime = (time - timestep) + ((self.race.distance - self.race.horses[i].distanceHistory[-1]) / self.race.horses[i].currSpeed) # finish time in real seconds
                            self.race.horses[i].currTime = self.race.horses[i].finishTime
                            # print('Test : horse ' + str(i+1) + ' finished')
                            self.race.finalStandings.append(self.race.horses[i])
                        if len(self.race.finalStandings) == self.race.numHorses: # all horses have finished
                            self.race.time = self.race.horses[-1].finishTime
                            self.race.determineFinalPlacings()
                            self.race.state = 'Finished'
                            # self.race.plotRaceGraph()
                            # print(len(self.race.finalStandings))
                            # print(self.race.numHorses)
                            # print(self.race.state)
                            break
                    else:
                        continue
        else:
            self.race.runRace()
            for i in range(len(self.race.finalStandings)):
                    print(self.race.finalStandings[i])
            self.race.plotRaceGraph()
        
    def payoutWinners(self):
        for bettor in range(self.numBettors):
            for betCounter in range(len(self.bettors[bettor].matchedBets)):
                bet = self.bettors[bettor].matchedBets[betCounter]
                if bet['HorseName'] == self.race.winner[0].name:
                    if bet['BetType'] == 'Back':
                        # horse won - successful back
                        # get stake back + profit
                        self.bettors[bettor].balance += bet['Stake'] + bet['Profit']
                    if bet['BetType'] == 'Lay':
                        # horse won - unsuccessful lay
                        # pay liability
                        self.bettors[bettor].balance -= bet['Liability']
                else:
                    if bet['BetType'] == 'Back':
                        # horse lost - unsuccesful back
                        # stake already removed from balance so no update
                        pass
                    if bet['BetType'] == 'Lay':
                        # horse lost - successful lay
                        # receive backer's stake
                        self.bettors[bettor].balance += bet['Stake']
            for betCounter in range(len(self.bettors[bettor].placedBets)):
                bet = self.bettors[bettor].placedBets[betCounter]
                if bet['BetType'] == 'Back' and bet['Matched'] == False:
                    # unmatched back bet - return stake to bettor
                    # print('Unmatched Bet')
                    self.bettors[bettor].balance += bet['Stake']
            self.bettors[bettor].balance = round(self.bettors[bettor].balance, 2)

    def visualiseBets(self):
        fig, ax = plt.subplots() # generate figure with subplots
        for horse in range(self.race.numHorses):
            pass

if __name__ == "__main__":
    testBBE = BBE('Test', 'Test Race - Real Race', 2000, 10, 10)
    testBBE.prepareRace()
    testBBE.populateLob()
    # print(testBBE.unsortedLOB[0].bets[1])
    # print(testBBE.unsortedLOB[1].bets[1])
    # print(testBBE.lob[0].bets[1])
    # print(testBBE.lob[1].bets[1])
    # print(testBBE.lob[0].anonBets[1])
    # print(testBBE.lob[1].anonBets[1])
    # print(testBBE.bettors[0].matchedBets)
    testBBE.runRace(inPlay=True)
    testBBE.payoutWinners()
    for bettor in range(testBBE.numBettors):
        print(testBBE.bettors[bettor].balance)