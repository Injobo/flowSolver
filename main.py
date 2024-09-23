class GameState:
    def __init__(self, grid, should_add_moat=True):
        self.grid = grid
        self.active_nodes = {}
        self.sources = {}
        self.sinks = {}
        self.colors = set()
        if should_add_moat:
            self.add_moat()
        self.find_nodes(self.grid)


    def find_nodes(self, grid):
        # Search through the grid, find sources and sinks for each color
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] > 0:  # assuming 0 is an empty space and -1 is a wall
                    color = grid[r][c]
                    
                    self.colors.add(color)
                    if color not in self.sources:
                        self.sources[color] = (r, c)  # first node is the source
                        self.active_nodes[color] = (r, c)  # set active node
                    else:
                        self.sinks[color] = (r, c)  # second node is the sink

    def add_moat(self):
        # Expand the grid to add a border (moat) with an unpickable color
        moat_color = -1
        L = len(self.grid)
        W = len(self.grid[0])
        new_grid = [[moat_color] * (W + 2)]
        for row in self.grid:
            new_grid.append([moat_color] + row + [moat_color])
        new_grid.append([moat_color] * (W + 2))
        self.grid = new_grid

    def get_rows(self):
        return len(self.grid)

    def get_cols(self):
        return len(self.grid[0])

    def get_color(self, color):
        # Return the source, sink, and active node for a given color
        return (self.sources[color], self.sinks[color], self.active_nodes[color])

    def get_colors(self):
        # Return the list of colors in the grid (not including the moat color)
        return list(self.colors)
    
    def get_active_colors(self):
        active_colors = set()
        for color in game_state.get_colors():
            source, sink, active = game_state.get_color(color)
            if sink != active:  # if active node is not the sink
                # this means color has not found its way to the sink
                active_colors.add(color)
        return active_colors
    
    def cute_print(self):
        matrix = self.grid
        s = [[str(e) for e in row] for row in matrix]
        lens = [max(map(len, col)) for col in zip(*s)]
        fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
        table = [fmt.format(*row) for row in s]
        print('\n'.join(table))


def is_finished(game_state: GameState):
    # Check if the given game state is complete
    for color in game_state.get_colors():
        source, sink, active = game_state.get_color(color)
        if sink != active:  # if active node is not the sink
            return False
    return True

#TODO this works but is increadibly inefficient and needs to be made more efficient. 
def next_game_states(game_state: GameState):
    # Generate child game states from the current state
    child_states = []
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # right, left, down, up

    for color in game_state.get_active_colors():
        source, sink, active = game_state.get_color(color)
        for direction in directions:
            new_active = (active[0] + direction[0], active[1] + direction[1])

            # Check if the move is valid (inside bounds and not colliding with another path or moat)
            if is_valid_move(new_active, game_state.grid, game_state.active_nodes, color):
                # Create a new game state after making this move
                new_game_state = create_new_game_state(game_state, color, new_active)
                
                # Heuristic: prioritize states that bring the active node closer to the sink
                if distance(new_active, sink) < distance(active, sink):
                    child_states.insert(0, new_game_state)  # More promising moves at the start
                else:
                    child_states.append(new_game_state)

    return child_states


def is_valid_move(pos, grid, active_nodes, color):
    rows, cols = len(grid), len(grid[0])
    r, c = pos
    if 0 <= r < rows and 0 <= c < cols:  # Check if within bounds
        # Allow moves into empty spaces or spaces of the same color
        if grid[r][c] == 0 or grid[r][c] == color:
            # Ensure no other active nodes are occupying the position
            for node_color, node in active_nodes.items():
                if node == pos and node_color != color:
                    return False
            return True
    return False


def distance(pos1, pos2):
    # Calculate Manhattan distance between two positions (row, col)
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def can_be_finished(game_state: GameState):
    # Check if the game state can be completed
    for color in game_state.get_colors():
        source, sink, active = game_state.get_color(color)
        # Perform pathfinding to check if the active node can reach the sink
        if not path_exists(active, sink, game_state.grid):
            return False
    return True


from collections import deque
def path_exists(start, end, grid):
    if start == end:
        return True
    
    rows, cols = len(grid), len(grid[0])
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # right, left, down, up
    visited = set()  # Track visited positions
    queue = deque([start])  # BFS queue initialized with the start node
    
    while queue:
        current = queue.popleft()
        
        if current == end:
            return True  # Path found

        if current in visited:
            continue

        visited.add(current)

        # Explore neighbors
        for direction in directions:
            neighbor = (current[0] + direction[0], current[1] + direction[1])
            if neighbor == end:
                return True  # Path found
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:  # Check bounds
                # Allow moves into empty spaces
                if grid[neighbor[0]][neighbor[1]] == 0:
                    queue.append(neighbor)  # Add valid move to the queue

    return False  # No path found

def find_solution(game_state: GameState):
    # Recursively solve the game state
    print(f"Trying to solve game state with active nodes: {game_state.active_nodes}")
    

    if not can_be_finished(game_state):
        return False
    elif is_finished(game_state):
        game_state.cute_print()
        return True
    else:
        for child in next_game_states(game_state):
            solution = find_solution(child)  # Pass the child state here
            if solution:
                return solution

    return False


def create_new_game_state(game_state: GameState, color, new_active):
    # Create a new game state with the updated active node for the given color
    new_state = GameState([row[:] for row in game_state.grid], False)  # Deep copy the grid
    new_state.sources = game_state.sources.copy()
    new_state.sinks = game_state.sinks.copy()
    new_state.active_nodes = game_state.active_nodes.copy()

    # Update the active node for the specific color
    new_state.active_nodes[color] = new_active

    # Mark the grid to track the path (set grid[r][c] to the color)
    r, c = new_active
    new_state.grid[r][c] = color

    return new_state


# Sample 5x5 grid with two colors (1 and 2)
grid = [
    [1, 0, 2, 0, 0],
    [0, 3, 0, 3, 0],
    [1, 0, 2, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0]
]

game_state = GameState(grid)
solution = find_solution(game_state)
print(f"Solution: {solution}")
