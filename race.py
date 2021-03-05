import numpy as np
import time
import sys
import pandas as pd
import matplotlib.pyplot as plt
from horse import Horse
class Race:
    def __init__(self, name, distance, numHorses):
        self.id              = name      # id of race, especially useful if multiple races being simulated
        self.distance        = distance  # distance of the race in metres
        self.numHorses       = numHorses # number of horses/competitors in the race
        self.maxTopSpeed     = 24.5872   # top speed of a horse in m/s
        self.raceFactors     = None      # vector for race conditions that affect competitors performance
        self.lanes           = False     # determining whether race has lanes, e.g. 100m/200m/sprint swimming. If True, groundLost factor for each competitor remains 1 throughout race
        self.staggered       = False     # for a staggered start, e.g. Formula 1, where each competitor begins stationary at a different distance away from start. If True, competitors initialised with different distances
        self.rolling         = False     # for a rolling start, e.g. Nascar, where competitors begin race at speed with different distances away from start. If True, comps initialised with diff. distances and speeds
        self.time            = 0         # time taken for the race to officialy end, e.g. last competitor crossed the line or top 3 determined
        self.currStandings   = []        # current standings updated each time step
        self.finalStandings  = []        # final standings at the end of the race
        self.winner          = []        # winner at the end of the race
        self.top3            = []        # top 3 standings at the end of the race
        self.state           = None      # state of race (Running/Finished)
        
    def __str__(self) -> str:
        pass

    def createHorses(self):
        horses = [None] * self.numHorses # array of Horse objects representing the starting horses
        for i in range(0,self.numHorses):
            horses[i] = Horse(i+1, 1, 1, 0, 0) # each horse has a number ID starting from 1 - could be changed to random string names
            horses[i].minSpeed = np.random.uniform(1.0, 5.0) # uniform distribution between 1 and 5 m/s to determine minimum speed
            horses[i].maxSpeed = np.random.uniform(self.maxTopSpeed / 2, self.maxTopSpeed) # uniform distribution between ~12.2 and 24.5872 m/s(world record speed for a horse) to determine maximum speed
            # print(horses[i])
        return horses
    
    def generateForwardStep(self):
        pass
    
    def plotRaceGraph(self, horses):
        fig, ax = plt.subplots() # generate figure with subplots
        for i in range(len(horses)):
            ax.plot(range(0, len(horses[i].distanceHistory)), horses[i].distanceHistory, label='Horse {}'.format(horses[i].name)) # plot each horses distance-time line graph 
        legend = ax.legend(loc='upper left')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Distance (metres)')
        plt.title('Distance-Time graph for {}'.format(self.id))
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
        self.winner.append(self.finalStandings[0]) # get winner
        self.top3.extend([self.finalStandings[0], self.finalStandings[1], self.finalStandings[2]]) # get top 3 placed

    def runRace(self):
        horses   = self.createHorses() # create competitors
        time     = 0 # current race time in 'seconds'
        timestep = 1 # 1 second
        while(self.state != 'Finished'): # while race is in running
            time += timestep # race time increases
            self.determineCurrentStandings()
            for i in range(self.numHorses): # for each horse
                self.currStandings.append(horses[i])
                if horses[i].state != 'Finished' and horses[i].state != 'DNF':
                    horses[i].distanceHistory.append(horses[i].currDistance)
                    horses[i].state = 'Running' # horse is in running
                    horses[i].currTime = time 
                    horses[i].prevSpeed = horses[i].currSpeed # record previous speed
                    horses[i].currSpeed = np.random.uniform(horses[i].minSpeed, horses[i].maxSpeed) # uniform random variable to update speed
                    progress = horses[i].currSpeed * timestep # progress on this timestep, distance = speed x time
                    horses[i].currDistance += progress # update current distance of horse along track
                    if horses[i].currDistance >= self.distance: # horse has crossed finish line
                        horses[i].state = 'Finished'
                        # print('Test : horse ' + str(i+1) + ' finished')
                        self.finalStandings.append(horses[i])
                    if len(self.finalStandings) == self.numHorses: # all horses have finished
                        self.determineFinalPlacings()
                        self.state = 'Finished'
                        self.plotRaceGraph(horses)
                        # print(len(self.finalStandings))
                        # print(self.numHorses)
                        # print(self.state)
                        break
                else:
                    continue
                
if __name__ == "__main__":
    testRace = Race("Test Race", 1000, 8)
    testRace.runRace()
    for i in range(len(testRace.winner)):
        print('Winner {}'.format(testRace.winner[i]))
    for i in range(len(testRace.top3)):
        print('Placed in {0} place {1}'.format(i+1, testRace.top3[i]))
    for i in range(len(testRace.finalStandings)):
        print(testRace.finalStandings[i])
    # testRace.plotRaceGraph(testRace.finalStandings)