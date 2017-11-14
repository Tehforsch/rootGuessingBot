import random
import os
import itertools

class TurnOrder:
    def __init__(self, players):
        self.players = players
        self.turnOrder = itertools.cycle(players)
        self.currentPlayer = next(self.turnOrder)

    def isPlayersTurn(self, player):
        return player == self.currentPlayer

    def nextTurn(self):
        self.currentPlayer = next(self.turnOrder)

    def getPlayerAndMakeTurn(self):
        player = self.currentPlayer
        self.nextTurn()
        return player

    def setPlayer(self, player):
        assert player in self.players
        self.currentPlayer = player
        index = self.players.index(player)
        playerOrder = self.players[index:] + self.players[:index]
        self.turnOrder = itertools.cycle(playerOrder)
        # advance once
        _ = next(self.turnOrder)

class Game:
    def __init__(self, players):
        self.players = players
        for player in self.players:
            player.score = 0
        self.numRoots = 4
        self.function = Function(self.numRoots)
        self.log = Log()
        self.log.write("Hello and welcome to this amazing game!")
        self.startingPlayerTurnOrder = TurnOrder(self.players)
        self.turnOrder = TurnOrder(self.players)
        self.setStartingPlayer()

    def handlePlayerGuess(self, player, guessedNumber):
        if not self.turnOrder.isPlayersTurn(player):
            self.log.write("It is not your turn {}".format(player))
            return
        else:
            if not self.guess(guessedNumber):
                self.turnOrder.nextTurn()

    def guess(self, guessedNumber):
        result = self.function((guessedNumber,))
        self.log.write("{} guessed. f({}) = {:,}".format(self.turnOrder.currentPlayer, guessedNumber, result))
        if result == 0:
            self.handleWonGame()
            return True
        return False

    def setStartingPlayer(self):
        startingPlayer = self.startingPlayerTurnOrder.getPlayerAndMakeTurn()
        self.turnOrder.setPlayer(startingPlayer)
        self.log.write("It's {}'s turn".format(startingPlayer))

    def handleWonGame(self):
        self.log.write("{} WINS HE IS AWESOME WOW".format(self.turnOrder.currentPlayer))
        self.turnOrder.currentPlayer.score += 1
        self.log.write("Zeroes: {}".format(self.function.params))
        self.log.write("The score is: ")
        for player in self.players:
            self.log.write("    {}: {}".format(player, player.score))
        self.setStartingPlayer()
        self.reset()

    def reset(self):
        self.log.write("Creating a new polynomial with {} roots.".format(self.numRoots))
        self.function = Function(self.numRoots)

    def setNumRoots(self, numRoots):
        self.numRoots = numRoots

    def resetScore(self):
        self.log.write("Resetting the score to 0.")
        for player in self.players:
            player.score = 0

class Function:
    def __init__(self, numParams):
        self.params = sorted([random.randint(0, 100) for i in range(numParams)])

    def __call__(self, inputs):
        product = 1
        for p in self.params:
            product *= (inputs[0] - p)
        return product

class Log:
    def __init__(self):
        self.content = ""

    def write(self, text):
        self.content = self.content + text + "\n"

    def dump(self):
        buf = self.content
        self.content = ""
        return buf

