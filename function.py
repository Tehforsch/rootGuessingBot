import random


class Function:
    def __init__(self, numRoots):
        self.lowerBound = 0
        self.upperBound = 100
        self.roots = sorted([random.randint(self.lowerBound, self.upperBound) for i in range(numRoots)])
        self.prefactor = 1

    def valueWithoutPrefactor(self, x):
        product = 1
        for p in self.roots:
            product *= x - p
        return product

    def __call__(self, x):
        poly = self.valueWithoutPrefactor(x)
        return self.prefactor * poly
