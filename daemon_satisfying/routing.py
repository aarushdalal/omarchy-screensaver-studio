"""Deterministic grid A* routing with reserved occupied cells and union-find spanning connectivity.

Designed for Circuit Weaver procedural trace generation.
"""

from __future__ import annotations

import heapq
import random
from typing import Dict, List, Optional, Set, Tuple

Point = Tuple[int, int]


class UnionFind:
    """Disjoint Set Union (DSU) with path compression and rank optimization."""

    def __init__(self, n: int) -> None:
        self.parent: List[int] = list(range(n))
        self.rank: List[int] = [0] * n
        self.num_components: int = n

    def find(self, i: int) -> int:
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i == root_j:
            return False
        if self.rank[root_i] < self.rank[root_j]:
            self.parent[root_i] = root_j
        elif self.rank[root_i] > self.rank[root_j]:
            self.parent[root_j] = root_i
        else:
            self.parent[root_j] = root_i
            self.rank[root_i] += 1
        self.num_components -= 1
        return True

    def connected(self, i: int, j: int) -> bool:
        return self.find(i) == self.find(j)


def _heuristic(a: Point, b: Point) -> float:
    """Manhattan distance heuristic."""
    return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))


def a_star_search(
    start: Point,
    goal: Point,
    blocked: Set[Point],
    reserved: Set[Point],
    size: int,
) -> Optional[List[Point]]:
    """Deterministic A* pathfinding on a uniform 2D grid with 4-way orthogonal steps.

    Avoids blocked cells, reserved occupied cells, and penalizes turns to produce
    clean, authentic PCB trace geometry.
    """
    if start == goal:
        return [start]

    directions: List[Point] = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    bend_penalty = 0.5

    # Priority queue item: (f_score, h_score, tie_breaker, current_node, current_dir)
    tie_counter = 0
    open_heap: List[Tuple[float, float, int, Point, Optional[Point]]] = []
    h0 = _heuristic(start, goal)
    heapq.heappush(open_heap, (h0, h0, tie_counter, start, None))

    # cost_so_far: (node, direction) -> cost
    cost_so_far: Dict[Tuple[Point, Optional[Point]], float] = {(start, None): 0.0}
    came_from: Dict[Tuple[Point, Optional[Point]], Tuple[Point, Optional[Point]]] = {}

    best_goal_state: Optional[Tuple[Point, Optional[Point]]] = None
    min_goal_cost = float("inf")

    while open_heap:
        f_score, h_score, _, current, cur_dir = heapq.heappop(open_heap)

        if current == goal:
            cur_cost = cost_so_far.get((current, cur_dir), f_score)
            if cur_cost < min_goal_cost:
                min_goal_cost = cur_cost
                best_goal_state = (current, cur_dir)
            break

        current_cost = cost_so_far.get((current, cur_dir), float("inf"))

        for d in directions:
            nxt = (current[0] + d[0], current[1] + d[1])

            # Grid boundary check
            if not (0 <= nxt[0] < size and 0 <= nxt[1] < size):
                continue

            # Obstacle check
            if nxt in blocked:
                continue

            # Reserved occupied cell check (goal is permitted)
            if nxt != goal and nxt in reserved:
                continue

            # Calculate cost with bend penalty
            turn_cost = bend_penalty if (cur_dir is not None and cur_dir != d) else 0.0
            new_cost = current_cost + 1.0 + turn_cost

            state_key = (nxt, d)
            if new_cost < cost_so_far.get(state_key, float("inf")):
                cost_so_far[state_key] = new_cost
                priority = new_cost + _heuristic(nxt, goal)
                tie_counter += 1
                heapq.heappush(open_heap, (priority, _heuristic(nxt, goal), tie_counter, nxt, d))
                came_from[state_key] = (current, cur_dir)

    if best_goal_state is None:
        return None

    # Reconstruct path
    path: List[Point] = []
    curr_state: Optional[Tuple[Point, Optional[Point]]] = best_goal_state
    while curr_state is not None:
        path.append(curr_state[0])
        curr_state = came_from.get(curr_state)

    path.reverse()
    return path


