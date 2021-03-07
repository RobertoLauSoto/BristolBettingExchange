import numpy as np
import time
import sys

class Horse:
    def __init__(self, name, startDistance, startPos, currDistance, currPos, time, numRaceFactors, raceFactors):
        self.name            = name                             # identity of the horse/competitor
        self.startDistance   = startDistance                    # current distance run by competitor (metres)
        self.startPosition   = startPos                         # starting position of the competitor
        self.currDistance    = currDistance                     # current distance run by competitor (metres)
        self.currPosition    = currPos                          # current position of the competitor
        self.currTime        = time                             # current time taken by competitor (seconds)
        self.maxTopSpeed     = 24                               # top speed of a horse in m/s
        self.minSpeed        = 0                                # minimum speed of competitor
        self.maxSpeed        = 0                                # maximum/top speed of competitor
        self.currSpeed       = 0                                # current speed of the competitor (metres/second)
        self.prevSpeed       = 0                                # speed in previous time step, used to calculate acceleration
        self.finishTime      = 0                                # finish time in real seconds of horse
        self.acceleration    = 0                                # current acceleration of the competitor (m/s2)
        self.prefs           = [None] * numRaceFactors          # vector for inital preference factors of competitor to help calculate step-size
        self.prefFactor      = 0
        self.resp            = 1                                # factor determining responsiveness of competitor, 1 = 100% responsive 
        self.groundLost      = 1                                # factor determinining the ground lost by a competitor due to interfernce, 1 = no delay
        self.distanceHistory = []                               # array of distances run in the race
        self.state           = None                             # currrent state of competitor (Running/Finished/DNF)

        for i in range(numRaceFactors):
            self.prefs[i] = np.random.uniform() # generate random number between 0 and 1
        # print(self.prefs)

        self.minSpeed = np.random.uniform(2.0, 5.0) # uniform distribution between 1 and 5 m/s to determine minimum speed
        self.maxSpeed = np.random.uniform(self.maxTopSpeed / 1.2, self.maxTopSpeed) # uniform distribution between ~12.2 and 24.5872 m/s(world record speed for a horse) to determine maximum speed

        pNorm = 3 # see https://en.wikipedia.org/wiki/Distance#Distance_in_Euclidean_space
        # prefConstant = numRaceFactors ** (1 / pNorm)
        prefConstant = numRaceFactors
        prefDistance = 0
        for i in range(numRaceFactors):
            prefDistance += abs(raceFactors[i] - self.prefs[i]) ** pNorm
        prefDistance = prefDistance ** (1 / pNorm)
        self.prefFactor =  prefConstant - prefDistance
        print('Horse {0} pref distance is : {1}. Pref factor is: {2}. Min speed is: {3}. Max speed is: {4}.'.format(self.name, prefDistance, self.prefFactor, self.minSpeed, self.maxSpeed))
        

    def __str__(self):
        return '[ID %s startDistance %s startPosition %s currDistance %s currPosition %s currSpeed %s currTime %s resp %s groundLost %s state %s]' \
               % (self.name, self.startDistance, self.startPosition, self.currDistance, self.currPosition, self.currSpeed, self.currTime, self.resp, self.groundLost, self.state)
    

