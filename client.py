import sys
from horse import Horse
from bettor import Bettor
from race import Race
from orderBook import OrderBook
from bbe import BBE


if __name__ == "__main__":
    # print('Number of arguments: {} arguments'.format(len(sys.argv)))
    # print('Argument list: {}'.format(str(sys.argv)))
    print("______       ______       ______\n"+
           "| ___ \      | ___ \      |  ___|\n"+
           "| |_/ /      | |_/ /      | |__\n"+
           "| ___ \      | ___ \      |  __|\n"+
           "| |_/ /      | |_/ /      | |___\n"+
           "\____/ristol \____/etting \____/xchange\n")

    BBE_name   = input('Enter a name for this BBE instance:')
    Race_name  = input('Enter a name for the race:')
    while True:
        DistanceString   = input('Enter a distance in metres:')
        try:
            Distance = float(DistanceString)
            break
        except ValueError:
            print("Please enter a valid distance:")
    while True:
        NumHorsesString  = input('Enter a number of horses:') 
        try:
            NumHorses = int(NumHorsesString)
            break
        except ValueError:
            print("Please enter a valid number:")
    while True:
        NumBettorsString = input('Enter a number of bettors:')
        try:
            NumBettors = int(NumBettorsString)
            break
        except ValueError:
            print("Please enter a valid number:")
                                       
    # clientBBE = BBE(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
    clientBBE = BBE(BBE_name, Race_name, Distance, NumHorses, NumBettors)
    # print(clientBBE.raceDistance)
    # print(clientBBE.numHorses)
    # print(clientBBE.numBettors)
    # print("finished")
    clientBBE.prepareRace()
    # print("finished")
    clientBBE.startingBets()
    # print("finished")
    clientBBE.runRace(inPlay=True)
    # print("finished")
    clientBBE.payoutWinners()
    clientBBE.visualiseBets()
    print("BBE simulation complete. Please refer to the figures saved in the 'graphs' folder for results!")