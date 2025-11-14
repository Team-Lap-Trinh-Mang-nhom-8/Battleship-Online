import random
from client.misc.utils import make_grid, SHIPS
from client.misc.colors import BLACK


def create_ship_grid(sx=50, ex=400, sy=30, ey=370, color=BLACK):
    """Create a grid and randomly place ships. Returns grid (list of dicts).
    Uses same algorithm as server layout (random orientation, collision checks).
    """
    grid = make_grid(sx, ex, sy, ey, color)
    for name, size in SHIPS.items():
        while True:
            ship_collision = False
            coords = []
            coord1 = random.randint(0, 9)
            coord2 = random.randint(0, 10 - size)

            if random.choice((True, False)):
                x, y = coord1, coord2
                xi, yi = 0, 1
            else:
                x, y = coord2, coord1
                xi, yi = 1, 0

            for i in range(size):
                new_x = x + (xi * i)
                new_y = y + (yi * i)
                if grid[new_x][new_y]["ship"]:
                    ship_collision = True
                    break
                coords.append((new_x, new_y))
            if not ship_collision:
                break
        for bx, by in coords:
            grid[bx][by]["ship"] = name
    return grid


class Bot:
    """Simple bot with random -> hunt/target behaviour.

    Bot stores a list of candidate target cells when it scores a hit.
    """

    def __init__(self, grid=None):
        # bot's own grid (where its ships are placed)
        if grid is None:
            self.grid = create_ship_grid()
        else:
            self.grid = grid
        self.target_mode = False
        self.targets = []

    def choose_move(self, player_grid):
        """Choose a move against player_grid (list of lists of dicts).

        Returns (x_index, y_index).
        Also updates internal targets when it scores a hit.
        """
        rows = len(player_grid)
        cols = len(player_grid[0]) if rows else 0

        # helper to check if a cell is already aimed
        def is_aimed(x, y):
            return player_grid[x][y]["aimed"]

        # Pop valid candidate from targets
        while self.targets:
            tx, ty = self.targets.pop(0)
            if 0 <= tx < rows and 0 <= ty < cols and not is_aimed(tx, ty):
                choice = (tx, ty)
                break
        else:
            # choose random unseen cell
            unseen = [(i, j) for i in range(rows) for j in range(cols) if not is_aimed(i, j)]
            if not unseen:
                return (0, 0)
            choice = random.choice(unseen)

        x, y = choice
        # determine hit
        hit = bool(player_grid[x][y]["ship"])
        if hit:
            # add neighbours to target list (up/down/left/right)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols and not is_aimed(nx, ny):
                    self.targets.append((nx, ny))
        return (x, y)
