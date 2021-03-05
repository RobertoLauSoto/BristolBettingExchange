import numpy as np
import time
import sys

class Horse:
    def __init__(self, name, start, position, distance, time):
        self.name            = name # identity of the horse/competitor
        self.startPosition   = start # starting position of the competitor
        self.currPosition    = position # current position of the competitor
        self.currDistance    = distance # current distance run by competitor (metres)
        self.currTime        = time # current time taken by competitor (seconds)
        self.minSpeed        = 0 # minimum speed of competitor
        self.maxSpeed        = 0 # maximum/top speed of competitor
        self.currSpeed       = 0 # current speed of the competitor (metres/second)
        self.prevSpeed       = 0 # speed in previous time step, used to calculate acceleration
        self.acceleration    = 0 # current acceleration of the competitor (m/s2)
        self.prefs           = None # vector for inital preference factors of competitor to help calculate step-size
        self.resp            = 1 # factor determining responsiveness of competitor, 1 = 100% responsive 
        self.groundLost      = 1 # factor determinining the ground lost by a competitor due to interfernce, 1 = no delay
        self.distanceHistory = []
        self.state           = None # currrent state of competitor (Running/Finished/DNF)

    def __str__(self):
        return '[ID %s startPosition %s currPosition %s currDistance %s currSpeed %s currTime %s resp %s groundLost %s state %s]' \
               % (self.name, self.startPosition, self.currPosition, self.currDistance, self.currSpeed, self.currTime, self.resp, self.groundLost, self.state)
    

