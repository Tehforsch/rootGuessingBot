from types import SimpleNamespace
from util import tryConvertToInt


class GameSettings(SimpleNamespace):
    def __init__(self):
        values = {
            "minNumRoots": 4,
            "maxNumRoots": 9,
            "numRootsToGuessDownTo": 3,
            "minNumGuessesInARow": 1,
            "maxNumGuessesInARow": 4,
            "punishmentForGuessingInARow": 2,
            "autoRecap": True,
            "autoPlay": True,
        }
        super().__init__(**values)
        self.names = list(values.keys())
        self.helpTexts = {
            "minNumRoots": "The minimum number of roots that a new game will be initialized with.",
            "maxNumRoots": "The maximum number of roots that a new game will be initialized with.",
            "numRootsToGuessDownTo": "The number of remaining roots at which the score for the current polynomial is evaluated",
            "minNumGuessesInARow": "The minimum (and default) number of guesses a player has",
            "maxNumGuessesInARow": "The maximum number of guesses the starting player can give himself (by typing #N, where N is the number of guesses).",
            "punishmentForGuessingInARow": "How many more guesses players after the starting player have if the starting player increased his number of guesses in a round",
            "autoRecap": "Whether to show a recap of the game automatically after guessing",
            "autoPlay": "Whether to fill in obvious roots (a single hole between two guessed values that show a sign change) automatically",
        }

    def iterVariables(self):
        for k in self.names:
            yield (k, self.__dict__[k])

    def showHelp(self):
        return "\n".join("{}: {}".format(k, self.helpTexts[k]) for (k, _) in self.iterVariables())

    def set(self, k, vString):
        if not k in self.names:
            return "Parameter does not exist: {}".format(k)
        v = tryConvertToInt(vString)
        if v is None:
            return "Invalid value: {}".format(vString)
        else:
            if type(self.__dict__[k]) == bool:
                v = bool(v)
            self.__dict__[k] = v
            print(self)
            return "Set {} to {}.".format(k, v)
