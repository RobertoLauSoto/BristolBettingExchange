import numpy as np
import random
import time
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from horse import Horse
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
        self.raceEndTime     = 0                            # time taken for the race to officialy end, e.g. last competitor crossed the line or top 3 determined
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
                        continue
                    else: # if comparison horse is slower - groundLost affected
                        if random.randint(1, 100) <= 30: # 30% likelihood slower horse in front will affect faster horse behind as overtake fails
                            groundLostFactor = np.random.normal(0.5, 0.1) * groundLostFactor # horse is around 50% slower
                            # print('Overtake by Horse {0} on Horse {1} failed - ground lost factor is {2}'.format(horse.name, self.horses[i].name, groundLostFactor))
                        else: # overtake occurs - groundLost not affected
                            # print('Overtake by Horse {0} on Horse {1} success - ground lost factor is {2}'.format(horse.name, self.horses[i].name, groundLostFactor))
                            continue
                else:
                    continue
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
                
if __name__ == "__main__":
    numHorses = [5, 10, 15, 20, 25, 30, 35, 40]
    numSims = [1, 10, 100, 1000, 10000, 20000, 40000, 60000, 80000, 100000]
    runtimes = []
    numWins = [0]*10
    # pNorm1 = [62, 0, 6, 2, 0, 8, 0, 8, 3, 11]
    # pNorm2 = [39, 0, 17, 10, 0, 2, 11, 17, 0, 4]
    # pNorm3 = [26, 0, 14, 8, 0, 4, 12, 28, 0, 8]
    pNorm1Results = [0]*10
    pNorm2Results = [0]*10
    pNorm3Results = [0]*10
    # for n in range(len(numSims)):
    #     start = time.time()
    
    testRace = Race("Test Race", 2000, 10)
    testRace.createHorses() # create competitors 
    for i in range(numSims[4]*3):
        if i < 10000:
            for j in range(len(testRace.horses)):
                testRace.horses[j].prefFactor = testRace.horses[j].prefPnorm1
        if 10000 <= i < 20000:
            for j in range(len(testRace.horses)):
                testRace.horses[j].prefFactor = testRace.horses[j].prefPnorm2
        if 20000 <= i < 30000:
            for j in range(len(testRace.horses)):
                testRace.horses[j].prefFactor = testRace.horses[j].prefPnorm3                       
        # testRace.id = 'Test Race {0} - numHorses {1}'.format(numSims+1, numHorses[n])
        testRace.runRace()
        if i < 10000:
            pNorm1Results[testRace.winner[0].name - 1] += 1
        if 10000 <= i < 20000:
            pNorm2Results[testRace.winner[0].name - 1] += 1
        if 20000 <= i < 30000:
            pNorm3Results[testRace.winner[0].name - 1] += 1
        # for i in range(len(testRace.winner)):
        #     print('Winner {}'.format(testRace.winner[i]))
        # for i in range(len(testRace.top3)):
        #     print('Placed in {0} place {1}'.format(i+1, testRace.top3[i]))
        # for i in range(len(testRace.finalStandings)):
        #     print(testRace.finalStandings[i])
        # testRace.plotRaceGraph()
        # print('{} complete'.format(testRace.id))
        testRace.reset()
        # end = time.time()
        # runTime = end- start
        # runtimes.append(runTime)
    # plt.scatter(numSims, runtimes)
    # plt.xlabel('Number of Simulations (N)')
    # plt.ylabel('Runtime (s)')
    # plt.yscale('log')
    # plt.title('Runtimes of N Simulations')
    # print(runtimes)
    # plt.show()
    print(pNorm1Results)
    print(pNorm2Results)
    print(pNorm3Results)

