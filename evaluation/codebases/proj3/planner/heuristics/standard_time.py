import random
from .base import PriorityHeuristic

class StandardTimeHeuristic(PriorityHeuristic):

    def __init__(self):
        self.epsilon = {}
        self.priority = {}

    def initialize(self, agents, graph=None):
        used = set()

        for a in agents:
            eps = random.random()

            while eps in used:
                eps = random.random()

            used.add(eps)

            self.epsilon[a] = eps
            self.priority[a] = eps

    def update(self, agents, paths, goals, t):

        for a in agents:
            if paths[a][t] == goals[a]:
                self.priority[a] = self.epsilon[a]
            else:
                self.priority[a] += 1

        return self.priority