"""Global constants for the application."""

# GitHub contribution graph dimensions
NUM_WEEKS = 52  # Number of weeks in contribution graph
NUM_DAYS = 7  # Number of days in a week (Sun-Sat)
SHIP_POSITION_Y = NUM_DAYS + 3  # Ship is positioned just below the grid

SHIP_SPEED = 0.25  # Cells per frame the ship moves
BULLET_SPEED = 0.15  # Cells per frame the bullet moves
FRAME_DURATION_MS = 20  # Duration of each frame in milliseconds
SHIP_SHOOT_COOLDOWN_FRAMES = 10  # Frames between ship shots