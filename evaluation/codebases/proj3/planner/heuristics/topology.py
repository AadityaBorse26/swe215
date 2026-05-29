import random
from .base import PriorityHeuristic

class TopologyHeuristic(PriorityHeuristic):
    """
    Topology-based priority heuristic.

    Agents in areas with high structural bottleneck/chokepoint criticality (e.g., narrow corridors)
    receive higher priority. Criticality is measured using betweenness centrality of nodes.
    """

    def __init__(self, topology_weight=10.0):
        self.topology_weight = topology_weight
        self.epsilon = {}
        self.centrality = {}
        self.priority = {}

    def initialize(self, agents, graph=None):
        # Initialize random tie-breakers so equal priorities do not create deterministic conflicts
        for agent in agents:
            self.epsilon[agent] = random.random()
            self.priority[agent] = self.epsilon[agent]

        # Compute static betweenness centrality for the graph if provided and not already computed
        if graph:
            if not self.centrality:
                self.centrality = self.compute_betweenness_centrality(graph)
        else:
            self.centrality = {}

    def compute_betweenness_centrality(self, graph):
        """
        Brandes' algorithm for fast betweenness centrality in unweighted undirected graphs.
        Time Complexity: O(V * E)
        """
        centrality = {node: 0.0 for node in graph}

        for s in graph:
            # BFS from source s
            S = []
            P = {w: [] for w in graph}
            sigma = {w: 0.0 for w in graph}
            sigma[s] = 1.0
            d = {w: -1 for w in graph}
            d[s] = 0

            queue = [s]
            head = 0
            while head < len(queue):
                v = queue[head]
                head += 1
                S.append(v)
                for w in graph[v]:
                    # Path discovery
                    if d[w] < 0:
                        queue.append(w)
                        d[w] = d[v] + 1
                    # Path counting
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)

            # Accumulate dependency
            delta = {w: 0.0 for w in graph}
            while S:
                w = S.pop()
                for v in P[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
                if w != s:
                    centrality[w] += delta[w]

        # Normalize centrality scores to [0.0, 1.0] for scale independence
        max_c = max(centrality.values()) if centrality else 1.0
        if max_c > 0:
            for node in centrality:
                centrality[node] /= max_c

        return centrality

    def update(self, agents, paths, goals, t):
        positions = {
            agent: paths[agent][t]
            for agent in agents
        }

        for agent in agents:
            # Agents already at their goals receive minimal priority
            if positions[agent] == goals[agent]:
                self.priority[agent] = self.epsilon[agent]
                continue

            node = positions[agent]
            cent = self.centrality.get(node, 0.0)

            # priority = topology_weight * centrality + epsilon tie-breaker
            self.priority[agent] = (
                self.topology_weight * cent
                + self.epsilon[agent]
            )

        return self.priority
