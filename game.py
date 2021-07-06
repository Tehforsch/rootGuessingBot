import random
import os
from turnOrder import TurnOrder
from function import Function
from log import Log
from gameSettings import GameSettings


class Game:
    def __init__(self, players, settings=None):
        self.players = players
        self.settings = GameSettings() if settings is None else settings
        for player in self.players:
            player.numGuessedRoots = 0
        self.log = Log()
        self.log.write("Hello and welcome to this amazing game!")
        self.resetFunction()
        self.startingPlayerTurnOrder = TurnOrder(self.players, [1 for _ in self.players])
        self.resetTurnOrder()
        self.setStartingPlayer()

    def dumpSettings(self):
        return "\n".join("{} = {}".format(k, v) for (k, v) in self.settings.iterVariables())

    def handlePlayerWantsNumGuesses(self, player, numGuesses):
        if not self.turnOrder.isPlayersTurn(player):
            self.log.write("It is not your turn {}".format(player))
        elif not self.startingPlayerTurnOrder.isPlayersTurn(player):
            self.log.write(
                "Only the starting player is allowed to set the number of guesses, {}. The current starting player is {}".format(
                    player, self.startingPlayerTurnOrder.currentPlayer
                )
            )
        elif not self.turnOrder.currentPlayersFirstTurn:
            self.log.write("The number of guesses can only be set on the first guess.")
        elif numGuesses > self.settings.maxNumGuessesInARow:
            self.log.write("A maximum of {} guesses is allowed!".format(self.settings.maxNumGuessesInARow))
        elif numGuesses < self.settings.minNumGuessesInARow + 1:
            self.log.write("A minimum of {} guesses is allowed!".format(self.settings.minNumGuessesInARow))
        else:
            self.resetTurnOrder([numGuesses if player == p else numGuesses + self.settings.punishmentForGuessingInARow for p in self.players])
            self.log.write(
                "Set the number of guesses to {} for {} and to {} for everyone else.".format(
                    numGuesses, player, numGuesses + self.settings.punishmentForGuessingInARow
                )
            )
            self.showCurrentPlayer()

    def handlePlayerGuess(self, player, guessedNumber):
        if not self.turnOrder.isPlayersTurn(player):
            self.log.write("It is not your turn {}".format(player))
        elif guessedNumber > self.function.upperBound:
            self.log.write("Guess a number <= {}".format(self.function.upperBound))
        elif guessedNumber < self.function.lowerBound:
            self.log.write("Guess a number >= {}".format(self.function.lowerBound))
        else:
            self.writeGuess(guessedNumber)
            self.guessedValues.add(guessedNumber)
            if not self.guess(guessedNumber):
                self.nextTurn()
                obviousRoot = self.getFirstObviousRoot()
                if obviousRoot is not None and self.settings.autoPlay:
                    self.printAutoplayMessage()
                    self.handlePlayerGuess(self.turnOrder.currentPlayer, obviousRoot)
                else:
                    self.showRecapOrCurrentPlayer()

    def resetTurnOrder(self, numTurns=None):
        if numTurns is None:
            numTurns = [self.settings.minNumGuessesInARow for _ in self.players]
        self.turnOrder = TurnOrder(self.players, numTurns)
        self.turnOrder.setPlayer(self.startingPlayer)

    def nextTurn(self):
        self.turnOrder.nextTurn()
        if self.newRoundJustStarted():
            self.resetTurnOrder()

    def newRoundJustStarted(self):
        return self.turnOrder.currentPlayer == self.startingPlayer and self.turnOrder.currentPlayersFirstTurn

    @property
    def startingPlayer(self):
        return self.startingPlayerTurnOrder.currentPlayer

    def printAutoplayMessage(self):
        self.log.write("Obvious root detected!")

    def showRecapOrCurrentPlayer(self):
        if self.settings.autoRecap:
            self.recap()
        else:
            self.showCurrentPlayer()

    def getFirstObviousRoot(self):
        sortedX = sorted(list(self.guessedValues))
        for (x1, x2) in zip(sortedX, sortedX[1:]):
            y1 = self.function(x1)
            y2 = self.function(x2)
            yHaveOppositeSigns = y1 * y2 < 0
            if (x1 + 2 == x2) and yHaveOppositeSigns:
                return x1 + 1
        return None

    def guess(self, guessedNumber):
        result = self.function(guessedNumber)
        if result == 0:
            return self.handleGuessedRoot(guessedNumber)
        return False

    def writeGuess(self, guessedNumber):
        result = self.function(guessedNumber)
        self.log.write("{} guessed f({}) = {:,}".format(self.turnOrder.currentPlayer, guessedNumber, result))

    def setStartingPlayer(self):
        startingPlayer = self.startingPlayerTurnOrder.getPlayerAndMakeTurn()
        self.resetTurnOrder()
        self.showCurrentPlayer()

    def showCurrentPlayer(self):
        self.log.write("It's {}'s turn ({} guesses remaining)".format(self.turnOrder.currentPlayer, self.turnOrder.numRemainingGuesses()))

    def playerRecap(self):
        for player in self.players:
            self.log.write("{} guessed {} roots".format(player.name, player.numGuessedRoots))

    def gameIsAlreadyWon(self):
        if len(self.players) == 1:
            return False
        scores = [player.numGuessedRoots for player in self.players]
        highestScore = max(scores)
        # A tie. Game can still be won
        if scores.count(highestScore) > 1:
            return False
        # Otherwise the game is won if the second highest score is at most than the amount of remaining roots away from the highest.
        scores = set(scores)
        scores.remove(highestScore)
        secondHighestScore = max(scores)
        return (
            highestScore - secondHighestScore
            > len(self.function.roots) - sum(player.numGuessedRoots for player in self.players) - self.settings.numRootsToGuessDownTo
        )

    def handleGuessedRoot(self, guessedRoot):
        if guessedRoot in self.rootsToGuess:
            self.log.write("That's a new root!")
            self.rootsToGuess.remove(guessedRoot)
            self.turnOrder.currentPlayer.numGuessedRoots += 1
            self.playerRecap()
            lastRootGuessed = len(self.rootsToGuess) <= self.settings.numRootsToGuessDownTo
            gameAlreadyWon = self.gameIsAlreadyWon()
            if lastRootGuessed or gameAlreadyWon:
                if lastRootGuessed:
                    self.log.write("That was the final root you needed to guess! Let's see who wins")
                elif gameAlreadyWon:
                    self.log.write("Damn, nobody can change the outcome anymore")
                self.handleWonGame()
                return True
        else:
            self.log.write("That's a root but it has already been guessed.")
            return False

    def handleWonGame(self):
        maxScore = max(player.numGuessedRoots for player in self.players)
        winningPlayers = [player for player in self.players if player.numGuessedRoots == maxScore]
        for player in winningPlayers:
            self.log.write("{} WINS HE IS AWESOME WOW".format(player))
            player.score += 1
        self.log.write("Zeroes: {}".format(self.function.roots))
        self.showScore()
        self.setStartingPlayer()
        self.resetFunction()

    def showScore(self):
        self.log.write("The score is: ")
        for player in self.players:
            self.log.write("    {}: {}".format(player, player.score))

    def resetFunction(self):
        self.log.write("Creating a new polynomial with {}-{} roots.".format(self.settings.minNumRoots, self.settings.maxNumRoots))
        self.numRoots = random.randint(self.settings.minNumRoots, self.settings.maxNumRoots)
        self.function = Function(self.numRoots)
        self.rootsToGuess = self.function.roots[:]
        self.guessedValues = set()
        for player in self.players:
            player.numGuessedRoots = 0

    def resetScore(self):
        self.log.write("Resetting the score to 0.")
        for player in self.players:
            player.score = 0

    def recap(self):
        if len(self.guessedValues) > 0:
            numberIndentation = max(len("{:,}".format(self.function(x))) for x in self.guessedValues)
            xIndentation = max(len("{}".format(x)) for x in self.guessedValues)
            # self.log.write("`", newline=False)
            for guessedValue in sorted(list(self.guessedValues)):
                self.log.write(
                    "`f({:<{xIndentation},}) = {:>{numberIndentation},}`".format(
                        guessedValue, self.function(guessedValue), numberIndentation=numberIndentation, xIndentation=xIndentation
                    )
                )
            # self.log.write("```")
        self.showCurrentPlayer()


if __name__ == "__main__":

    class Player:
        def __init__(self, name, id_):
            self.name = name
            self.id = id_

        def __repr__(self):
            return self.name

    p1 = Player("a", 0)
    p2 = Player("b", 1)
    g = Game([p1, p2])
    for i in range(200):
        if i % 2 == 0:
            g.handlePlayerGuess(g.turnOrder.currentPlayer, i // 2)
        else:
            g.handlePlayerGuess(g.turnOrder.currentPlayer, 0)
        # g.recap()
        # g.playerRecap()
        print(g.log.dump())
