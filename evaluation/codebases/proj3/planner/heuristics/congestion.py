import random
from .base import PriorityHeuristic


class CongestionHeuristic(PriorityHeuristic):
    """
    Congestion-based priority heuristic.

    Agents in crowded local neighborhoods receive higher priority.
    Local density is measured using Manhattan distance.
    """

    def __init__(self, radius=1, congestion_weight=1.0):
        self.radius = radius
        self.congestion_weight = congestion_weight

        self.epsilon = {}
        self.priority = {}

    def initialize(self, agents, graph=None):
        for agent in agents:
            # Random tie-breaker so equal priorities
            # do not create deterministic conflicts
            self.epsilon[agent] = random.random()
            self.priority[agent] = self.epsilon[agent]

    def manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def update(self, agents, paths, goals, t):
        positions = {
            agent: paths[agent][t]
            for agent in agents
        }

        for agent in agents:
            # Agents already at goals receive minimal priority
            if positions[agent] == goals[agent]:
                self.priority[agent] = self.epsilon[agent]
                continue

            local_density = 0

            for other_agent in agents:
                if other_agent == agent:
                    continue

                # Count nearby agents within congestion radius
                if self.manhattan(positions[agent], positions[other_agent]) <= self.radius:
                    local_density += 1

            
            # Agents inside crowded regions are prioritized to clear traffic-heavy areas first.
            # priority = congestion_weight * local_density + epsilon tie-breaker
            self.priority[agent] = (
                self.congestion_weight * local_density
                + self.epsilon[agent]
            )
        return self.priority