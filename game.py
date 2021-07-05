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
            player.numGuessedRoots = 0
        self.minNumRoots = 3
        self.maxNumRoots = 9
        self.numRootsToGuessDownTo = 3
        self.autoRecap = True
        self.log = Log()
        self.log.write("Hello and welcome to this amazing game!")
        self.reset()
        self.startingPlayerTurnOrder = TurnOrder(self.players)
        self.turnOrder = TurnOrder(self.players)
        self.setStartingPlayer()

    def dumpSettings(self):
        self.minNumRoots = 3
        self.maxNumRoots = 9
        self.numRootsToGuessDownTo = 3
        self.autoRecap = True
        result = f"""minNumRoots = {self.minNumRoots}
    maxNumRoots = {self.maxNumRoots}
    numRootsToGuessDownTo = {self.numRootsToGuessDownTo}
    autoRecap = {self.autoRecap}"""
        return "\n".join(line.lstrip() for line in result.split("\n"))

    def handlePlayerGuess(self, player, guessedNumber):
        if not self.turnOrder.isPlayersTurn(player):
            self.log.write("It is not your turn {}".format(player))
            return
        else:
            if guessedNumber > self.function.upperBound:
                self.log.write("Guess a number <= {}".format(self.function.upperBound))
                return
            if guessedNumber < self.function.lowerBound:
                self.log.write("Guess a number >= {}".format(self.function.lowerBound))
                return
            self.guessedValues.add(guessedNumber)
            if not self.guess(guessedNumber):
                self.turnOrder.nextTurn()
                if self.autoRecap:
                    self.recap()
                else:
                    self.showCurrentPlayer()

    def guess(self, guessedNumber):
        result = self.function(guessedNumber)
        self.writeGuess(guessedNumber)
        if result == 0:
            return self.handleGuessedRoot(guessedNumber)
        return False

    def writeGuess(self, guessedNumber):
        result = self.function(guessedNumber)
        self.log.write("{} guessed f({}) = {:,}".format(self.turnOrder.currentPlayer, guessedNumber, result))

    def setStartingPlayer(self):
        startingPlayer = self.startingPlayerTurnOrder.getPlayerAndMakeTurn()
        self.turnOrder.setPlayer(startingPlayer)
        self.showCurrentPlayer()

    def showCurrentPlayer(self):
        self.log.write("It's {}'s turn".format(self.turnOrder.currentPlayer))

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
            highestScore - secondHighestScore > len(self.function.roots) - sum(player.numGuessedRoots for player in self.players) - self.numRootsToGuessDownTo
        )

    def handleGuessedRoot(self, guessedRoot):
        if guessedRoot in self.rootsToGuess:
            self.log.write("That's a new root!")
            self.rootsToGuess.remove(guessedRoot)
            self.turnOrder.currentPlayer.numGuessedRoots += 1
            self.playerRecap()
            lastRootGuessed = len(self.rootsToGuess) <= self.numRootsToGuessDownTo
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
        self.reset()

    def showScore(self):
        self.log.write("The score is: ")
        for player in self.players:
            self.log.write("    {}: {}".format(player, player.score))

    def reset(self):
        self.log.write("Creating a new polynomial with {}-{} roots.".format(self.minNumRoots, self.maxNumRoots))
        self.numRoots = random.randint(self.minNumRoots, self.maxNumRoots)
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


class Function:
    def __init__(self, numRoots):
        self.lowerBound = 0
        self.upperBound = 100
        self.roots = sorted([random.randint(self.lowerBound, self.upperBound) for i in range(numRoots)])
        # # normalize polynomial so number of roots is not as obvious
        # self.prefactor = 1.0 / sum(abs(self.valueWithoutPrefactor(i)) for i in range(self.lowerBound, self.upperBound)) / (self.upperBound - self.lowerBound)
        self.prefactor = 1

    def valueWithoutPrefactor(self, x):
        product = 1
        for p in self.roots:
            product *= x - p
        return product

    def __call__(self, x):
        poly = self.valueWithoutPrefactor(x)
        return self.prefactor * poly


class Log:
    def __init__(self):
        self.content = ""

    def write(self, text, newline=True):
        self.content = self.content + text + ("\n" if newline else "")

    def dump(self):
        buf = self.content
        self.content = ""
        return buf


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
