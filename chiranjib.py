import pygame
import random
import sys

# Initialize pygame
pygame.init()

# Constants
WINDOW_SIZE = 700
BOARD_SIZE = 600
CELL_SIZE = BOARD_SIZE // 15
OFFSET = (WINDOW_SIZE - BOARD_SIZE) // 2

FPS = 60

# Colors
WHITE       = (255, 255, 255)
BLACK       = (0, 0, 0)
RED         = (220, 50, 50)
GREEN       = (50, 180, 50)
BLUE        = (50, 100, 220)
YELLOW      = (230, 200, 0)
LIGHT_GRAY  = (200, 200, 200)
DARK_GRAY   = (80, 80, 80)
ORANGE      = (255, 165, 0)
BG_COLOR    = (30, 30, 45)

PLAYER_COLORS = [RED, GREEN, BLUE, YELLOW]
PLAYER_NAMES  = ["Red", "Green", "Blue", "Yellow"]

# Safe cells (0-indexed on the 52-cell path)
SAFE_CELLS = {0, 8, 13, 21, 26, 34, 39, 47}

# Each player's starting cell index on the main path (0-indexed)
PLAYER_START = [0, 13, 26, 39]

# Home column entry cell (the cell just before entering home stretch)
HOME_ENTRY = [50, 11, 24, 37]

# Home column path indices (6 cells leading to center)
# These are relative steps after entering home column
HOME_COL_LENGTH = 6

# Board path: list of (row, col) for all 52 cells (15x15 grid)
def build_path():
    """Build the 52-cell outer path as (row, col) grid coordinates."""
    path = []
    # Starting from Red's start going clockwise
    # Top-left quadrant going down then right
    # Red start is at (6, 1)
    
    # Left column going down (rows 6..8, col 1)
    for r in range(6, 9):
        path.append((r, 1))
    # Bottom-left going right (row 8, cols 1..6) -- already have (8,1)
    for c in range(2, 7):
        path.append((8, c))
    # Down left side (rows 9..13, col 6)
    for r in range(9, 14):
        path.append((r, 6))
    # Bottom row going right (row 13, cols 7..8)
    for c in range(7, 9):
        path.append((13, c))
    # Right side of bottom going up (rows 13..9, col 8)
    for r in range(13, 8, -1):
        path.append((r, 8))
    # Right going right bottom (row 8, cols 9..13)
    for c in range(9, 14):
        path.append((8, c))
    # Right column going up (rows 8..6, col 13)
    for r in range(8, 5, -1):
        path.append((r, 13))
    # Top right going left (row 6, cols 13..8)
    for c in range(13, 7, -1):
        path.append((6, c))
    # Top going up (rows 5..1, col 8)
    for r in range(5, 0, -1):
        path.append((r, 8))
    # Top row going left (row 1, cols 8..6)... wait need (1,7) and (1,6)
    for c in range(7, 5, -1):
        path.append((1, c))
    # Left side going down (rows 1..5, col 6)
    for r in range(2, 7):
        path.append((r, 6))
    # Back to (6,1) via row 6 going left -- cols 6..2
    for c in range(5, 0, -1):
        path.append((6, c))

    # Trim/fix to exactly 52
    return path[:52]

PATH = build_path()

# Home column paths for each player (cells from home entry toward center)
def build_home_cols():
    cols = []
    # Red: col 7, rows 7 down to 1 (but home entry from bottom)
    # Red enters at path index 50 -> (6,1) direction, home col goes right
    # Red home: row 7, col 1..6
    red_home = [(7, c) for c in range(1, 7)]
    # Green home: col 7, row 1..6
    green_home = [(r, 7) for r in range(1, 7)]
    # Blue home: row 7, col 13..8
    blue_home = [(7, c) for c in range(13, 7, -1)]
    # Yellow home: col 7, row 13..8
    yellow_home = [(r, 7) for r in range(13, 7, -1)]
    cols = [red_home, green_home, blue_home, yellow_home]
    return cols

HOME_COLS = build_home_cols()

