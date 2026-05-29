import random
import math
import copy
from itertools import permutations
import time

def dist(c1, c2):
    return abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])

def path_cost(start, seq):
    if not seq:
        return 0
    cost = dist(start, seq[0])
    for i in range(len(seq) - 1):
        cost += dist(seq[i], seq[i+1])
    return cost

def hill_climbing(start, goals, trace=False):
    if not goals:
        return 0, []
    if len(goals) == 1:
        return dist(start, goals[0]), goals
    
    # Start with random ordering
    seq = list(goals)
    # The prompt says: "Start with a random ordering of the given goal cells, for example..."
    # We'll just use the list as it is passed, assuming it's already shuffled or arbitrary.
    
    if trace:
        print(f"Trace for start={start}, goals={goals}")
        print(f"Initial sequence: {seq}, cost: {path_cost(start, seq)}")
        
    while True:
        best_cost = path_cost(start, seq)
        best_seqs = []
        
        # Consider every subsequence of length > 1
        n = len(seq)
        for i in range(n):
            for j in range(i+1, n):
                # Reverse the subsequence seq[i:j+1]
                new_seq = seq[:i] + seq[i:j+1][::-1] + seq[j+1:]
                cost = path_cost(start, new_seq)
                
                if cost < best_cost:
                    best_cost = cost
                    best_seqs = [new_seq]
                elif cost == best_cost and cost < path_cost(start, seq):
                    best_seqs.append(new_seq)
                    
        if best_seqs:
            seq = random.choice(best_seqs)
            if trace:
                print(f"Improved to sequence: {seq}, cost: {best_cost}")
        else:
            if trace:
                print(f"Local minimum reached at sequence: {seq}, cost: {best_cost}")
            break
            
    return path_cost(start, seq), seq

def greedy_hill_climbing(start, goals, trace=False):
    if not goals:
        return 0, []
    if len(goals) == 1:
        return dist(start, goals[0]), goals
        
    # 1. Greedy Nearest Neighbor Initialization
    unvisited = list(goals)
    curr = start
    seq = []
    while unvisited:
        best_goal = None
        best_dist = float('inf')
        for g in unvisited:
            d = dist(curr, g)
            if d < best_dist:
                best_dist = d
                best_goal = g
        seq.append(best_goal)
        unvisited.remove(best_goal)
        curr = best_goal
        
    if trace:
        print(f"Trace for start={start}, goals={goals}")
        print(f"Nearest neighbor initialization: {seq}, cost: {path_cost(start, seq)}")
        
    # 2. Hill Climbing from greedy initialization
    while True:
        best_cost = path_cost(start, seq)
        best_seqs = []
        n = len(seq)
        for i in range(n):
            for j in range(i+1, n):
                new_seq = seq[:i] + seq[i:j+1][::-1] + seq[j+1:]
                cost = path_cost(start, new_seq)
                if cost < best_cost:
                    best_cost = cost
                    best_seqs = [new_seq]
                elif cost == best_cost and cost < path_cost(start, seq):
                    best_seqs.append(new_seq)
                    
        if best_seqs:
            seq = random.choice(best_seqs)
            if trace:
                print(f"Improved to sequence: {seq}, cost: {best_cost}")
        else:
            if trace:
                print(f"Local minimum reached at sequence: {seq}, cost: {best_cost}")
            break
            
    return path_cost(start, seq), seq



def parallel_auction(starts, goals, trace=False):
    assignments = {i: [] for i in range(len(starts))}
    
    for g_idx, g in enumerate(goals):
        best_cost = float('inf')
        best_robots = []
        
        for r_idx, s in enumerate(starts):
            cost = dist(s, g)
            if cost < best_cost:
                best_cost = cost
                best_robots = [r_idx]
            elif cost == best_cost:
                best_robots.append(r_idx)
                
        winner = random.choice(best_robots)
        assignments[winner].append(g)
        if trace:
            print(f"Goal {g} assigned to Robot {winner} with distance {best_cost}")
            
    total_distance = 0
    for r_idx, assigned_goals in assignments.items():
        cost, _ = hill_climbing(starts[r_idx], assigned_goals)
        total_distance += cost
        if trace:
            print(f"Robot {r_idx} assigned goals {assigned_goals}, path cost: {cost}")
            
    return total_distance, assignments

