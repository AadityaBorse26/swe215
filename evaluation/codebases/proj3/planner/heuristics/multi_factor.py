import random
from .base import PriorityHeuristic
from .topology import TopologyHeuristic

class MultiFactorHeuristic(PriorityHeuristic):
    """
    Multi-Factor dynamic priority heuristic.

    Combines:
    1. Wait-time urgency (helps stuck agents escape deadlocks).
    2. Congestion density (prioritizes agents in crowded areas to clear traffic).
    3. Topology criticality (prioritizes agents at bottlenecks/chokepoints).
    """

    def __init__(self, w_wait=1.0, w_congestion=1.0, w_topology=10.0, radius=1):
        self.w_wait = w_wait
        self.w_congestion = w_congestion
        self.w_topology = w_topology
        self.radius = radius

        self.epsilon = {}
        self.wait_time = {}
        self.priority = {}

        # Delegate topology calculation to TopologyHeuristic
        self.topology_heur = TopologyHeuristic(topology_weight=1.0)

    def initialize(self, agents, graph=None):
        for agent in agents:
            self.epsilon[agent] = random.random()
            self.wait_time[agent] = 0
            self.priority[agent] = self.epsilon[agent]

        self.topology_heur.initialize(agents, graph)

    def manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def update(self, agents, paths, goals, t):
        positions = {
            agent: paths[agent][t]
            for agent in agents
        }

        # Step 1: Update wait times for all agents
        for agent in agents:
            if positions[agent] == goals[agent]:
                self.wait_time[agent] = 0
                continue

            if t == 0:
                self.wait_time[agent] = 0
                continue

            prev_pos = paths[agent][t - 1]
            curr_pos = paths[agent][t]

            if curr_pos == prev_pos:
                self.wait_time[agent] += 1
            else:
                self.wait_time[agent] = 0

        # Step 2: Compute priority combining all three factors
        for agent in agents:
            # Agents at goals receive minimal priority
            if positions[agent] == goals[agent]:
                self.priority[agent] = self.epsilon[agent]
                continue

            # 1. Wait factor
            wait_val = self.wait_time[agent]

            # 2. Congestion/Density factor
            local_density = 0
            for other_agent in agents:
                if other_agent == agent:
                    continue
                if self.manhattan(positions[agent], positions[other_agent]) <= self.radius:
                    local_density += 1

            # 3. Topology factor
            node = positions[agent]
            topology_val = self.topology_heur.centrality.get(node, 0.0)

            # Combined Priority formula
            self.priority[agent] = (
                self.w_wait * wait_val
                + self.w_congestion * local_density
                + self.w_topology * topology_val
                + self.epsilon[agent]
            )

        return self.priority