# Base (yard) positions for each player's 4 tokens
BASE_POSITIONS = [
    [(2, 2), (2, 4), (4, 2), (4, 4)],   # Red
    [(2, 10), (2, 12), (4, 10), (4, 12)], # Green
    [(10, 10), (10, 12), (12, 10), (12, 12)], # Blue
    [(10, 2), (10, 4), (12, 2), (12, 4)],   # Yellow
]

class Token:
    def __init__(self, player, idx):
        self.player = player
        self.idx = idx          # token index (0-3)
        self.pos = -1           # -1 = in base, 0-51 = path, 52-57 = home col, 58 = home
        self.finished = False

    def board_cell(self):
        """Return grid (row, col) for current position."""
        if self.pos == -1:
            return BASE_POSITIONS[self.player][self.idx]
        if self.pos == 58:
            return (7, 7)  # center
        if self.pos >= 52:
            home_idx = self.pos - 52
            return HOME_COLS[self.player][home_idx]
        # Main path: adjust for player offset
        path_pos = (self.pos + PLAYER_START[self.player]) % 52
        return PATH[path_pos]

    def can_move(self, dice):
        if self.finished:
            return False
        if self.pos == -1:
            return dice == 6
        remaining = 57 - self.pos  # steps to home (58 = center, but 52+5=57 is last home col)
        return dice <= remaining + 1

def cell_to_pixel(row, col):
    x = OFFSET + col * CELL_SIZE + CELL_SIZE // 2
    y = OFFSET + row * CELL_SIZE + CELL_SIZE // 2
    return (x, y)

def draw_rounded_rect(surface, color, rect, radius=8):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

class LudoGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("🎲 Ludo")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_med   = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 15)
        self.reset()

    def reset(self):
        self.tokens = [[Token(p, i) for i in range(4)] for p in range(4)]
        self.current_player = 0
        self.dice_value = 0
        self.dice_rolled = False
        self.selected_token = None
        self.movable_tokens = []
        self.message = "Red's turn – Roll the dice!"
        self.winner = None
        self.extra_turn = False
        self.game_over = False
        self.animation = None  # (token, start_pixel, end_pixel, progress)

    def roll_dice(self):
        if self.dice_rolled or self.game_over:
            return
        self.dice_value = random.randint(1, 6)
        self.dice_rolled = True
        self.movable_tokens = self.get_movable_tokens()
        name = PLAYER_NAMES[self.current_player]
        if not self.movable_tokens:
            self.message = f"{name} rolled {self.dice_value} – No moves! Next turn."
            pygame.time.set_timer(pygame.USEREVENT, 1200)
        else:
            self.message = f"{name} rolled {self.dice_value} – Choose a token."

    def get_movable_tokens(self):
        movable = []
        for token in self.tokens[self.current_player]:
            if token.can_move(self.dice_value):
                movable.append(token)
        return movable

    def move_token(self, token):
        if token not in self.movable_tokens:
            return
        player = token.player
        dice = self.dice_value

        if token.pos == -1:
            # Move out of base
            token.pos = 0
        else:
            token.pos += dice

        # Check if reached/passed home
        if token.pos >= 58:
            token.pos = 58
            token.finished = True

        # Check for capture on main path (pos 0-51)
        if 0 <= token.pos <= 51:
            abs_cell = (token.pos + PLAYER_START[player]) % 52
            if abs_cell not in SAFE_CELLS:
                for other_p in range(4):
                    if other_p == player:
                        continue
                    for other_tok in self.tokens[other_p]:
                        if other_tok.pos == -1 or other_tok.pos >= 52 or other_tok.finished:
                            continue
                        other_abs = (other_tok.pos + PLAYER_START[other_p]) % 52
                        if other_abs == abs_cell:
                            other_tok.pos = -1  # send home
                            self.message = f"{PLAYER_NAMES[player]} captured {PLAYER_NAMES[other_p]}!"
                            self.extra_turn = True

        # Check win
        if all(t.finished for t in self.tokens[player]):
            self.winner = player
            self.game_over = True
            self.message = f"🎉 {PLAYER_NAMES[player]} WINS! 🎉"
            return

        # Extra turn on 6 or capture
        if dice == 6:
            self.extra_turn = True

        self.dice_rolled = False
        self.selected_token = None
        self.movable_tokens = []

        if self.extra_turn:
            self.extra_turn = False
            self.message = f"{PLAYER_NAMES[player]} gets another turn!"
        else:
            self.next_player()

    def next_player(self):
        self.current_player = (self.current_player + 1) % 4
        self.message = f"{PLAYER_NAMES[self.current_player]}'s turn – Roll the dice!"

    def handle_click(self, pos):
        if self.game_over:
            # Check restart button
            btn_rect = pygame.Rect(WINDOW_SIZE//2 - 70, WINDOW_SIZE - 45, 140, 34)
            if btn_rect.collidepoint(pos):
                self.reset()
            return

        # Check dice button
        dice_rect = pygame.Rect(WINDOW_SIZE//2 - 50, WINDOW_SIZE - 55, 100, 38)
        if dice_rect.collidepoint(pos) and not self.dice_rolled:
            self.roll_dice()
            return

        # Check token clicks
        if self.dice_rolled:
            for token in self.movable_tokens:
                cell = token.board_cell()
                px, py = cell_to_pixel(*cell)
                dist = ((pos[0]-px)**2 + (pos[1]-py)**2)**0.5
                if dist < CELL_SIZE * 0.5:
                    self.move_token(token)
                    return

    # ─── Drawing ────────────────────────────────────────────────

    def draw_board(self):
        s = self.screen
        s.fill(BG_COLOR)

        board_rect = pygame.Rect(OFFSET, OFFSET, BOARD_SIZE, BOARD_SIZE)
        draw_rounded_rect(s, WHITE, board_rect, 12)

        # Draw grid cells
        for r in range(15):
            for c in range(15):
                rect = pygame.Rect(OFFSET + c*CELL_SIZE, OFFSET + r*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = self.get_cell_color(r, c)
                if color:
                    pygame.draw.rect(s, color, rect)
                pygame.draw.rect(s, LIGHT_GRAY, rect, 1)

        # Home triangle arrows (center cross)
        self.draw_home_triangles()

        # Draw safe star markers
        for idx in SAFE_CELLS:
            for p in range(4):
                abs_idx = (idx - PLAYER_START[p]) % 52
                if 0 <= abs_idx < 52:
                    r, c = PATH[(idx) % 52]
                    px, py = cell_to_pixel(r, c)
                    self.draw_star(px, py, 6, WHITE)
                    break

    def get_cell_color(self, r, c):
        # Home yards
        if 1 <= r <= 5 and 1 <= c <= 5:   return (255, 180, 180)  # Red yard
        if 1 <= r <= 5 and 9 <= c <= 13:   return (180, 230, 180)  # Green yard
        if 9 <= r <= 13 and 9 <= c <= 13:  return (180, 180, 255)  # Blue yard
        if 9 <= r <= 13 and 1 <= c <= 5:   return (255, 245, 160)  # Yellow yard
        # Center
        if 6 <= r <= 8 and 6 <= c <= 8:    return (240, 240, 240)
        if r == 7 and c == 7:              return WHITE
        # Home columns
        if r == 7 and 1 <= c <= 5:         return (255, 150, 150)
        if c == 7 and 1 <= r <= 5:         return (150, 220, 150)
        if r == 7 and 9 <= c <= 13:        return (150, 150, 255)
        if c == 7 and 9 <= r <= 13:        return (255, 230, 100)
        # Colored start cells
        if r == 6 and c == 1: return RED
        if r == 1 and c == 8: return GREEN
        if r == 8 and c == 13: return BLUE
        if r == 13 and c == 6: return YELLOW
        return None

    def draw_home_triangles(self):
        cx = OFFSET + 7*CELL_SIZE + CELL_SIZE//2
        cy = OFFSET + 7*CELL_SIZE + CELL_SIZE//2
        half = 3 * CELL_SIZE

        # Red (left)
        pygame.draw.polygon(self.screen, RED,
            [(cx - half, cy - half), (cx - half, cy + half), (cx, cy)])
        # Green (top)
        pygame.draw.polygon(self.screen, GREEN,
            [(cx - half, cy - half), (cx + half, cy - half), (cx, cy)])
        # Blue (right)
        pygame.draw.polygon(self.screen, BLUE,
            [(cx + half, cy - half), (cx + half, cy + half), (cx, cy)])
        # Yellow (bottom)
        pygame.draw.polygon(self.screen, YELLOW,
            [(cx - half, cy + half), (cx + half, cy + half), (cx, cy)])

    def draw_star(self, x, y, size, color):
        import math
        points = []
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            r = size if i % 2 == 0 else size // 2
            points.append((x + r * math.cos(angle), y + r * math.sin(angle)))
        pygame.draw.polygon(self.screen, color, points)

    def draw_tokens(self):
        for p in range(4):
            for token in self.tokens[p]:
                cell = token.board_cell()
                px, py = cell_to_pixel(*cell)
                color = PLAYER_COLORS[p]
                is_movable = token in self.movable_tokens

                # Glow effect for movable tokens
                if is_movable:
                    pygame.draw.circle(self.screen, WHITE, (px, py), CELL_SIZE//2 - 1)

                pygame.draw.circle(self.screen, color, (px, py), CELL_SIZE//2 - 3)
                pygame.draw.circle(self.screen, WHITE, (px, py), CELL_SIZE//2 - 3, 2)

                # Draw token number
                txt = self.font_small.render(str(token.idx+1), True, WHITE)
                self.screen.blit(txt, txt.get_rect(center=(px, py)))

                if token.finished:
                    self.draw_star(px, py-CELL_SIZE//2, 4, ORANGE)

    def draw_dice(self):
        val = self.dice_value
        cx = WINDOW_SIZE // 2
        cy = WINDOW_SIZE - 36

        btn_rect = pygame.Rect(cx - 50, cy - 18, 100, 36)
        btn_color = (70, 130, 70) if not self.dice_rolled and not self.game_over else DARK_GRAY
        draw_rounded_rect(self.screen, btn_color, btn_rect, 10)

        label = f"Roll 🎲" if not self.dice_rolled else f"Rolled: {val}"
        txt = self.font_med.render(label, True, WHITE)
        self.screen.blit(txt, txt.get_rect(center=(cx, cy)))

    def draw_ui(self):
        # Player turn indicator
        for p in range(4):
            x = OFFSET + p * (BOARD_SIZE // 4)
            y = 10
            color = PLAYER_COLORS[p]
            rect = pygame.Rect(x, y, BOARD_SIZE//4 - 4, 28)
            if p == self.current_player and not self.game_over:
                draw_rounded_rect(self.screen, color, rect, 6)
                txt = self.font_small.render(PLAYER_NAMES[p], True, WHITE)
            else:
                draw_rounded_rect(self.screen, DARK_GRAY, rect, 6)
                txt = self.font_small.render(PLAYER_NAMES[p], True, color)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

        # Message bar
        msg_surf = self.font_med.render(self.message, True, WHITE)
        msg_rect = msg_surf.get_rect(center=(WINDOW_SIZE//2, OFFSET + BOARD_SIZE + 18))
        self.screen.blit(msg_surf, msg_rect)

        # Restart button if game over
        if self.game_over:
            btn_rect = pygame.Rect(WINDOW_SIZE//2 - 70, WINDOW_SIZE - 45, 140, 34)
            draw_rounded_rect(self.screen, GREEN, btn_rect, 8)
            txt = self.font_med.render("New Game", True, WHITE)
            self.screen.blit(txt, txt.get_rect(center=btn_rect.center))

    def run(self):
        while True:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.USEREVENT:
                    pygame.time.set_timer(pygame.USEREVENT, 0)
                    if not self.game_over:
                        self.dice_rolled = False
                        self.next_player()

            self.draw_board()
            self.draw_tokens()
            self.draw_ui()
            self.draw_dice()
            pygame.display.flip()

if __name__ == "__main__":
    game = LudoGame()
    game.run()
