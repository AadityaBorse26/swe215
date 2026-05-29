import heapq
import random
import time
from planner.heuristics.base import PriorityHeuristic

class LaCAMPlanner:
    """
    LaCAM (Lazy Constraint Addition for MAPF) Planner.

    Combines global heuristic search in the joint configuration space with
    PIBT as a one-step transition generator.
    Employs lazy constraint addition to avoid visited configurations and escape deadlocks.
    """

    def __init__(self, graph, starts, goals, heuristic, max_steps=1000, max_nodes=1000):
        self.graph = graph
        self.starts = starts
        self.goals = goals
        self.agents = list(starts.keys())

        self.heuristic = heuristic
        self.heuristic.initialize(self.agents, self.graph)

        self.max_steps = max_steps
        self.max_nodes = max_nodes

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

    def distance(self, agent, node):
        return self.distance_maps[agent].get(node, 999999)

    def get_heuristic_val(self, state):
        return sum(self.distance(a, state[a]) for a in self.agents)

    def pibt_step(self, curr_node, constraints):
        """
        Runs one step of PIBT from the given joint search node 'curr_node'
        subject to 'constraints' (set of (agent, position) tuples).
        Reconstructs the path history from the start node to restore correct heuristic states.
        """
        # Reconstruct path history from start to curr_node
        path_nodes = []
        curr = curr_node
        while curr:
            path_nodes.append(curr.state)
            curr = curr.parent
        path_nodes.reverse()

        t = curr_node.g
        # paths: {agent: [pos0, pos1, ..., pos_t, None]}
        paths = {a: [] for a in self.agents}
        for s in path_nodes:
            for a in self.agents:
                paths[a].append(s[a])
        for a in self.agents:
            paths[a].append(None)

        state = curr_node.state

        # Reset heuristic and replay chronological updates along the path history to reconstruct the correct state
        self.heuristic.initialize(self.agents, self.graph)
        priorities = {}
        for step_t in range(t + 1):
            priorities = self.heuristic.update(self.agents, paths, self.goals, step_t)

        # Sort agents by reconstructed priorities
        order = sorted(self.agents, key=lambda a: priorities[a], reverse=True)

        reserved_next = {}
        visited = set()

        def pibt_rec(ai, parent):
            visited.add(ai)
            curr_pos = state[ai]
            candidates = list(self.graph[curr_pos]) + [curr_pos]

            # Filter candidates by single-agent constraints
            candidates = [v for v in candidates if (ai, v) not in constraints]

            # Sort by distance to goal
            candidates.sort(key=lambda node: self.distance(ai, node))

            for v in candidates:
                # Vertex conflict
                if v in reserved_next.values():
                    continue

                # Swap conflict
                if parent is not None and v == state[parent]:
                    continue

                reserved_next[ai] = v
                paths[ai][t + 1] = v

                # Find if any agent currently occupies v
                blocker = None
                for other in self.agents:
                    if other != ai and state[other] == v:
                        blocker = other
                        break

                if blocker is not None:
                    if blocker not in visited:
                        success = pibt_rec(blocker, ai)
                        if not success:
                            reserved_next.pop(ai)
                            paths[ai][t + 1] = None
                            continue
                return True

            # Fallback: wait in place if allowed
            if (ai, curr_pos) not in constraints:
                paths[ai][t + 1] = curr_pos
                reserved_next[ai] = curr_pos
                return False
            return False

        for a in order:
            if paths[a][t + 1] is None:
                pibt_rec(a, None)

        # Ensure all agents have a valid position (fallback to wait in place if not resolved)
        for a in self.agents:
            if paths[a][t + 1] is None:
                if (a, state[a]) not in constraints:
                    paths[a][t + 1] = state[a]
                else:
                    return None  # Constraint violation: failed to find a valid move

        return {a: paths[a][t + 1] for a in self.agents}

    def plan(self):
        start_state = {a: self.starts[a] for a in self.agents}
        goal_state = {a: self.goals[a] for a in self.agents}

        start_config = tuple(start_state[a] for a in self.agents)
        goal_config = tuple(goal_state[a] for a in self.agents)

        if start_config == goal_config:
            return {a: [self.starts[a]] for a in self.agents}

        planner = self
        node_id_counter = 0
        class Node:
            def __init__(self, state, g, h, parent=None):
                nonlocal node_id_counter
                self.id = node_id_counter
                node_id_counter += 1
                self.state = state
                self.config = tuple(state[a] for a in planner.agents)
                self.g = g
                self.h = h
                self.f = g + h
                self.parent = parent
                self.constraints = set()  # set of (agent, pos)
                self.expanded_count = 0

            def __lt__(self, other):
                if self.f == other.f:
                    return self.id < other.id
                return self.f < other.f

        open_list = []
        start_node = Node(start_state, g=0, h=self.get_heuristic_val(start_state))
        heapq.heappush(open_list, start_node)

        visited = {start_config: start_node}
        nodes_count = 0

        start_time = time.perf_counter()
        success = False
        end_node = None

        while open_list and nodes_count < self.max_nodes:
            # 0.2-second hard time limit to prevent benchmark hangs
            if time.perf_counter() - start_time > 0.2:
                break

            curr_node = heapq.heappop(open_list)
            nodes_count += 1

            if curr_node.config == goal_config:
                success = True
                end_node = curr_node
                break

            # Branching factor: try to generate up to 5 alternative successors
            for branch in range(5):
                next_state = self.pibt_step(curr_node, curr_node.constraints)
                if next_state is None:
                    # PIBT failed under these constraints
                    break

                next_config = tuple(next_state[a] for a in self.agents)

                if next_config not in visited:
                    next_h = self.get_heuristic_val(next_state)
                    next_node = Node(next_state, g=curr_node.g + 1, h=next_h, parent=curr_node)
                    visited[next_config] = next_node
                    heapq.heappush(open_list, next_node)

                    # Re-enqueue the parent to allow further branching later (up to 5 branches)
                    curr_node.expanded_count += 1
                    if curr_node.expanded_count < 5:
                        heapq.heappush(open_list, curr_node)
                    break
                else:
                    # Joint state is already visited. Add a constraint to force alternative branching.
                    # Restrict one agent that moved from changing its position.
                    moved_agents = [
                        a for a in self.agents
                        if next_state[a] != curr_node.state[a]
                    ]
                    if moved_agents:
                        agent_to_constrain = random.choice(moved_agents)
                        curr_node.constraints.add((agent_to_constrain, next_state[agent_to_constrain]))
                    else:
                        break

        # Reconstruct path
        if success and end_node:
            path_nodes = []
            curr = end_node
            while curr:
                path_nodes.append(curr.state)
                curr = curr.parent
            path_nodes.reverse()

            paths = {a: [] for a in self.agents}
            for state in path_nodes:
                for a in self.agents:
                    paths[a].append(state[a])
            return paths
        else:
            # Fallback: return static wait-in-place paths
            return {a: [self.starts[a]] * self.max_steps for a in self.agents}
