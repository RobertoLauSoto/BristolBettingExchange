import boto3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import time
import copy
import random

sqs = boto3.resource('sqs', region_name='us-east-1')
s3_resource = boto3.resource('s3', region_name='us-east-1')

queue = sqs.get_queue_by_name(QueueName='bbeQueue')

class Horse:
    def __init__(self, name, startDistance, startPos, currDistance, currPos, time, numRaceFactors, raceFactors, color):
        self.name            = name                             # identity of the horse/competitor
        self.startDistance   = startDistance                    # start distance (metres) of the competitor - can be used to model a staggered start
        self.startPosition   = startPos                         # starting position of the competitor
        self.currDistance    = currDistance                     # current distance run by competitor (metres)
        self.currPosition    = currPos                          # current position of the competitor
        self.currTime        = time                             # current time taken by competitor (seconds)
        self.color           = color                            # color of the horse shown in graphs
        self.maxTopSpeed     = 24                               # top speed of a horse in m/s
        self.minSpeed        = 0                                # minimum speed of competitor
        self.maxSpeed        = 0                                # maximum/top speed of competitor
        self.currSpeed       = 0                                # current speed of the competitor (metres/second)
        self.prevSpeed       = 0                                # speed in previous time step, used to calculate acceleration
        self.finishTime      = 0                                # finish time in real seconds of horse
        self.acceleration    = 0                                # current acceleration of the competitor (m/s2)
        self.prefs           = [None] * numRaceFactors          # vector for inital preference factors of competitor to help calculate step-size
        self.prefFactor      = 0                                # preference factor calculated after p-norm distance between pref vector and race factor vector
        # self.prefPnorm1 = 0
        # self.prefPnorm2 = 0
        # self.prefPnorm3 = 0
        self.resp            = 1                                # factor determining responsiveness of competitor, 1 = 100% responsive
        self.delay           = False                            # boolean determining if delay to competitor has occurred
        self.groundLost      = 1                                # factor determinining the ground lost by a competitor due to interfernce, 1 = no delay
        self.distanceHistory = []                               # array of distances run in the race
        self.state           = None                             # currrent state of competitor (Running/Finished/DNF)

        for i in range(numRaceFactors):
            self.prefs[i] = np.random.uniform() # generate random number between 0 and 1
        # print(self.prefs)

        self.minSpeed = np.random.uniform(3.0, 5.0) # uniform distribution between 2 and 5 m/s to determine minimum speed
        self.maxSpeed = np.random.uniform(self.maxTopSpeed / 1.2, self.maxTopSpeed) # uniform distribution between ~12.2 and 24.5872 m/s(world record speed for a horse) to determine maximum speed

        # pNorm1 = 1 # see https://en.wikipedia.org/wiki/Distance#Distance_in_Euclidean_space
        # # prefConstant1 = numRaceFactors ** (1 / pNorm1)
        # prefConstant1 = numRaceFactors
        # prefDistance1 = 0
        # for i in range(numRaceFactors):
        #     prefDistance1 += abs(raceFactors[i] - self.prefs[i]) ** pNorm1
        # prefDistance1 = prefDistance1 ** (1 / pNorm1)
        # self.prefPnorm1 =  (prefConstant1 - prefDistance1) / numRaceFactors

        # pNorm2 = 2 # see https://en.wikipedia.org/wiki/Distance#Distance_in_Euclidean_space
        # # prefConstant2 = numRaceFactors ** (1 / pNorm2)
        # prefConstant2 = numRaceFactors
        # prefDistance2 = 0
        # for i in range(numRaceFactors):
        #     prefDistance2 += abs(raceFactors[i] - self.prefs[i]) ** pNorm2
        # prefDistance2 = prefDistance2 ** (1 / pNorm2)
        # self.prefPnorm2 =  (prefConstant2 - prefDistance2) / numRaceFactors

        pNorm = 3 # see https://en.wikipedia.org/wiki/Distance#Distance_in_Euclidean_space
        # prefConstant = numRaceFactors ** (1 / pNorm)
        prefConstant = numRaceFactors
        prefDistance = 0
        for i in range(numRaceFactors):
            prefDistance += abs(raceFactors[i] - self.prefs[i]) ** pNorm
        prefDistance = prefDistance ** (1 / pNorm)
        # self.prefPnorm =  (prefConstant - prefDistance) / numRaceFactors
        self.prefFactor =  (prefConstant - prefDistance) / numRaceFactors
        # print('Horse {0} pref distance is : {1}. Pref factor is: {2}. Min speed is: {3}. Max speed is: {4}.'.format(self.name, prefDistance, self.prefFactor, self.minSpeed, self.maxSpeed))

    def reset(self):
        self.currDistance = 0
        self.currPosition = 1
        self.currTime = 0
        self.currSpeed = 0
        self.prevSpeed = 0
        self.finishTime = 0
        self.acceleration = 0
        self.resp = 1
        self.delay = False
        self.groundLost = 1
        self.distanceHistory.clear()
        self.state = None
        
    def __str__(self):
        return '[ID %s startDistance %s startPosition %s currDistance %s currPosition %s currSpeed %s currTime %s resp %s groundLost %s state %s minSpeed %s maxSpeed %s]' \
               % (self.name,
                  round(self.startDistance, 5),
                  self.startPosition,
                  round(self.currDistance, 5), 
                  self.currPosition, 
                  round(self.currSpeed, 5), 
                  round(self.currTime, 5), 
                  round(self.resp, 5), 
                  round(self.groundLost, 5), 
                  self.state, 
                  round(self.minSpeed, 5), 
                  round(self.maxSpeed, 5))

