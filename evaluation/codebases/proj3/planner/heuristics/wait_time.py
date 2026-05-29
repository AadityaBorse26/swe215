import random
from .base import PriorityHeuristic

class WaitTimeHeuristic(PriorityHeuristic):
    """
    Wait-time urgency heuristic.

    Agents gain priority only when they are stuck/stationary.
    If an agent moves, its wait time resets to 0.
    """
    def __init__(self):
        self.epsilon = {}
        self.wait_time = {}
        self.priority = {}

    def initialize(self, agents, graph=None):
        for agent in agents:
            self.epsilon[agent] = random.random()
            self.wait_time[agent] = 0
            self.priority[agent] = self.epsilon[agent]

    def update(self, agents, paths, goals, t):
        for agent in agents:

            # If agent already reached goal, reset priority
            if paths[agent][t] == goals[agent]:
                self.wait_time[agent] = 0
                self.priority[agent] = self.epsilon[agent]
                continue

            if t == 0:
                self.priority[agent] = self.epsilon[agent]
                continue

            prev_pos = paths[agent][t - 1]
            curr_pos = paths[agent][t]

            # If stationary, increase urgency
            if curr_pos == prev_pos:
                self.wait_time[agent] += 1
            else:
                self.wait_time[agent] = 0

            # Priority is mainly wait time, with epsilon as tie-breaker
            self.priority[agent] = self.wait_time[agent] + self.epsilon[agent]
        return self.priority