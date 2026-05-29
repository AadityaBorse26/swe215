class PIBTPlanner:
    def __init__(self, graph, starts, goals, heuristic, max_steps=1000):
        self.graph = graph
        self.starts = starts
        self.goals = goals
        self.agents = list(starts.keys())

        self.heuristic = heuristic
        self.heuristic.initialize(self.agents, self.graph)

        self.max_steps = max_steps
        self.paths = {a: [starts[a]] for a in self.agents}

        # Precompute BFS-based exact shortest path distance maps from each agent's goal
        self.distance_maps = {}
        for a in self.agents:
            self.distance_maps[a] = self._compute_distance_map(self.goals[a])

    def _compute_distance_map(self, goal):
        dist = {goal: 0}
        queue = [goal]
        head = 0
        while head < len(queue):
            curr = queue[head]
            head += 1
            curr_dist = dist[curr]
            for neighbor in self.graph[curr]:
                if neighbor not in dist:
                    dist[neighbor] = curr_dist + 1
                    queue.append(neighbor)
        return dist

    def plan(self):
        t = 0

        while t < self.max_steps:
            if all(self.paths[a][t] == self.goals[a] for a in self.agents):
                break

            priorities = self.heuristic.update(self.agents,self.paths,self.goals,t)
            order = sorted(self.agents, key=lambda a: priorities[a], reverse=True)
            reserved_next = {}
            visited = set()

            for a in order:
                self.ensure_path_length(a, t + 1)
                if self.paths[a][t + 1] is None:
                    self.pibt(a, None, t, reserved_next, visited)

            for a in self.agents:
                self.ensure_path_length(a, t + 1)
                if self.paths[a][t + 1] is None:
                    self.paths[a][t + 1] = self.paths[a][t]
            t += 1
        return self.paths
    
    def pibt(self, ai, parent, t, reserved_next, visited):
        visited.add(ai)
        current = self.paths[ai][t]
        candidates = list(self.graph[current]) + [current]
        candidates.sort(key=lambda node: self.distance(ai, node))

        for v in candidates:
            # vertex conflict
            if v in reserved_next.values():
                continue

            # swap conflict
            if parent is not None and v == self.paths[parent][t]:
                continue

            reserved_next[ai] = v
            self.ensure_path_length(ai, t + 1)
            self.paths[ai][t + 1] = v
            blocker = self.agent_currently_at(v, t)

            if blocker is not None and blocker != ai:
                if blocker not in visited:
                    success = self.pibt(blocker, ai, t, reserved_next, visited)

                    if not success:
                        reserved_next.pop(ai)
                        self.paths[ai][t + 1] = None
                        continue
            return True

        # fallback: wait in place
        self.ensure_path_length(ai, t + 1)
        self.paths[ai][t + 1] = current
        reserved_next[ai] = current
        return False
    
    def finished(self):
        return all(self.paths[a][-1] == self.goals[a] for a in self.agents)
    
    def ensure_path_length(self, agent, index):
        while len(self.paths[agent]) <= index:
            self.paths[agent].append(None)

    def distance(self, agent, node):
        return self.distance_maps[agent].get(node, 999999)

    def agent_currently_at(self, node, t):
        for a in self.agents:
            if self.paths[a][t] == node:
                return a
        return None