def plan_routes(
    seed: int = 1,
    node_count: int = 12,
    obstacle_density: float = 0.12,
    size: int = 48,
    custom_nodes: Optional[List[List[int]]] = None,
    custom_blocked: Optional[List[List[int]]] = None,
) -> Dict:
    """Plan deterministic circuit routes over a grid using A* and union-find connectivity.

    Args:
        seed: Random seed for deterministic generation.
        node_count: Number of circuit terminal nodes to place.
        obstacle_density: Fraction of grid cells reserved as obstacles (0.0 to 1.0).
        size: Width and height of the square grid.
        custom_nodes: Optional explicit list of [x, y] coordinates for nodes.
        custom_blocked: Optional explicit list of [x, y] coordinates for obstacles.

    Returns:
        JSON-compatible dictionary containing:
            - 'nodes': List of [x, y] node coordinates.
            - 'blocked': List of [x, y] obstacle coordinates.
            - 'paths': List of route metadata dicts with 'from', 'to', 'points', 'distance', 'reveal_start', 'reveal_end'.
            - 'connected': True iff all nodes form a single unified connected component.
            - 'unreachable': List of [x, y] coordinates of nodes that could not be connected.
    """
    rng = random.Random(seed)

    # 1. Obstacle generation
    if custom_blocked is not None:
        blocked_set: Set[Point] = {tuple(p) for p in custom_blocked}  # type: ignore
    else:
        blocked_set = set()
        total_cells = size * size
        target_obstacles = int(total_cells * max(0.0, min(0.8, obstacle_density)))

        # Cluster some obstacles as circuit IC blocks for authentic visual structure
        num_clusters = max(1, target_obstacles // 16)
        for _ in range(num_clusters):
            if len(blocked_set) >= target_obstacles:
                break
            cw = rng.randint(2, 4)
            ch = rng.randint(2, 4)
            cx = rng.randint(1, size - cw - 1)
            cy = rng.randint(1, size - ch - 1)
            for ox in range(cx, cx + cw):
                for oy in range(cy, cy + ch):
                    if len(blocked_set) < target_obstacles:
                        blocked_set.add((ox, oy))

        # Fill remaining obstacle quota with isolated points
        while len(blocked_set) < target_obstacles:
            rx = rng.randint(0, size - 1)
            ry = rng.randint(0, size - 1)
            blocked_set.add((rx, ry))

    # 2. Node placement
    if custom_nodes is not None:
        nodes: List[Point] = [tuple(p) for p in custom_nodes]  # type: ignore
        for pt in nodes:
            blocked_set.discard(pt)
    else:
        nodes = []
        available_cells = [
            (x, y)
            for x in range(2, size - 2)
            for y in range(2, size - 2)
            if (x, y) not in blocked_set
        ]
        rng.shuffle(available_cells)

        min_spacing = 3
        for cell in available_cells:
            if len(nodes) >= node_count:
                break
            if all(abs(cell[0] - n[0]) + abs(cell[1] - n[1]) >= min_spacing for n in nodes):
                nodes.append(cell)

        # Fallback if strict spacing exhausted available cells
        if len(nodes) < node_count:
            for cell in available_cells:
                if len(nodes) >= node_count:
                    break
                if cell not in nodes:
                    nodes.append(cell)

    num_nodes = len(nodes)
    if num_nodes == 0:
        return {
            "nodes": [],
            "blocked": [[x, y] for x, y in sorted(blocked_set)],
            "paths": [],
            "connected": True,
            "unreachable": [],
            "metadata": {"total_distance": 0, "path_count": 0},
        }

    # 3. Spanning connectivity setup
    uf = UnionFind(num_nodes)
    node_set = set(nodes)

    # Candidate edges sorted by Manhattan distance for minimum spanning preference
    candidate_edges: List[Tuple[int, int, int]] = []
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            dist = abs(nodes[i][0] - nodes[j][0]) + abs(nodes[i][1] - nodes[j][1])
            candidate_edges.append((dist, i, j))
    candidate_edges.sort(key=lambda item: (item[0], item[1], item[2]))

    # Reserved cells track occupied path traces
    # Intermediate cells of routed paths cannot be crossed or reused
    reserved_cells: Set[Point] = set()

    paths_data: List[Dict] = []
    cumulative_distance = 0

    for _, u, v in candidate_edges:
        if uf.connected(u, v):
            continue

        # Terminal nodes other than start and goal cannot be traversed
        other_terminals = node_set - {nodes[u], nodes[v]}
        impassable_reserved = reserved_cells | other_terminals

        path = a_star_search(
            start=nodes[u],
            goal=nodes[v],
            blocked=blocked_set,
            reserved=impassable_reserved,
            size=size,
        )

        if path is not None and len(path) >= 2:
            uf.union(u, v)

            # Reserve intermediate cells of this path
            for pt in path[1:-1]:
                reserved_cells.add(pt)

            path_distance = len(path) - 1
            reveal_start = float(cumulative_distance)
            reveal_end = float(cumulative_distance + path_distance)
            cumulative_distance += path_distance

            paths_data.append({
                "from": [nodes[u][0], nodes[u][1]],
                "to": [nodes[v][0], nodes[v][1]],
                "from_index": u,
                "to_index": v,
                "points": [[pt[0], pt[1]] for pt in path],
                "path": [[pt[0], pt[1]] for pt in path],
                "distance": path_distance,
                "reveal_start": reveal_start,
                "reveal_end": reveal_end,
            })

    # 4. Connectivity and Reachability Assessment
    component_map: Dict[int, List[int]] = {}
    for idx in range(num_nodes):
        root = uf.find(idx)
        component_map.setdefault(root, []).append(idx)

    primary_root = max(component_map.keys(), key=lambda r: len(component_map[r]))
    primary_nodes = set(component_map[primary_root])

    unreachable_nodes = [
        [nodes[idx][0], nodes[idx][1]]
        for idx in range(num_nodes)
        if idx not in primary_nodes
    ]

    # Invariant: Must NEVER claim connected if unreachable
    is_connected = (len(unreachable_nodes) == 0 and uf.num_components <= 1)
    if unreachable_nodes:
        is_connected = False

    return {
        "nodes": [[pt[0], pt[1]] for pt in nodes],
        "blocked": [[pt[0], pt[1]] for pt in sorted(blocked_set)],
        "paths": paths_data,
        "connected": is_connected,
        "unreachable": unreachable_nodes,
        "metadata": {
            "seed": seed,
            "size": size,
            "node_count": num_nodes,
            "obstacle_density": obstacle_density,
            "total_distance": cumulative_distance,
            "path_count": len(paths_data),
            "components": uf.num_components,
        },
    }