class Race:
    def __init__(self, name, distance, numHorses):
        self.id              = name                         # id of race, especially useful if multiple races being simulated
        self.distance        = distance                     # distance of the race in metres
        self.numHorses       = numHorses                    # number of horses/competitors in the race
        self.horses          = [None] * numHorses           # vector of Horse objects representing field of competitors in the race
        self.horseDistances  = [None] * numHorses           # vector of distances representing current distances run by competitors along track
        self.numRaceFactors  = 5                            # number of race factors affecting the performance of horses
        self.raceFactors     = [None] * self.numRaceFactors # vector for race conditions that affect competitors performance
        self.lanes           = False                        # determining whether race has lanes, e.g. 100m/200m/sprint swimming. If True, groundLost factor for each competitor remains 1 throughout race
        self.staggered       = False                        # for a staggered start, e.g. Formula 1, where each competitor begins stationary at a different distance away from start. If True, competitors initialised with different distances
        self.rolling         = False                        # for a rolling start, e.g. Nascar, where competitors begin race at speed with different distances away from start. If True, comps initialised with diff. distances and speeds
        self.raceEndTime            = 0                            # time taken for the race to officialy end, e.g. last competitor crossed the line or top 3 determined
        self.currStandings   = []                           # current standings updated each time step
        self.finalStandings  = []                           # final standings at the end of the race
        self.winner          = []                           # winner at the end of the race
        self.top3            = []                           # top 3 standings at the end of the race
        self.state           = None                         # state of race (Running/Finished)

        for i in range(self.numRaceFactors):
            self.raceFactors[i] = np.random.uniform() # generate random number between 0 and 1
        # print(self.raceFactors)
        
    def __str__(self) -> str:
        pass

    def createHorses(self):
        horses = [None] * self.numHorses
        colors = cm.tab20(range(20))
        for i in range(self.numHorses):
            horses[i] = Horse(i+1, 0, 1, 0, 1, 0, self.numRaceFactors, self.raceFactors, colors[i%20]) # each horse has a number ID starting from 1 - could be changed to random string names
            # print(horses[i])
        self.horses = horses

    def resetHorses(self):
        for i in range(self.numHorses):
            self.horses[i].reset()

    def reset(self):
        self.raceEndTime = 0
        self.currStandings   = []                           
        self.finalStandings  = []                           
        self.winner          = []                           
        self.top3            = []                            
        self.state           = None
        self.horseDistances  = [None] * self.numHorses
        self.resetHorses()

    def generateResponsiveness(self, horse):
        # one way responsiveness can vary is dependent on the distance covered in the race by th competitor
        distanceCovered = horse.currDistance / self.distance
        # competitors are slower at the beginning (e.g first 10% of the race) - scale speed range down by some percentage as they build up speed
        if (distanceCovered <= 0.1 and horse.delay == False):
            horse.resp = np.random.uniform(0.1, 0.4) # horse speed scaled down between 60 to 80% at beginning at random
        # competitors reach closer to their average speed during next 20% of race
        elif (0.1 < distanceCovered <= 0.3 and horse.delay == False):
            horse.resp = np.random.uniform(0.4, 0.8) # horse speed scaled down by a bit less as they gather momentum - 80 to 95%
        # next 60% of race competitors should be at or around their average speed
        elif (0.3 < distanceCovered <= 0.9 and horse.delay == False):
            horse.resp = np.random.uniform(0.8, 1.1) # horse can have short bursts of acceleration or deceleration
        # final 10% of race is volatile - competitors might be tired out or be bursting towards the finish line
        elif (0.9 < distanceCovered < 1.0 and horse.delay == False):
            horse.resp = np.random.uniform(0.5, 1.5)

        # another way horse's resp can vary is if they have a delay themselves - e.g. injury, mechanical failure, tying their shoelaces - this can happen at any stage of the race

        # horse can either recover or stay delayed for this time step - 20% likelihood that they recover
        if random.randint(1, 100) <= 20 and horse.delay == True:
            horse.delay = False
        
        # 2% chance that a horse will get delayed
        if random.randint(1, 100) <= 2 and horse.delay == False:
            horse.delay = True
            horse.resp = np.random.uniform(0.0, 0.2)

    def generateGroundLoss(self, horse):
        groundLostFactor = 1
        for i in range(len(self.horseDistances)):
            if horse.name != i+1: # avoid comparing a horse to itself
                if (0 <= self.horseDistances[i] - horse.currDistance <= 2): # if current horse is 2 metres or fewer behind comparison horse
                    if (self.horses[i].currSpeed > horse.currSpeed): # if comparison horse is faster - do nothing
                        # groundLostFactor += 1
                        continue
                    else: # if comparison horse is slower - groundLost affected
                        if random.randint(1, 100) <= 30: # 30% likelihood slower horse in front will affect faster horse behind as overtake fails
                            groundLostFactor = np.random.normal(0.5, 0.1) * groundLostFactor # horse is around 50% slower
                            # print('Overtake by Horse {0} on Horse {1} failed - ground lost factor is {2}'.format(horse.name, self.horses[i].name, groundLostFactor))
                        else: # overtake occurs - groundLost not affected
                            # groundLostFactor += 1
                            # print('Overtake by Horse {0} on Horse {1} success - ground lost factor is {2}'.format(horse.name, self.horses[i].name, groundLostFactor))
                            continue
                else:
                    # groundLostFactor += 1
                    continue
        # horse.groundLost = groundLostFactor / self.numHorses
        horse.groundLost = groundLostFactor

    def generateForwardStep(self, horse):
        self.generateResponsiveness(horse)
        # print('Horse {0} horse.resp = {1}'.format(horse.name, horse.resp))
        if self.horseDistances[horse.name-1] != None:
            self.generateGroundLoss(horse)    
        progress = horse.prefFactor*horse.resp*horse.groundLost*np.random.uniform(horse.minSpeed, horse.maxSpeed) # uniform random variable to update speed
        return progress 

    def plotRaceGraph(self):
        fig, ax = plt.subplots() # generate figure with subplots
        for i in range(len(self.finalStandings)):
            ax.plot(range(0, len(self.finalStandings[i].distanceHistory)), self.finalStandings[i].distanceHistory, 
                    # label='Horse {0} - Time {1}'.format(self.finalStandings[i].name, round(self.finalStandings[i].finishTime, 1)), color=self.finalStandings[i].color) # plot each horses distance-time line graph in order of placing
                    label='Horse {}'.format(self.finalStandings[i].name), color=self.finalStandings[i].color) # plot each horses distance-time line graph in order of placing
        plt.axhline(y=self.distance, label='Finish line', color='black', linestyle='--')
        legend = ax.legend()
        plt.xlabel('Time (seconds)')
        plt.ylabel('Distance (metres)')
        # plt.title('Distance-Time graph for {}'.format(self.id))
        plt.show()

    def determineCurrentStandings(self):
        self.currStandings.sort(key=lambda x: [x.currTime, -x.currDistance]) # sort current standings of horses by time (asc.) and then by distance (dist.) if equal time
        for i in range(len(self.currStandings)):
            self.currStandings[i].currPosition = i+1 # update position
            # print(self.currStandings[i])
        self.currStandings.clear() # clear array for next iteration

    def determineFinalPlacings(self):
        self.finalStandings.sort(key=lambda x: [x.currTime, -x.currDistance]) # sort final standings of horses by time (asc.) and then by distance (dist.) if equal time
        for i in range(len(self.finalStandings)):
            self.finalStandings[i].currPosition = i+1 # place final position
        if len(self.finalStandings) >= 3:
            self.top3.extend([self.finalStandings[0], self.finalStandings[1], self.finalStandings[2]]) # get top 3 placed
        else:
            self.top3.extend([self.finalStandings])


    def runRace(self):
        time     = 0 # race clock in seconds
        timestep = 1 # timestep is 1 second
        while(self.state != 'Finished'): # while race is in running
            time += timestep # race clock increases
            self.determineCurrentStandings()
            for i in range(self.numHorses): # for each horse
                self.currStandings.append(self.horses[i])
                if self.horses[i].state != 'Finished' and self.horses[i].state != 'Retired':
                    self.horses[i].state = 'Running' # horse is in running
                    self.horses[i].currTime = time # update horse's time
                    self.horses[i].prevSpeed = self.horses[i].currSpeed # record previous speed
                    self.horses[i].currSpeed = self.generateForwardStep(self.horses[i]) # function to generate forward step at each iteration
                    progress = self.horses[i].currSpeed * timestep # progress on this timestep, distance = speed x time
                    self.horses[i].currDistance += progress # update current distance of horse
                    self.horses[i].distanceHistory.append(self.horses[i].currDistance) # append to distance history array for the distance-time graph
                    self.horseDistances[i] = self.horses[i].currDistance # update the distance to inform the other horses
                    if self.horses[i].currDistance >= self.distance: # if horse has crossed finish line
                        self.horses[i].state = 'Finished'
                        self.horses[i].finishTime = (time - timestep) + ((self.distance - self.horses[i].distanceHistory[-1]) / self.horses[i].currSpeed) # finish time in real seconds
                        self.horses[i].currTime = self.horses[i].finishTime
                        # print('Test : horse ' + str(i+1) + ' finished')
                        self.finalStandings.append(self.horses[i])
                        if len(self.winner) == 0:
                            self.winner.append(self.horses[i]) # winner
                    if len(self.finalStandings) == self.numHorses: # if all horses have finished
                        self.determineFinalPlacings()
                        self.raceEndTime = self.finalStandings[-1].finishTime # race finish time is the same as the last placed horse's finish time
                        self.state = 'Finished'
                        # self.plotRaceGraph()
                        # print(len(self.finalStandings))
                        # print(self.numHorses)
                        # print(self.state)
                        break
                else:
                    continue

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
        self.oddsHistory      = []
        self.numChecksDone    = 0
        self.unmatchedBacks   = 0
        self.updateOddsWeight = 0
        self.oddsWeightChosen = False

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
        # update 7/4/21: first version of inPlayBetting done a couple of days ago. This function only updates 2 horses right now (current leader and projected
        # winner), maybe update all horses odds?
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
            # print('I SHOULD UPDATE ODDS - Horse {0} winning, Horse {1} projected, Time checked was {2}'.format(currentStandings[0].name, self.projStandings[0]['HorseName'], time))
        
        self.currentOdds = copy.deepcopy(oddsArray)
        self.oddsHistory.append(oddsArray)    
            
        return updateBets
    
    def calcOddsWeight(self, currentStandings, time):
        # this should determine an odds weight depending on how much of the race is left
        percentDistCovered = currentStandings[0].currDistance / self.race.distance
        self.updateOddsWeight = percentDistCovered 

    def calcProbFromCurrentDistance(self, horseCurrentPostion, horseCurrentDistance, invTotalDistancesLeft):
        # calc denominator
        positionWeight = self.race.numHorses + 1 - horseCurrentPostion
        probability = ((positionWeight * (1 / (self.race.distance - horseCurrentDistance))) / invTotalDistancesLeft) * 100
        
        return probability

    def updateAllOdds(self, currentStandings, time):
        # 8/4/21: trying to implement update of all horses odds, depending on their current position compared to their projected placing
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

