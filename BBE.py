import numpy as np
import time
import copy
import matplotlib.pyplot as plt
from horse import Horse
from race import Race
from bettor import Bettor
from lob import LOB
import sys
class BBE:
    def __init__(self, name, raceName, raceDistance, numHorses, numBettors):
        self.id           = name # name of betting exchange
        self.race         = None # Race object that will take place and bets placed on
        self.raceName     = raceName
        self.raceDistance = raceDistance
        self.numHorses    = numHorses
        self.numBettors   = numBettors # number of bettors placing bets on the race
        self.bettors      = [None] * numBettors # list of Bettor objects that will populate this betting exchange
        self.lob          = [] # LOB of betting exchange, made up of backs and lays LOBs (essentially an array of two LOB objects)
        self.unsortedLOB  = []
        self.backs        = None # LOB offered to back a horse
        self.lays         = None # LOB offered to lay a horse
        self.maxStake     = 20 # maximum stake allowed on the exchange

    def prepareRace(self):
        self.race = Race(self.raceName, self.raceDistance, self.numHorses) # create race
        self.race.createHorses() # create competitors
        # create bettors
        # select inPlayCheck from random number
        inPlayChecks = [10, 30, 60, 120, 240] # 11/4/2021: 1 bettor for each type of update
        for i in range(self.numBettors): # for each bettor in array
            # inPlayCheck  = np.random.choice(inPlayChecks)
            inPlayCheck = inPlayChecks[0]
            inPlayChecks.remove(inPlayCheck)
            self.bettors[i] = Bettor(i+1, 10000, 'Back/Lay', 0, self.race, inPlayCheck) # create bettor
            print('Bettor {0} inPlayCheck = {1}'.format(i+1, inPlayCheck))
            self.bettors[i].runSimulations(10) # run simulations

    def populateLOB(self):
        # create two empty LOB objects for the backs and lays and create whole LOB from there
        self.backs = LOB('Backs')
        self.lays  = LOB('Lays')
        
        for horse in range(self.race.numHorses):
            listOfBettors = list(range(1, self.numBettors+1))
            bestBackOddsBet     = None
            bestLayOddsBet      = None
            self.backs.bestOdds = None
            self.lays.bestOdds  = None
            # print('HORSE {}'.format(horse+1))
            for bettorIndex in range(self.numBettors):
                # get best odds currently on LOB, depends on what action is to be taken by the bettor
                # for the backs LOB, bettor wants to get matched with lowest odds available - therefore best odds is the min value on the LOB
                # for the lays LOB, vice versa - best odds is the max value as the bettor would like to make as much money as possible
                if bettorIndex != 0:
                    bestBackOddsBet = min(self.backs.bets[horse+1], key=lambda x: x['Odds'])
                    self.backs.bestOdds = bestBackOddsBet['Odds']
                    bestBackOddsID      = bestBackOddsBet['BettorID']
                if bettorIndex != 0:
                    bestLayOddsBet = max(self.lays.bets[horse+1], key=lambda x: x['Odds'])
                    self.lays.bestOdds = bestLayOddsBet['Odds']
                    bestLayOddsID      = bestLayOddsBet['BettorID']

                randomBettorId = np.random.choice(listOfBettors)
                listOfBettors.remove(randomBettorId)

                backBet = self.bettors[randomBettorId-1].placeBet(horse, 'Back')
                layBet  = self.bettors[randomBettorId-1].placeBet(horse, 'Lay')

                backMatched = False
                layMatched  = False
                # check if LOB is empty; if not, see if a bet on there can be matched
                if self.lays.bestOdds != None:
                    # figure out if a lay can be matched
                    if self.lays.bestOdds >= backBet['Odds']:
                        layMatched = True
                        # if randomBettorId == 1 or bestLayOddsID == 1:
                        #     print('layMatched {0}, {1}, {2}'.format(bettorIndex, randomBettorId, bestLayOddsID))
                        #remove best odds from LOB
                        self.lays.matchBet(horse+1, randomBettorId-1, backBet, bestLayOddsID-1, bestLayOddsBet, self.bettors)
                if self.backs.bestOdds != None:
                    #figure out if a back can be matched
                    if self.backs.bestOdds <= layBet['Odds']:
                        backMatched = True
                        # if randomBettorId == 1 or bestBackOddsID == 1:                        
                        #     print('backMatched {0}, {1}, {2}'.format(bettorIndex, randomBettorId, bestBackOddsID))
                        self.backs.matchBet(horse+1, randomBettorId-1, layBet, bestBackOddsID-1, bestBackOddsBet, self.bettors)
                # if the LOB is empty, or if no good odds available on the LOB, place a new bet on the LOB
                if self.backs.bestOdds == None or layMatched == False:
                    # first place back bet
                    self.backs.addBet(backBet)
                    self.bettors[randomBettorId-1].placedBets.append(backBet)
                    
                if self.lays.bestOdds == None or backMatched == False:
                    # then place lay bet
                    self.lays.addBet(layBet)  
                    self.bettors[randomBettorId-1].placedBets.append(layBet)                            

        self.lob.append(self.backs)
        self.lob.append(self.lays) 
        self.unsortedLOB = copy.deepcopy(self.lob)
        self.lob[0].sortLOB()
        self.lob[1].sortLOB()
        # self.lob[0].anonLOB()
        # self.lob[1].anonLOB()

    def inPlayBetting(self, bettorIndex, time):
        currentLeaderID = self.race.currStandings[0].name
        projWinnerID = self.bettors[bettorIndex].projStandings[0]['HorseName']
        horseIDs = [currentLeaderID, projWinnerID]
        # make bettor choose odds weight
        # if self.bettors[bettorIndex].oddsWeightChosen == False:
            # self.bettors[bettorIndex].chooseOddsWeight(time)
        # updateBets = self.bettors[bettorIndex].updateLeaderOdds(self.race.currStandings, time, currentLeaderID, projWinnerID)
        self.bettors[bettorIndex].updateAllOdds(self.race.currStandings, time)
        for horse in range(len(horseIDs)):
            horseID = horseIDs[horse]
            if self.race.horses[horseID-1].state != 'Finished': # to prevent bets trading when the horses in question have already finished
                # bettor can only have one open bet on the LOB at a time, so remove open bet if present
                # first deal with back
                # print('Horse {0} is still running, current state = {1}, time={2}'.format(horseID, self.race.horses[horseID-1].state, time))
                self.lob[0].removeBet(horseID, bettorIndex+1)
                self.lob[1].removeBet(horseID, bettorIndex+1)

                backBet = self.bettors[bettorIndex].placeInPlayBet(horseID-1, 'Back', time) # back bet the bettor wants to either match or add onto LOB
                layBet  = self.bettors[bettorIndex].placeInPlayBet(horseID-1, 'Lay', time) # lay bet the bettor wants to either match or add onto LOB

                if len(self.lob[1].bets[horseID]) != 0:
                    bestLayOddsBet = max(self.lob[1].bets[horseID], key=lambda x: x['Odds'])                    
                    # print('Best lay bet = {0}, my ID = {1}'.format(bestLayOddsBet, bettorIndex+1))
                    self.lob[1].bestOdds = bestLayOddsBet['Odds']
                    bestLayOddsID = bestLayOddsBet['BettorID']

                layMatched = False

                # figure out if a lay can be matched
                
                if len(self.lob[1].bets[horseID]) != 0:
                    if bestLayOddsBet['BettorID'] != bettorIndex+1:
                        if self.lob[1].bestOdds != None:
                            if self.lob[1].bestOdds >= backBet['Odds']:
                                layMatched = True
                                # if bettorIndex= 1 or bestLayOddsID == 1:
                                #     print('layMatched {0}, {1}, {2}'.format(bettorIndex, bettorbestLayOddsID))
                                #remove best odds from LOB
                                self.lob[1].matchBet(horseID, bettorIndex, backBet, bestLayOddsID-1, bestLayOddsBet, self.bettors)
                                print('LAY MATCHED INPLAY  - {}'.format(backBet))
                                print('BET MATCHED         - {}'.format(bestLayOddsBet))                              

                if len(self.lob[0].bets[horseID]) != 0:
                    # want to update bet on current leader's market
                    bestBackOddsBet = min(self.lob[0].bets[horseID], key=lambda x: x['Odds'])
                    # print('Best back bet = {0}, my ID = {1}'.format(bestBackOddsBet, bettorIndex+1))
                    self.lob[0].bestOdds = bestBackOddsBet['Odds']
                    bestBackOddsID = bestBackOddsBet['BettorID']
                
                backMatched = False

                #figure out if a back can be matched
                
                if len(self.lob[0].bets[horseID]) != 0:
                    if bestBackOddsBet['BettorID'] != bettorIndex+1:
                        if self.lob[0].bestOdds != None:
                            if self.lob[0].bestOdds <= layBet['Odds']:
                                backMatched = True
                                # if bettorIndex= 1 or bestBackOddsID == 1:                        
                                #     print('backMatched {0}, {1}, {2}'.format(bettorIndex, bettorbestBackOddsID))
                                self.lob[0].matchBet(horseID, bettorIndex, layBet, bestBackOddsID-1, bestBackOddsBet, self.bettors)
                                print('BACK MATCHED INPLAY - {}'.format(layBet))
                                print('BET MATCHED         - {}'.format(bestBackOddsBet))                               
                                    
                # if the LOB is empty, or if no good odds available on the LOB, place a new bet on the LOB
                if layMatched == False:
                    # first place back bet                    
                    self.lob[0].addBet(backBet)
                    self.bettors[bettorIndex].placedBets.append(backBet)
                if backMatched == False:
                    # then place lay bet
                    self.lob[1].addBet(layBet)
                    self.bettors[bettorIndex].placedBets.append(layBet)
            
            #reset best odds
            bestBackOddsBet = None
            bestLayOddsBet = None
            # self.lob[0].bestOdds = None
            # self.lob[1].bestOdds = None
        
        self.unsortedLOB = copy.deepcopy(self.lob)
        self.lob[0].sortLOB()
        self.lob[1].sortLOB()
        # self.lob[0].anonLOB()
        # self.lob[1].anonLOB()

    def determineCurrentStandings(self):
        self.race.currStandings.sort(key=lambda x: [x.currTime, -x.currDistance]) # sort current standings of horses by time (asc.) and then by distance (dist.) if equal time
        for i in range(len(self.race.currStandings)):
            self.race.currStandings[i].currPosition = i+1 # update position
            # print(self.currStandings[i])

    def plotRaceGraph(self):
        fig, ax = plt.subplots() # generate figure with subplots
        plt.axhline(y=self.race.distance, label='Finish line', color='black', linestyle='--')
        for i in range(len(self.race.finalStandings)):
            ax.plot(range(0, len(self.race.finalStandings[i].distanceHistory)), self.race.finalStandings[i].distanceHistory,
                    label='Horse {0} - Time {1}'.format(self.race.finalStandings[i].name, round(self.race.finalStandings[i].finishTime, 1)), color=self.race.finalStandings[i].color) # plot each horses distance-time line graph in order of placing
        legend = ax.legend()
        plt.xlabel('Time (seconds)')
        plt.ylabel('Distance (metres)')
        plt.title('Distance-Time graph for {}'.format(self.race.id))
        plt.savefig('{}_graph.pdf'.format(self.race.id))
        plt.close(fig)

    def runRace(self, inPlay=None):
        if inPlay == True:
            time     = 0 # current race time in 'seconds'
            timestep = 1 # 1 second
            while(self.race.state != 'Finished'): # while race is in running
                time += timestep # race time increases
                self.determineCurrentStandings()
                # do inplay betting stuff
                if len(self.race.currStandings) != 0 and len(self.race.winner) != 1:
                    for bettorIndex in range(self.numBettors):
                        if self.bettors[bettorIndex].inPlayCheck != 0:
                            if time % self.bettors[bettorIndex].inPlayCheck == 0:
                                self.inPlayBetting(bettorIndex, time)
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
                            if len(self.race.winner) == 0:
                                self.race.winner.append(self.race.horses[i]) # winner
                        if len(self.race.finalStandings) == self.race.numHorses: # all horses have finished
                            self.race.time = self.race.horses[-1].finishTime
                            self.race.determineFinalPlacings()
                            self.race.state = 'Finished'
                            self.plotRaceGraph()
                            # print(len(self.race.finalStandings))
                            # print(self.race.numHorses)
                            # print(self.race.state)
                            break
                    else:
                        continue
        else:
            self.race.runRace()
            # for i in range(len(self.race.finalStandings)):
                    # print(self.race.finalStandings[i])
            self.plotRaceGraph()
        
    def payoutWinners(self):
        for bettorIndex in range(self.numBettors):
            numMatchedBacks = 0
            numMatchedLays  = 0
            numUnmatchedBacks = 0
            numUnmatchedLays = 0
            for betCounter in range(len(self.bettors[bettorIndex].matchedBets)):
                bet = self.bettors[bettorIndex].matchedBets[betCounter]
                if bet['HorseName'] == self.race.winner[0].name:
                    if bet['BetType'] == 'Back':
                        # horse won - successful back
                        # get stake back + profit
                        payout = bet['Stake'] + bet['Profit']
                        self.bettors[bettorIndex].balance += payout
                        numMatchedBacks += 1
                    if bet['BetType'] == 'Lay':
                        # horse won - unsuccessful lay
                        # pay liability
                        # self.bettors[bettorIndex].balance -= bet['Liability']
                        pass
                        numMatchedLays += 1
                elif bet['HorseName'] != self.race.winner[0].name:
                    if bet['BetType'] == 'Back':
                        # horse lost - unsuccesful back
                        # stake already removed from balance so no update
                        pass
                        numMatchedBacks += 1
                    if bet['BetType'] == 'Lay':
                        # horse lost - successful lay
                        # receive backer's stake
                        payout = bet['Stake'] + bet['Liability']
                        self.bettors[bettorIndex].balance += payout 
                        numMatchedLays += 1
            for betCounter in range(len(self.bettors[bettorIndex].placedBets)):
                bet = self.bettors[bettorIndex].placedBets[betCounter]
                if bet['BetType'] == 'Back' and bet['Matched'] == False:
                    # unmatched back bet - return stake to bettorIndex
                    # print('Unmatched Bet')
                    self.bettors[bettorIndex].balance += bet['Stake']
                    numUnmatchedBacks += 1

                if bet['BetType'] == 'Lay' and bet['Matched'] == False:
                    self.bettors[bettorIndex].balance += bet['Liability']
                    numUnmatchedLays += 1
            # print('Bettor {0} numMatchedBacks = {1}'.format(bettorIndex+1, numMatchedBacks))
            # print('Bettor {0} numMatchedLays = {1}'.format(bettorIndex+1, numMatchedLays))
            # print('Bettor {0} numUnmatchedBacks = {1}'.format(bettorIndex+1, numUnmatchedBacks))
            # print('Bettor {0} numUnmatchedLays = {1}'.format(bettorIndex+1, numUnmatchedLays))
            self.bettors[bettorIndex].balance = round(self.bettors[bettorIndex].balance, 2)

    

    def visualiseBets(self):
        oddsHistoryDict = {}
        for bettor in range(self.numBettors):
            print('Bettor {0} odds history:  {1}'.format(bettor+1, self.bettors[bettor].oddsHistory))
                
            for j in range(self.numHorses):
                oddsHistoryDict[j+1] = []
                for i in range(len(self.bettors[bettor].oddsHistory)):
                    oddsHistoryDict[j+1].append(self.bettors[bettor].oddsHistory[i][j])
                    
            fig, ax = plt.subplots() # generate figure with subplots
            for horse in range(self.race.numHorses):
                xAxisList = [i*self.bettors[bettor].inPlayCheck for i in range(0, len(oddsHistoryDict[horse+1]))]
                ax.step(xAxisList, oddsHistoryDict[horse+1], where='post', label='Horse {} odds'.format(horse+1), color=self.race.horses[horse].color)
                # ax.plot(xAxisList, oddsHistoryDict[horse+1])
                # ax.plot(xAxisList, oddsHistoryDict[horse+1], label='Horse {} odds'.format(horse+1), color=self.race.horses[horse].color)
            legend = ax.legend()
            plt.xlabel('Time (seconds)')
            plt.ylabel('Decimal odds')
            plt.ylim(bottom=0, top=20)
            plt.title('Odds history of Bettor {0} (updates every {1} seconds)'.format(bettor+1, self.bettors[bettor].inPlayCheck))
            plt.savefig('{0}_Bettor_{1}.pdf'.format(self.race.id, bettor+1))
            plt.close(fig)


