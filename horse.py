import numpy as np
import time
import sys

class Horse:
    def __init__(self, name, startDistance, startPos, currDistance, currPos, time):
        self.name            = name # identity of the horse/competitor
        self.startDistance   = startDistance # current distance run by competitor (metres)
        self.startPosition   = startPos # starting position of the competitor
        self.currDistance    = currDistance # current distance run by competitor (metres)
        self.currPosition    = currPos # current position of the competitor
        self.currTime        = time # current time taken by competitor (seconds)
        self.minSpeed        = 0 # minimum speed of competitor
        self.maxSpeed        = 0 # maximum/top speed of competitor
        self.currSpeed       = 0 # current speed of the competitor (metres/second)
        self.prevSpeed       = 0 # speed in previous time step, used to calculate acceleration
        self.finishTime      = 0 # finish time in real seconds of horse
        self.acceleration    = 0 # current acceleration of the competitor (m/s2)
        self.prefs           = None # vector for inital preference factors of competitor to help calculate step-size
        self.resp            = 1 # factor determining responsiveness of competitor, 1 = 100% responsive 
        self.groundLost      = 1 # factor determinining the ground lost by a competitor due to interfernce, 1 = no delay
        self.distanceHistory = [] # array of distances run in the race
        self.state           = None # currrent state of competitor (Running/Finished/DNF)

    def __str__(self):
        return '[ID %s startDistance %s startPosition %s currDistance %s currPosition %s currSpeed %s currTime %s resp %s groundLost %s state %s]' \
               % (self.name, self.startDistance, self.startPosition, self.currDistance, self.currPosition, self.currSpeed, self.currTime, self.resp, self.groundLost, self.state)
    

