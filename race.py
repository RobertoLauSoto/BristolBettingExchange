import numpy as np
import time
import sys
from horse import Horse
import operator

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
            horses[i].minSpeed = np.random.uniform(1.0, 5.0)
            horses[i].maxSpeed = np.random.uniform(self.maxTopSpeed / 2, self.maxTopSpeed)
            # print(horses[i])
        return horses
    
    def determineCurrentStandings(self):
        self.currStandings.sort(key=lambda x: [x.currTime, -x.currDistance])
        for i in range(0, len(self.currStandings)):
            self.currStandings[i].currPosition = i+1

    def determineFinalPlacings(self):
        self.finalStandings.sort(key=lambda x: [x.currTime, -x.currDistance])
        for i in range(0, len(self.finalStandings)):
            self.finalStandings[i].currPosition = i+1
        self.winner.append(self.finalStandings[0])
        self.top3.extend([self.finalStandings[0], self.finalStandings[1], self.finalStandings[2]])

    def runRace(self):
        horses   = self.createHorses() # create competitors
        time     = 0 # current race time in 'seconds'
        timestep = 1 # 1 second
        while(self.state != 'Finished'):
            time += timestep # race time increases
            self.determineCurrentStandings()
            for i in range(0, self.numHorses):
                self.currStandings.append(horses[i])
                if horses[i].state != 'Finished' and horses[i].state != 'DNF':
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
                        # print(len(self.finalStandings))
                        # print(self.numHorses)
                        # print(self.state)
                        break
                else:
                    continue
                
if __name__ == "__main__":
    testRace = Race("testRace", 1000, 8)
    testRace.runRace()
    for i in range(0, len(testRace.winner)):
        print('Winner ' + str(testRace.winner[i]))
    for i in range(0, len(testRace.top3)):
        print('Placed in ' + str(i+1) + ' place ' + str(testRace.top3[i]))
    for i in range(0, len(testRace.finalStandings)):
        print(testRace.finalStandings[i])