class OrderBook:
    def __init__(self, orderBookType):
        self.orderBookType   = orderBookType # backs or lays
        self.bets      = {}      # dictionary of list of bets on this orderBook, to be anonymized
        self.anonBets  = {}      # list of anonymised bets, made public to all bettors (keep as dictionary?)
        self.bestOdds  = None    # best odds offered on the orderBook, including stake
    
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

class BBE:
    def __init__(self, name, raceName, raceDistance, numHorses, numBettors, bbeBucketName):
        self.name               = name # name of betting exchange
        self.race               = None # Race object that will take place and bets placed on
        self.raceName           = raceName
        self.raceDistance       = raceDistance
        self.numHorses          = numHorses
        self.numBettors         = numBettors # number of bettors placing bets on the race
        self.bettors            = [None] * numBettors # list of Bettor objects that will populate this betting exchange
        self.orderBook          = [] # Order book of betting exchange, made up of backs and lays orderBooks (essentially an array of two orderBook objects)
        self.unsortedOrderBook  = []
        self.backs              = None # orderBook offered to back a horse
        self.lays               = None # orderBook offered to lay a horse
        self.maxStake           = 20 # maximum stake allowed on the exchange

    def prepareRace(self):
        self.race = Race(self.raceName, self.raceDistance, self.numHorses) # create race
        self.race.createHorses() # create competitors
        # create bettors
        # select inPlayCheck from random number
        inPlayChecks = [10, 30, 60, 120, 240] # 11/4/2021: 1 bettor for each type of update
        for i in range(self.numBettors): # for each bettor in array
            inPlayCheck  = np.random.choice(inPlayChecks)
            # inPlayCheck = inPlayChecks[0]
            # inPlayChecks.remove(inPlayCheck)
            self.bettors[i] = Bettor(i+1, 10000, 'Back/Lay', 0, self.race, inPlayCheck) # create bettor
            # print('Bettor {0} inPlayCheck = {1}'.format(i+1, inPlayCheck))
            numPriorSims = np.random.randint(1, 2)
            # print("numPriorSims = {}".format(numPriorSims))
            self.bettors[i].runSimulations(numPriorSims) # run simulations

    def startingBets(self):
        # create two empty orderBook objects for the backs and lays and create whole order book from there
        self.backs = OrderBook('Backs')
        self.lays  = OrderBook('Lays')
        
        for horse in range(self.race.numHorses): # go ladder by ladder in orderBook
            listOfBettors = list(range(1, self.numBettors+1))
            bestBackOddsBet     = None
            bestLayOddsBet      = None
            self.backs.bestOdds = None
            self.lays.bestOdds  = None
            # print('HORSE {}'.format(horse+1))
            for bettorIndex in range(self.numBettors):
                # get best odds currently on orderBook, depends on what action is to be taken by the bettor
                # for the backs orderBook, bettor wants to get matched with lowest odds available - therefore best odds is the min value on the orderBook
                # for the lays orderBook, vice versa - best odds is the max value as the bettor would like to make as much money as possible
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
                # check if orderBook is empty; if not, see if a bet on there can be matched
                if self.lays.bestOdds != None:
                    # figure out if a lay can be matched
                    if self.lays.bestOdds >= backBet['Odds']:
                        layMatched = True
                        # if randomBettorId == 1 or bestLayOddsID == 1:
                        #     print('layMatched {0}, {1}, {2}'.format(bettorIndex, randomBettorId, bestLayOddsID))
                        #remove best odds from orderBook
                        self.lays.matchBet(horse+1, randomBettorId-1, backBet, bestLayOddsID-1, bestLayOddsBet, self.bettors)
                if self.backs.bestOdds != None:
                    #figure out if a back can be matched
                    if self.backs.bestOdds <= layBet['Odds']:
                        backMatched = True
                        # if randomBettorId == 1 or bestBackOddsID == 1:                        
                        #     print('backMatched {0}, {1}, {2}'.format(bettorIndex, randomBettorId, bestBackOddsID))
                        self.backs.matchBet(horse+1, randomBettorId-1, layBet, bestBackOddsID-1, bestBackOddsBet, self.bettors)
                # if the orderBook is empty, or if no good odds available on the orderBook, place a new bet on the orderBook
                if self.backs.bestOdds == None or layMatched == False:
                    # first place back bet
                    self.backs.addBet(backBet)
                    self.bettors[randomBettorId-1].placedBets.append(backBet)
                    
                if self.lays.bestOdds == None or backMatched == False:
                    # then place lay bet
                    self.lays.addBet(layBet)  
                    self.bettors[randomBettorId-1].placedBets.append(layBet)                            

        self.orderBook.append(self.backs)
        self.orderBook.append(self.lays) 
        self.unsortedOrderBook = copy.deepcopy(self.orderBook)
        self.orderBook[0].sortOrderBook()
        self.orderBook[1].sortOrderBook()
        # self.orderBook[0].anonOrderBook()
        # self.orderBook[1].anonOrderBook()

    def inPlayBetting(self, bettorIndex, time):
        currentLeaderID = self.race.currStandings[0].name
        projWinnerID = self.bettors[bettorIndex].projStandings[0]['HorseName']
        horseIDs = [currentLeaderID, projWinnerID]
        # make bettor choose odds weight
        # if self.bettors[bettorIndex].oddsWeightChosen == False:
            # self.bettors[bettorIndex].chooseOddsWeight(time)
        # updateBets = self.bettors[bettorIndex].updateLeaderOdds(self.race.currStandings, time, currentLeaderID, projWinnerID)
        self.bettors[bettorIndex].updateAllOdds(self.race.currStandings, time)
        for horse in range(len(horseIDs)): # go ladder by ladder on the orderBook
            horseID = horseIDs[horse]
            if self.race.horses[horseID-1].state != 'Finished': # to prevent bets trading when the horses in question have already finished
                # bettor can only have one open bet on the orderBook at a time, so remove open bet if present
                # first deal with back
                # print('Horse {0} is still running, current state = {1}, time={2}'.format(horseID, self.race.horses[horseID-1].state, time))
                self.orderBook[0].removeBet(horseID, bettorIndex+1)
                self.orderBook[1].removeBet(horseID, bettorIndex+1)

                backBet = self.bettors[bettorIndex].placeInPlayBet(horseID-1, 'Back', time) # back bet the bettor wants to either match or add onto orderBook
                layBet  = self.bettors[bettorIndex].placeInPlayBet(horseID-1, 'Lay', time) # lay bet the bettor wants to either match or add onto orderBook

                if len(self.orderBook[1].bets[horseID]) != 0:
                    bestLayOddsBet = max(self.orderBook[1].bets[horseID], key=lambda x: x['Odds'])                    
                    # print('Best lay bet = {0}, my ID = {1}'.format(bestLayOddsBet, bettorIndex+1))
                    self.orderBook[1].bestOdds = bestLayOddsBet['Odds']
                    bestLayOddsID = bestLayOddsBet['BettorID']

                layMatched = False

                # figure out if a lay can be matched
                
                if len(self.orderBook[1].bets[horseID]) != 0:
                    if bestLayOddsBet['BettorID'] != bettorIndex+1:
                        if self.orderBook[1].bestOdds != None:
                            if self.orderBook[1].bestOdds >= backBet['Odds']:
                                layMatched = True
                                # if bettorIndex= 1 or bestLayOddsID == 1:
                                #     print('layMatched {0}, {1}, {2}'.format(bettorIndex, bettorbestLayOddsID))
                                #remove best odds from orderBook
                                self.orderBook[1].matchBet(horseID, bettorIndex, backBet, bestLayOddsID-1, bestLayOddsBet, self.bettors)
                                # print('LAY MATCHED INPLAY  - {}'.format(backBet))
                                # print('BET MATCHED         - {}'.format(bestLayOddsBet))                              

                if len(self.orderBook[0].bets[horseID]) != 0:
                    # want to update bet on current leader's market
                    bestBackOddsBet = min(self.orderBook[0].bets[horseID], key=lambda x: x['Odds'])
                    # print('Best back bet = {0}, my ID = {1}'.format(bestBackOddsBet, bettorIndex+1))
                    self.orderBook[0].bestOdds = bestBackOddsBet['Odds']
                    bestBackOddsID = bestBackOddsBet['BettorID']
                
                backMatched = False

                #figure out if a back can be matched
                
                if len(self.orderBook[0].bets[horseID]) != 0:
                    if bestBackOddsBet['BettorID'] != bettorIndex+1:
                        if self.orderBook[0].bestOdds != None:
                            if self.orderBook[0].bestOdds <= layBet['Odds']:
                                backMatched = True
                                # if bettorIndex= 1 or bestBackOddsID == 1:                        
                                #     print('backMatched {0}, {1}, {2}'.format(bettorIndex, bettorbestBackOddsID))
                                self.orderBook[0].matchBet(horseID, bettorIndex, layBet, bestBackOddsID-1, bestBackOddsBet, self.bettors)
                                # print('BACK MATCHED INPLAY - {}'.format(layBet))
                                # print('BET MATCHED         - {}'.format(bestBackOddsBet))                               
                                    
                # if the orderBook is empty, or if no good odds available on the orderBook, place a new bet on the orderBook
                if layMatched == False:
                    # first place back bet                    
                    self.orderBook[0].addBet(backBet)
                    self.bettors[bettorIndex].placedBets.append(backBet)
                if backMatched == False:
                    # then place lay bet
                    self.orderBook[1].addBet(layBet)
                    self.bettors[bettorIndex].placedBets.append(layBet)
            
            #reset best odds
            bestBackOddsBet = None
            bestLayOddsBet = None
            # self.orderBook[0].bestOdds = None
            # self.orderBook[1].bestOdds = None
        
        self.unsortedOrderBook = copy.deepcopy(self.orderBook)
        self.orderBook[0].sortOrderBook()
        self.orderBook[1].sortOrderBook()
        # self.orderBook[0].anonOrderBook()
        # self.orderBook[1].anonOrderBook()

    def determineCurrentStandings(self):
        self.race.currStandings.sort(key=lambda x: [x.currTime, -x.currDistance]) # sort current standings of horses by time (asc.) and then by distance (dist.) if equal time
        for i in range(len(self.race.currStandings)):
            self.race.currStandings[i].currPosition = i+1 # update position
            # print(self.currStandings[i])

    def plotRaceGraph(self, bbeBucketName):
        fig, ax = plt.subplots() # generate figure with subplots
        plt.axhline(y=self.race.distance, label='Finish line', color='black', linestyle='--')
        for i in range(len(self.race.finalStandings)):
            ax.plot(range(0, len(self.race.finalStandings[i].distanceHistory)), self.race.finalStandings[i].distanceHistory,
                    label='Horse {0} - Time {1}'.format(self.race.finalStandings[i].name, round(self.race.finalStandings[i].finishTime, 1)), color=self.race.finalStandings[i].color) # plot each horses distance-time line graph in order of placing
        legend = ax.legend()
        plt.xlabel('Time (seconds)')
        plt.ylabel('Distance (metres)')
        plt.title('Distance-Time graph for {}'.format(self.race.id))
        filename = '{0}_graph_{1}.pdf'.format(self.race.id, self.name)
        plt.savefig(filename)
        s3_resource.meta.client.upload_file(Filename=filename, Bucket=bbeBucketName, Key=filename)
        plt.close(fig)

    def runRace(self, bbeBucketName, inPlay=None):
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
                            self.plotRaceGraph(bbeBucketName)
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

    def visualiseBets(self, bbeBucketName):
        oddsHistoryDict = {}
        for bettor in range(self.numBettors):
            # print('Bettor {0} odds history:  {1}'.format(bettor+1, self.bettors[bettor].oddsHistory))
                
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
            filename = '{0}_Bettor_{1}.pdf'.format(self.name, bettor+1)
            plt.savefig(filename)
            s3_resource.meta.client.upload_file(Filename=filename, Bucket=bbeBucketName, Key=filename)
            plt.close(fig)