def sequential_auction(starts, goals, trace=False):
    assignments = {i: [] for i in range(len(starts))}
    unassigned_goals = list(goals)
    
    while unassigned_goals:
        best_bid = float('inf')
        best_options = [] # list of (r_idx, g_idx, g, cost, seq)
        
        for g_idx, g in enumerate(unassigned_goals):
            for r_idx, s in enumerate(starts):
                current_cost, _ = hill_climbing(s, assignments[r_idx])
                new_goals = assignments[r_idx] + [g]
                new_cost, new_seq = hill_climbing(s, new_goals)
                marginal_cost = new_cost - current_cost
                
                if marginal_cost < best_bid:
                    best_bid = marginal_cost
                    best_options = [(r_idx, g_idx, g, new_cost, new_seq)]
                elif marginal_cost == best_bid:
                    best_options.append((r_idx, g_idx, g, new_cost, new_seq))
                    
        winner_r_idx, winner_g_idx, winner_g, new_cost, new_seq = random.choice(best_options)
        assignments[winner_r_idx].append(winner_g)
        unassigned_goals.pop(winner_g_idx)
        
        if trace:
            print(f"Goal {winner_g} assigned to Robot {winner_r_idx} with marginal cost {best_bid}")
            
    total_distance = 0
    for r_idx, assigned_goals in assignments.items():
        cost, _ = hill_climbing(starts[r_idx], assigned_goals)
        total_distance += cost
        if trace:
            print(f"Robot {r_idx} assigned goals {assigned_goals}, path cost: {cost}")
            
    return total_distance, assignments

def generate_instance():
    starts = [(random.randint(0, 14), random.randint(0, 14)) for _ in range(10)]
    goals = [(random.randint(0, 14), random.randint(0, 14)) for _ in range(20)]
    return starts, goals

def main():
    random.seed(42)
    num_instances = 100
    instances = [generate_instance() for _ in range(num_instances)]
    
    # 1. Compare Hill Climbing vs Greedy Hill Climbing
    print("--- Algorithm Comparison (100 instances) ---")
    hc_total_distance = 0
    greedy_total_distance = 0
    
    start_time = time.time()
    for starts, goals in instances:
        # evaluate just one robot for baseline comparison
        cost, _ = hill_climbing(starts[0], goals)
        hc_total_distance += cost
    hc_time = time.time() - start_time
    
    start_time = time.time()
    for starts, goals in instances:
        cost, _ = greedy_hill_climbing(starts[0], goals)
        greedy_total_distance += cost
    greedy_time = time.time() - start_time
    
    print(f"Our Algorithm (Random Init Hill Climbing) - Avg Distance: {hc_total_distance / num_instances:.2f}, Time: {hc_time:.4f}s")
    print(f"Your Algorithm (Greedy Init Hill Climbing) - Avg Distance: {greedy_total_distance / num_instances:.2f}, Time: {greedy_time:.4f}s")

    print()
    
    # 2. Parallel vs Sequential Auction
    print("--- Auction Comparison (100 instances) ---")
    total_parallel = 0
    total_sequential = 0
    
    for i, (starts, goals) in enumerate(instances):
        p_cost, _ = parallel_auction(starts, goals)
        s_cost, _ = sequential_auction(starts, goals)
        total_parallel += p_cost
        total_sequential += s_cost
        
    print(f"Average Parallel Auction Distance: {total_parallel / num_instances}")
    print(f"Average Sequential Auction Distance: {total_sequential / num_instances}")

if __name__ == "__main__":
    main()