if __name__ == "__main__":
    for i in range(5):
        testBBE = BBE('Test', 'Test Race {}'.format(i+1), 2000, 5, 5)
        testBBE.prepareRace()
        testBBE.populateLOB()
        # print(testBBE.unsortedLOB[0].bets[1])
        # print(testBBE.unsortedLOB[1].bets[1])
        # print(testBBE.lob[0].bets[1])
        # print(testBBE.lob[1].bets[1])
        # print(testBBE.lob[0].anonBets[1])
        # print(testBBE.lob[1].anonBets[1])
        # print(testBBE.bettors[0].matchedBets)
        testBBE.runRace(inPlay=True)
        testBBE.payoutWinners()
        totalBalances = 0
        for bettorIndex in range(testBBE.numBettors):
            totalBalances += testBBE.bettors[bettorIndex].balance
            # print(testBBE.bettors[bettorIndex].placedBets)
            print('Bettor {0} balance = {1}'.format(bettorIndex+1, testBBE.bettors[bettorIndex].balance))
            # print(testBBE.bettors[bettorIndex].matchedBets)
            # print(testBBE.bettors[bettorIndex].placedBets)
        print('Total balances = {}'.format(round(totalBalances)))
        print('Race winner = {}'.format(testBBE.race.winner[0].name))
        testBBE.visualiseBets()
        
        # print(round(testBBE.race.winner[0].currTime))
        if round(totalBalances) != round(10000*testBBE.numBettors):
            print(testBBE.bettors[0].matchedBets)
            print(testBBE.bettors[1].matchedBets)
            sys.exit()