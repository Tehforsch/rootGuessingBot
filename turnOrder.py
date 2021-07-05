import itertools


class TurnOrder:
    def __init__(self, players, numTurns):
        self.turnOrder = repeatedCycle(players, numTurns)
        self.currentPlayer = next(self.turnOrder)
        self.players = players
        self.currentPlayersFirstTurn = True

    def isPlayersTurn(self, player):
        return player == self.currentPlayer

    def nextTurn(self):
        previousPlayer = self.currentPlayer
        self.currentPlayer = next(self.turnOrder)
        self.currentPlayersFirstTurn = self.currentPlayer != previousPlayer

    def getPlayerAndMakeTurn(self):
        self.nextTurn()
        return self.currentPlayer

    def setPlayer(self, player):
        assert player in self.players
        while self.currentPlayer != player:
            self.nextTurn()

    def numRemainingGuesses(self):
        self.turnOrder, order = itertools.tee(self.turnOrder)
        numRemaining = 1
        while self.currentPlayer == next(order) and numRemaining < 100:  # oops
            numRemaining += 1
        return numRemaining


def repeatedCycle(items, numTurns):
    repeatedItems = [item for (item, num) in zip(items, numTurns) for _ in range(num)]
    return itertools.cycle(repeatedItems)
