import numpy as np
import time
import sys

class Horse:
    def __init__(self, number, start, position, distance, time):
        self.number         = number # identity of the horse/competitor
        self.startPosition  = start # starting position of the competitor
        self.currPosition   = position # current position of the competitor
        self.currDistance   = distance # current distance run by competitor (metres)
        self.currTime       = time # current time taken by competitor (seconds)
        self.currSpeed      = 0 # current speed of the competitor (metres/second)
        self.acceleration   = 0 # current acceleration of the competitor (m/s2)
        self.prefs          = None # vector for inital preference factors of competitor to help calculate step-size
        self.responsiveness = 1 # factor determining responsiveness of competitor, 1 = 100% responsive 
        self.groundLost     = 1 # factor determinining the ground lost by a competitor due to interfernce, 1 = no delay
        self.status         = None # currrent status of competitor (Start/Running/Finished)

    def __str__(self):
        return '[ID %s startPos %s currPos %s currDis %s currSpeed %s currAcc %s resp %s groundLost %s status %s]' \
               % (self.number, self.startPosition, self.currPosition, self.currDistance, self.currSpeed, self.acceleration, self.responsiveness, self.groundLost, self.status)
    
    