while True:
    for message in queue.receive_messages(MessageAttributeNames=['BbeName', 'RaceName', 'RaceDistance', 'NumHorses', 'NumBettors', 'BbeBucket', 'TotalSims']):
        bbeInstanceName = ''
        raceName        = ''
        distance        = None
        numHorses       = None
        numBettors      = None
        bbeBucketName   = ''
        totalSims       = None            

        if message.message_attributes is not None:
            bbeNameString    = message.message_attributes.get('BbeName').get('StringValue')
            raceNameString   = message.message_attributes.get('RaceName').get('StringValue')
            distanceString   = message.message_attributes.get('RaceDistance').get('StringValue')
            numHorsesString  = message.message_attributes.get('NumHorses').get('StringValue')
            numBettorsString = message.message_attributes.get('NumBettors').get('StringValue')
            bbeBucketString  = message.message_attributes.get('BbeBucket').get('StringValue')
            totalSimsString  = message.message_attributes.get('TotalSims').get('StringValue')
            if bbeNameString:
                bbeInstanceName = '{0}'.format(bbeNameString)
            if raceNameString:
                raceName = '{0}'.format(raceNameString)
            if distanceString:
                distance = float(distanceString)
            if numHorsesString:
                numHorses = int(numHorsesString)
            if numBettorsString:
                numBettors = int(numBettorsString)
            if bbeBucketString:
                bbeBucketName = '{0}'.format(bbeBucketString)
            if totalSimsString:
                totalSims = int(totalSimsString)

            print('Running BBE instance {0}. Uploading to bucket {1}'.format(bbeInstanceName, bbeBucketName))
            startTime = time.time()
            bbeInstance = BBE(bbeInstanceName, raceName, distance, numHorses, numBettors, bbeBucketName)
            bbeInstance.prepareRace()
            bbeInstance.startingBets()
            bbeInstance.runRace(bbeBucketName, inPlay=True)
            bbeInstance.payoutWinners()
            bbeInstance.visualiseBets(bbeBucketName)
            timeTakenToRunSim = time.time() - startTime
            print('Time taken to run simulation {0} was {1} seconds.'.format(bbeInstanceName, timeTakenToRunSim))
            message.delete()