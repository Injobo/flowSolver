directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # right, left, down, up

def get_neighbors(coord):
    neighbors = []
    for direction in directions:
        neighbor = (coord[0] + direction[0], coord[1] + direction[1])
        neighbors.append(neighbor)
    return neighbors
    
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
        for color in self.get_colors():
            source, sink, active = self.get_color(color)
            get_neighbors(active)
            for direction in directions:
                new_active = (active[0] + direction[0], active[1] + direction[1])
                if new_active == sink:
                    active = sink
            if sink != active:  # if active node is not the sink
                # this means color has not found its way to the sink
                active_colors.add(color)
        return active_colors

    def color_code(self, value):
        """Return the ANSI escape code for the color based on the value."""
        # List of ANSI color codes
        color_map = [
            "\033[91m",  # Red for negative numbers
            "\033[0m",   # Default color for zero
            "\033[32m",  # Green
            "\033[33m",  # Yellow
            "\033[34m",  # Blue
            "\033[35m",  # Magenta
            "\033[36m",  # Cyan
            "\033[93m",  # Bright Yellow
            "\033[94m",  # Bright Blue
            "\033[95m",  # Bright Magenta
            "\033[96m",  # Bright Cyan
            "\033[92m"   # Bright Green for higher numbers
        ]
    
        # Use the value to index into the color_map
        if value < 0:
            return color_map[0]  # Red
        elif value >= 0 and value < len(color_map):
            return color_map[value + 1]  # Adjust index for zero-based
        else:
            return color_map[-1]  # Default to Bright Green for values beyond the defined range

    def cute_print(self):
        matrix = self.grid
        table = []
        
        for row in matrix:
            colored_row = [f"{self.color_code(e)}\u2588\u2588\033[0m" for e in row]  # Block character
            table.append("".join(colored_row))

        print('\n'.join(table))


def is_finished(game_state: GameState):
    # Check if the given game state is complete
    # if len(game_state.get_active_colors()) <= 0:
    #     return True
    # else:
    #     return False
    
    for color in game_state.get_colors():
        _, sink, active = game_state.get_color(color)
        if sink != active and (active not in get_neighbors(sink)):  # if active node is not the sink
            return False
    return True


def get_children(game_state, color):
    # given a game_state and a color return the children of the gamestate where that color has made all possible moves
    _, _, active = game_state.get_color(color)
    answer = []
    for neighbor in get_neighbors(active):
        if is_valid_move(neighbor, game_state.grid, game_state.active_nodes, color):
            passing_state = create_new_game_state(game_state, color, neighbor)
            answer.append(passing_state)
    return answer

def next_game_states(game_state: GameState):
    colors = game_state.get_active_colors()
    draining_stack = [game_state]
    accumulating_stack = []
    while len(colors) > 0:
        curr_color = colors.pop()
        while draining_stack:
            curr_state = draining_stack.pop()
            accumulating_stack.extend(get_children(curr_state, curr_color))
        if len(colors) > 0:
            # we popped the last color and dont want to clear out the accumulating_stack
            draining_stack = accumulating_stack.copy()
            accumulating_stack = []
    
    filtered_final_states = []
    for final_state in accumulating_stack:
        if can_be_finished(final_state):
            if final_state in filtered_final_states:
                print("error duplicate final_states found, your code is fucked")
                exit
            filtered_final_states.append(final_state)
    return filtered_final_states





def is_valid_move(pos, grid, active_nodes, color):
    rows, cols = len(grid), len(grid[0])
    r, c = pos
    if 0 <= r < rows and 0 <= c < cols:  # Check if within bounds
        # Allow moves into empty spaces
        if grid[r][c] == 0:
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


def copy_game_state(game_state: GameState):
    # Create a new game state with the updated active node for the given color
    new_state = GameState([row[:] for row in game_state.grid], False)  # Deep copy the grid
    new_state.sources = game_state.sources.copy()
    new_state.sinks = game_state.sinks.copy()
    new_state.active_nodes = game_state.active_nodes.copy()
    return new_state


def create_new_game_state(game_state: GameState, color, new_active):
    # Create a new game state with the updated active node for the given color
    new_state = copy_game_state(game_state)


    # Update the active node for the specific color
    new_state.active_nodes[color] = new_active

    # Mark the grid to track the path (set grid[r][c] to the color)
    r, c = new_active
    new_state.grid[r][c] = color

    return new_state


def find_solution(game_state: GameState):
    # Stack to store game states to process (initially containing the input game state)
    stack = [game_state]
    print("solving:")
    game_state.cute_print()

    i = 0
    while (stack):
        i += 1
        # if (i == 2):
        #     print("checkpoint")

        current_state = stack[0]
        if (i % 100 == 0):
            print(i)
            current_state.cute_print()

        stack = stack[1:]
        #print(f"Trying to solve game state with active nodes: {current_state.active_nodes}")

        # Check if the current state can be finished
        if not can_be_finished(current_state):
            print("no finish")
            continue

        # Check if the current state is a finished solution
        if is_finished(current_state):
            print("solution is:")
            current_state.cute_print()  # Print the finished state
            return True

        # If not finished, add the next possible game states to the stack
        saved_statess = next_game_states(current_state)
        # print("children")
        # for thing in saved_statess:
        #     thing.cute_print()
        stack = saved_statess + stack

    # Return False if no solution was found after processing all states
    return False

# sample 10 x 10 grid
# grid = [
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
#     [0, 2, 1, 0, 0, 0, 0, 0, 2, 0],
#     [0, 6, 0, 0, 0, 5, 4, 0, 3, 0],
#     [0, 0, 0, 0, 0, 7, 0, 0, 0, 0],
#     [0, 0, 8, 4, 7, 0, 0, 0, 0, 0],
#     [0, 0, 0, 0, 0, 0, 0, 0, 0, 9],
#     [0, 5, 0, 6, 0, 0, 0, 0, 0, 3],
#     [0, 9, 0, 0, 0, 0, 0, 0, 0, 8],
# ]

# Sample 8x8 grid
grid = [
    [1, 0, 0, 1, 2, 0, 0, 0],
    [0, 0, 3, 4, 5, 0, 5, 0],
    [0, 0, 6, 0, 0, 0, 0, 0],
    [0, 0, 7, 0, 8, 9, 0, 0],
    [0, 0, 0, 0, 4, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0, 0],
    [0, 6, 0, 7, 0, 0, 8, 2],
    [0, 0, 0, 0, 0, 0, 0, 9],
]

# Sample 5x5 grid with two colors (1 and 2)
# grid = [
#     [0, 0, 0, 0, 0, 1],
#     [0, 0, 0, 0, 0, 0],
#     [0, 2, 3, 0, 0, 0],
#     [0, 0, 0, 4, 0, 2],
#     [0, 4, 0, 1, 3, 5],
#     [0, 0, 0, 5, 0, 0],
# ]

# grid = [
#     [1, 0, 2],
#     [0, 0, 0],
#     [1, 0, 2]
# ]



game_state = GameState(grid)
solution = find_solution(game_state)
print(f"Solution: {solution}")