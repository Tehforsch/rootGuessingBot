import random
import os
import itertools

class Game:
    def __init__(self, players):
        self.players = players
        for player in self.players:
            player.score = 0
        self.turnOrder = itertools.cycle(self.players)
        self.currentPlayer = next(self.turnOrder)
        self.function = Function(4)
        self.log = Log()
        self.log.write("Hello and welcome to this amazing game!")

    def handlePlayerGuess(self, player, guessedNumber):
        if not self.isPlayersTurn(player):
            self.log.write("It is not your turn {}".format(player))
            return
        else:
            self.guess(guessedNumber)
            self.currentPlayer = next(self.turnOrder)

    def guess(self, guessedNumber):
        result = self.function((guessedNumber,))
        self.log.write("{} guessed. f({}) = {:,}".format(self.currentPlayer, guessedNumber, result))
        if result == 0:
            self.handleWonGame()

    def isPlayersTurn(self, player):
        return player == self.currentPlayer

    def handleWonGame(self):
        self.log.write("{} WINS HE IS AWESOME WOW".format(self.currentPlayer))
        self.currentPlayer.score += 1
        self.log.write("Zeroes: {}".format(self.function.params))
        self.log.write("The score is: ")
        for player in self.players:
            self.log.write("    {}: {}".format(player, player.score))
        self.log.write("Creating a new polynomial.")
        self.reset()

    def reset(self):
        self.function = Function(4)

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

