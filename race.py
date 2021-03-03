import numpy as np
import time
import sys
from horse import Horse

class Race:
    def __init__(self, name, distance, numHorses):
        self.id        = name # id of race if multiple races being simulated
        self.distance  = distance # distance of the race in metres
        self.numHorses = numHorses # number of horses/competitors in the race
        self.lanes     = False # determining whether race has lanes, e.g. 100m/200m/sprint swimming. If True, groundLost factor for each competitor remains 1 throughout race
        self.standing  = False # for a standing start, e.g. Formula 1, where each competitor begins stationary at a different distance away frpm start. If True, competitors initialised with different distances
        self.rolling   = False # for a rolling start, e.g. Nascar, where competitors begin race at speed with different distances away from start. If True, comps initialised with diff. distances and speeds
        self.time      = 0 # time taken for the race to officialy end, e.g. last competitor crossed the line or top 3 determined

    def __str__(self) -> str:
        pass

    def initialiseRace(self):
        pass