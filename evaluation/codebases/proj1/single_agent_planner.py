import heapq

def move(loc, dir):
    # Directions: up, right, down, left, wait (Task 1.1: added wait action)
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)]
    return loc[0] + directions[dir][0], loc[1] + directions[dir][1]


def get_sum_of_cost(paths):
    rst = 0
    for path in paths:
        rst += len(path) - 1
    return rst


def compute_heuristics(my_map, goal):
    # Use Dijkstra to build a shortest-path tree rooted at the goal location
    open_list = []
    closed_list = dict()
    root = {'loc': goal, 'cost': 0}
    heapq.heappush(open_list, (root['cost'], goal, root))
    closed_list[goal] = root
    while len(open_list) > 0:
        (cost, loc, curr) = heapq.heappop(open_list)
        for dir in range(4):
            child_loc = move(loc, dir)
            child_cost = cost + 1
            if child_loc[0] < 0 or child_loc[0] >= len(my_map) \
               or child_loc[1] < 0 or child_loc[1] >= len(my_map[0]):
               continue
            if my_map[child_loc[0]][child_loc[1]]:
                continue
            child = {'loc': child_loc, 'cost': child_cost}
            if child_loc in closed_list:
                existing_node = closed_list[child_loc]
                if existing_node['cost'] > child_cost:
                    closed_list[child_loc] = child
                    # open_list.delete((existing_node['cost'], existing_node['loc'], existing_node))
                    heapq.heappush(open_list, (child_cost, child_loc, child))
            else:
                closed_list[child_loc] = child
                heapq.heappush(open_list, (child_cost, child_loc, child))

    # build the heuristics table
    h_values = dict()
    for loc, node in closed_list.items():
        h_values[loc] = node['cost']
    return h_values


def build_constraint_table(constraints, agent):
    """Build a lookup table of constraints indexed by timestep for the given agent.
    
    Task 1.2/1.3: Filters all constraints to only those belonging to 'agent',
    then groups them by timestep for O(1) lookup during A* expansion.
    Returns: dict mapping timestep -> list of constraint dicts for that timestep.
    """
    constraint_table = {}
    for constraint in constraints:
        if constraint['agent'] == agent:
            timestep = constraint['timestep']
            if timestep not in constraint_table:
                constraint_table[timestep] = []
            constraint_table[timestep].append(constraint)
    return constraint_table


def get_location(path, time):
    if time < 0:
        return path[0]
    elif time < len(path):
        return path[time]
    else:
        return path[-1]  # wait at the goal location


def get_path(goal_node):
    path = []
    curr = goal_node
    while curr is not None:
        path.append(curr['loc'])
        curr = curr['parent']
    path.reverse()
    return path


def is_constrained(curr_loc, next_loc, next_time, constraint_table):
    """Check if moving from curr_loc to next_loc at next_time violates any constraint.
    
    Task 1.2: Vertex constraints have loc = [(x,y)] — the agent cannot be at (x,y)
              at the given timestep.
    Task 1.3: Edge constraints have loc = [(x1,y1), (x2,y2)] — the agent cannot move
              from (x1,y1) to (x2,y2) at the given timestep.
    Returns True if the move is constrained (should be pruned).
    """
    if next_time in constraint_table:
        for constraint in constraint_table[next_time]:
            if len(constraint['loc']) == 1:
                # Vertex constraint: agent cannot occupy this cell at this time
                if constraint['loc'][0] == next_loc:
                    return True
            else:
                # Edge constraint: agent cannot traverse this edge at this time
                if constraint['loc'][0] == curr_loc and constraint['loc'][1] == next_loc:
                    return True
    return False


def push_node(open_list, node):
    heapq.heappush(open_list, (node['g_val'] + node['h_val'], node['h_val'], node['loc'], node))


def pop_node(open_list):
    _, _, _, curr = heapq.heappop(open_list)
    return curr


def compare_nodes(n1, n2):
    """Return true is n1 is better than n2."""
    return n1['g_val'] + n1['h_val'] < n2['g_val'] + n2['h_val']


def a_star(my_map, start_loc, goal_loc, h_values, agent, constraints):
    """ my_map      - binary obstacle map
        start_loc   - start position
        goal_loc    - goal position
        agent       - the agent that is being re-planned
        constraints - constraints defining where robot should or cannot go at each timestep
    """

    ##############################
    # Task 1.1: Extend A* to search in the space-time domain.
    #   - Each node now includes a 'timestep' key (root starts at 0, children increment by 1)
    #   - closed_list is indexed by (cell, timestep) tuples instead of just cell
    #   - We generate a 5th child for each node where the agent waits in place (dir=4)

    open_list = []
    closed_list = dict()
    earliest_goal_timestep = 0
    h_value = h_values[start_loc]

    # Pre-process constraints into a table indexed by timestep for O(1) lookup
    constraint_table = build_constraint_table(constraints, agent)

    # Task 1.4: The agent must not declare "goal reached" if there are future vertex
    # constraints on the goal cell. Find the latest such constraint and require the
    # agent to arrive strictly after it. This prevents the agent from "arriving" at
    # the goal and then being in violation at a later constrained timestep.
    for timestep, constraint_list in constraint_table.items():
        for constraint in constraint_list:
            if len(constraint['loc']) == 1 and constraint['loc'][0] == goal_loc:
                earliest_goal_timestep = max(earliest_goal_timestep, timestep + 1)

    # Task 2.4: Compute an upper bound on the search depth to prevent infinite loops.
    # The longest possible shortest path is bounded by the grid size plus any
    # constraint-imposed delays.
    max_timestep = 0
    for constraint in constraints:
        if constraint['timestep'] > max_timestep:
            max_timestep = constraint['timestep']
    upper_bound = max(max_timestep + 1, len(my_map) * len(my_map[0])) + len(my_map) * len(my_map[0])

    # Task 1.1: Root node now includes timestep=0
    root = {'loc': start_loc, 'g_val': 0, 'h_val': h_value, 'parent': None, 'timestep': 0}
    push_node(open_list, root)
    # Task 1.1: closed_list indexed by (cell, timestep) for space-time search
    closed_list[(root['loc'], 0)] = root
    while len(open_list) > 0:
        curr = pop_node(open_list)
        # Task 1.4: Only accept the goal if we are past all goal-location constraints
        if curr['loc'] == goal_loc and curr['timestep'] >= earliest_goal_timestep:
            return get_path(curr)

        # Prevent infinite loops
        if curr['timestep'] >= upper_bound:
            continue

        # Task 1.1: 5 actions — 4 cardinal moves + 1 wait action
        for dir in range(5):
            child_loc = move(curr['loc'], dir)
            # Check bounds
            if child_loc[0] < 0 or child_loc[0] >= len(my_map) \
               or child_loc[1] < 0 or child_loc[1] >= len(my_map[0]):
                continue
            if my_map[child_loc[0]][child_loc[1]]:
                continue
            child = {'loc': child_loc,
                    'g_val': curr['g_val'] + 1,
                    'h_val': h_values[child_loc],
                    'parent': curr,
                    'timestep': curr['timestep'] + 1}

            # Check constraints
            if is_constrained(curr['loc'], child['loc'], child['timestep'], constraint_table):
                continue

            if (child['loc'], child['timestep']) in closed_list:
                existing_node = closed_list[(child['loc'], child['timestep'])]
                if compare_nodes(child, existing_node):
                    closed_list[(child['loc'], child['timestep'])] = child
                    push_node(open_list, child)
            else:
                closed_list[(child['loc'], child['timestep'])] = child
                push_node(open_list, child)

    return None  # Failed to find solutions
