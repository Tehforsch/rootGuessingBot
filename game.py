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
        self.minNumRoots = 2
        self.maxNumRoots = 6
        self.numRootsToGuessDownTo = 2
        self.log = Log()
        self.log.write("Hello and welcome to this amazing game!")
        self.reset()
        self.startingPlayerTurnOrder = TurnOrder(self.players)
        self.turnOrder = TurnOrder(self.players)
        self.setStartingPlayer()

    def handlePlayerGuess(self, player, guessedNumber):
        self.guessedValues.add(guessedNumber)
        if not self.turnOrder.isPlayersTurn(player):
            self.log.write("It is not your turn {}".format(player))
            return
        else:
            if not self.guess(guessedNumber):
                self.turnOrder.nextTurn()
                self.showCurrentPlayer()

    def guess(self, guessedNumber):
        result = self.function(guessedNumber)
        self.log.write("{} guessed. f({}) = {:,}".format(self.turnOrder.currentPlayer, guessedNumber, result))
        if result == 0:
            return self.handleGuessedRoot(guessedNumber)
        return False

    def setStartingPlayer(self):
        startingPlayer = self.startingPlayerTurnOrder.getPlayerAndMakeTurn()
        self.turnOrder.setPlayer(startingPlayer)
        self.showCurrentPlayer()

    def showCurrentPlayer(self):
        self.log.write("It's {}'s turn".format(self.turnOrder.currentPlayer))

    def playerRecap(self):
        for player in self.players:
            self.log.write("{} guessed {} roots so far".format(player.name, player.numGuessedRoots))

    def handleGuessedRoot(self, guessedRoot):
        if guessedRoot in self.rootsToGuess:
            self.log.write("That's a new root!")
            self.rootsToGuess.remove(guessedRoot)
            self.turnOrder.currentPlayer.numGuessedRoots += 1
            self.playerRecap()
            if len(self.rootsToGuess) == self.numRootsToGuessDownTo:
                self.log.write("That was the final root needed to guess! Let's see who wins")
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
        self.log.write("The score is: ")
        for player in self.players:
            self.log.write("    {}: {}".format(player, player.score))
        self.setStartingPlayer()
        self.reset()

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
        for guessedValue in sorted(list(self.guessedValues)):
            self.log.write("f({}) = {:,}".format(guessedValue, self.function(guessedValue)))

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
            product *= (x - p)
        return product

    def __call__(self, x):
        poly = self.valueWithoutPrefactor(x)
        return self.prefactor * poly

class Log:
    def __init__(self):
        self.content = ""

    def write(self, text):
        self.content = self.content + text + "\n"

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
    for i in range(100):
        g.handlePlayerGuess(g.turnOrder.currentPlayer, i)
        g.recap()
        g.playerRecap()
        print(g.log.dump())
        

