"""Game state management for tracking enemies, ship, and bullets."""

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from PIL import ImageDraw

from ..constants import BULLET_SPEED, NUM_DAYS, NUM_WEEKS, SHIP_POSITION_Y, SHIP_SHOOT_COOLDOWN_FRAMES, SHIP_SPEED
from ..github_client import ContributionData

if TYPE_CHECKING:
    from .render_context import RenderContext

class Drawable(ABC):
    """Interface for objects that can be animated and drawn."""

    @abstractmethod
    def animate(self) -> None:
        """Update the object's state for the next animation frame."""
        pass

    @abstractmethod
    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """
        Draw the object on the image.

        Args:
            draw: PIL ImageDraw object
            context: Rendering context with helper functions and constants
        """
        pass


class Starfield(Drawable):
    """Animated starfield background with slowly moving stars."""

    def __init__(self):
        """Initialize the starfield with random stars."""
        self.stars = []
        # Generate about 100 stars across the play area
        for _ in range(100):
            # Random position across the entire grid area
            x = random.uniform(-2, NUM_WEEKS + 2)
            y = random.uniform(-2, SHIP_POSITION_Y + 4)
            # Brightness: 0.2 to 1.0 (dimmer stars for depth)
            brightness = random.uniform(0.2, 1.0)
            # Size: 1-2 pixels
            size = random.choice([1, 1, 1, 2])  # More 1-pixel stars
            # Speed: slower for dimmer (farther) stars
            speed = 0.02 + (brightness * 0.03)  # 0.02-0.05 cells per frame
            self.stars.append([x, y, brightness, size, speed])

    def animate(self) -> None:
        """Move stars downward, wrapping around when they go off screen."""
        for star in self.stars:
            # star[1] is the y position, star[4] is the speed
            star[1] += star[4]

            # Wrap around: if star goes below the screen, move it back to the top
            if star[1] > SHIP_POSITION_Y + 4:
                star[1] = -2
                # Randomize x position when wrapping for variety
                star[0] = random.uniform(-2, NUM_WEEKS + 2)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw all stars at their current positions."""
        for star_x, star_y, brightness, size, _ in self.stars:
            # Convert grid position to pixel position
            x, y = context.get_cell_position(star_x, star_y)

            # Calculate star color (white with varying brightness)
            star_brightness = int(255 * brightness)
            star_color = (star_brightness, star_brightness, star_brightness, 255)

            # Draw star as a small rectangle or point
            if size == 1:
                # Single pixel star
                draw.point([(x, y)], fill=star_color)
            else:
                # Slightly larger star (2x2)
                draw.rectangle(
                    [x, y, x + size - 1, y + size - 1],
                    fill=star_color
                )


class Explosion(Drawable):
    """Particle explosion effect that expands and fades out."""

    def __init__(self, x: float, y: float, size: str, color: tuple, game_state: "GameState"):
        """
        Initialize an explosion.

        Args:
            x: X position (week, 0-51)
            y: Y position (day, 0-6)
            size: "small" for bullet hits, "large" for enemy destruction
            color: Base color for the explosion particles
            game_state: Reference to game state for self-removal
        """
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.game_state = game_state
        self.frame = 0
        self.max_frames = 6 if size == "small" else 10

    def animate(self) -> None:
        """Progress the explosion animation and remove when complete."""
        self.frame += 1
        if self.frame >= self.max_frames:
            self.game_state.explosions.remove(self)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw expanding particle explosion with fade effect."""
        # Calculate animation progress (0 to 1)
        progress = self.frame / self.max_frames
        fade = 1 - progress  # Fade out as animation progresses

        # Get center position
        center_x, center_y = context.get_cell_position(self.x, self.y)
        center_x += context.cell_size // 2
        center_y += context.cell_size // 2

        # Explosion parameters based on size
        if self.size == "small":
            particle_count = 4
            max_radius = 8
        else:  # large
            particle_count = 8
            max_radius = 15

        # Draw expanding particles in a circle pattern
        for i in range(particle_count):
            angle = (i / particle_count) * 2 * 3.14159  # Distribute evenly in circle
            distance = progress * max_radius

            # Particle position
            px = int(center_x + distance * (i % 2 * 2 - 1))  # Alternate left/right
            py = int(center_y + distance * ((i // 2) % 2 * 2 - 1))  # Alternate up/down

            # Particle size decreases as it expands
            particle_size = int((1 - progress * 0.5) * 3) + 1

            # Color with fade
            r, g, b = self.color
            particle_color = (
                int(r * fade),
                int(g * fade),
                int(b * fade),
                int(255 * fade)
            )

            draw.rectangle(
                [px - particle_size, py - particle_size,
                 px + particle_size, py + particle_size],
                fill=particle_color
            )

        # Draw a central flash for the first few frames
        if self.frame < 3:
            flash_size = int((1 - progress * 2) * 4)
            flash_color = (*self.color, int(255 * (1 - progress * 2)))
            draw.ellipse(
                [center_x - flash_size, center_y - flash_size,
                 center_x + flash_size, center_y + flash_size],
                fill=flash_color
            )


class Enemy(Drawable):
    """Represents an enemy at a specific position."""

    def __init__(self, x: int, y: int, health: int, game_state: "GameState"):
        """
        Initialize an enemy.

        Args:
            x: Week position in contribution grid (0-51)
            y: Day position in contribution grid (0-6, Sun-Sat)
            health: Initial health/lives (1-4)
            game_state: Reference to game state for self-removal when destroyed
        """
        self.x = x
        self.y = y
        self.health = health
        self.game_state = game_state

    def take_damage(self) -> None:
        """
        Enemy takes 1 damage and removes itself from game if destroyed.
        Creates a large explosion when destroyed.
        """
        self.health -= 1
        if self.health <= 0:
            # Create large explosion with green color (enemy color)
            explosion = Explosion(self.x, self.y, "large", (57, 211, 83), self.game_state)
            self.game_state.explosions.append(explosion)
            self.game_state.enemies.remove(self)

    def animate(self) -> None:
        """Update enemy state for next frame (enemies don't animate currently)."""
        pass

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the enemy at its position."""        
        x, y = context.get_cell_position(self.x, self.y)
        color = context.enemy_colors.get(self.health, context.enemy_colors[1])

        draw.rectangle(
            [x, y, x + context.cell_size, y + context.cell_size],
            fill=color,
        )


class Bullet(Drawable):
    """Represents a bullet fired by the ship."""

    def __init__(self, x: int, game_state: "GameState"):
        """
        Initialize a bullet at ship's firing position.

        Args:
            x: Week position where bullet is fired (0-51)
            game_state: Reference to game state for collision detection and self-removal
        """
        self.x = x
        self.y: float = SHIP_POSITION_Y - 1
        self.game_state = game_state


    def _check_collision(self) -> Enemy | None:
        """Check if bullet has hit an enemy at its current position."""
        for enemy in self.game_state.enemies:
            if enemy.x == self.x and enemy.y >= self.y:
                return enemy
        return None

    def animate(self) -> None:
        """Update bullet position, check for collisions, and remove on hit."""
        self.y -= BULLET_SPEED
        hit_enemy = self._check_collision()
        if hit_enemy:
            # Create small explosion at impact point with yellow color
            explosion = Explosion(self.x, self.y, "small", (255, 223, 0), self.game_state)
            self.game_state.explosions.append(explosion)
            hit_enemy.take_damage()
            self.game_state.bullets.remove(self)
        if self.y < -10: # magic number to remove off-screen bullets
            self.game_state.bullets.remove(self)

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the bullet with trailing tail effect."""

        trail_num = 5
        for i in range(trail_num):
            trail_y = self.y + (trail_num - i) * BULLET_SPEED / 2
            fade_factor = (i + 1) / trail_num * 0.7
            self._draw_bullet(draw, context, (self.x, trail_y), fade_factor=fade_factor)
        
        self._draw_bullet(draw, context, (self.x, self.y))

    def _draw_bullet(
        self, 
        draw: ImageDraw.ImageDraw, 
        context: "RenderContext", 
        position: tuple[float, float], 
        fade_factor: float = 1, 
    ) -> None:
        x, y = context.get_cell_position(position[0], position[1])
        x += context.cell_size // 2
        y += context.cell_size // 2

        r_x = .5
        r_y = 3
        draw.rectangle(
            [x - r_x, y - r_y, x + r_x, y + r_y],
            fill=(*context.bullet_color, int(fade_factor * 255)),
        )


class Ship(Drawable):
    """Represents the player's ship."""

    def __init__(self, game_state: "GameState"):
        """Initialize the ship at starting position."""
        self.x: float = 25  # Start middle of screen
        self.target_x = self.x
        self.shoot_cooldown = 0  # Frames until ship can shoot again
        self.game_state = game_state

    def move_to(self, x: int):
        """
        Move ship to a new x position.

        Args:
            x: Target x position
        """
        self.target_x = x

    def is_moving(self) -> bool:
        """Check if ship is moving to a new position."""
        return self.x != self.target_x

    def can_shoot(self) -> bool:
        """Check if ship can shoot (cooldown has finished)."""
        return self.shoot_cooldown == 0

    def animate(self) -> None:
        """Update ship position, moving toward target at constant speed."""
        if self.x < self.target_x:
            self.x = min(self.x + SHIP_SPEED, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - SHIP_SPEED, self.target_x)

        # Decrement shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw the ship with gradient effects and detailed design."""
        # Ship stays below the grid at a fixed vertical position
        x, y = context.get_cell_position(self.x, SHIP_POSITION_Y)

        # Calculate ship dimensions
        center_x = x + context.cell_size // 2
        width = context.cell_size
        height = context.cell_size

        # Extract base color components
        r, g, b = context.ship_color

        # Draw engine glow (bottom, brightest)
        glow_color = (min(r + 40, 255), min(g + 40, 255), min(b + 60, 255))
        draw.ellipse(
            [center_x - 3, y + height - 4, center_x + 3, y + height + 2],
            fill=glow_color
        )

        # Draw wings (darker shade)
        wing_color = (max(r - 30, 0), max(g - 30, 0), max(b - 30, 0))
        # Left wing
        draw.polygon(
            [
                (center_x - 2, y + height * 0.4),
                (x - 2, y + height * 0.7),
                (x + 2, y + height * 0.8),
            ],
            fill=wing_color
        )
        # Right wing
        draw.polygon(
            [
                (center_x + 2, y + height * 0.4),
                (x + width + 2, y + height * 0.7),
                (x + width - 2, y + height * 0.8),
            ],
            fill=wing_color
        )

        # Draw main body with gradient (3 segments for smooth gradient)
        # Front segment (lightest)
        front_color = (min(r + 30, 255), min(g + 30, 255), min(b + 40, 255))
        draw.polygon(
            [
                (center_x, y),  # Nose
                (center_x - 4, y + height * 0.35),
                (center_x + 4, y + height * 0.35),
            ],
            fill=front_color
        )

        # Middle segment (base color)
        draw.polygon(
            [
                (center_x - 4, y + height * 0.35),
                (center_x + 4, y + height * 0.35),
                (center_x - 5, y + height * 0.7),
                (center_x + 5, y + height * 0.7),
            ],
            fill=context.ship_color
        )

        # Back segment (darker)
        back_color = (max(r - 20, 0), max(g - 20, 0), max(b - 20, 0))
        draw.polygon(
            [
                (center_x - 5, y + height * 0.7),
                (center_x + 5, y + height * 0.7),
                (center_x - 4, y + height),
                (center_x + 4, y + height),
            ],
            fill=back_color
        )

        # Draw cockpit (bright accent)
        cockpit_color = (min(r + 80, 255), min(g + 100, 255), min(b + 120, 255))
        draw.ellipse(
            [center_x - 2, y + height * 0.25, center_x + 2, y + height * 0.45],
            fill=cockpit_color
        )


class GameState(Drawable):
    """Manages the current state of the game."""

    def __init__(self, contribution_data: ContributionData):
        """
        Initialize game state from contribution data.

        Args:
            contribution_data: The GitHub contribution data
        """
        self.starfield = Starfield()
        self.ship = Ship(self)
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.explosions: List[Explosion] = []

        # Initialize enemies from contribution data
        self._initialize_enemies(contribution_data)

    def _initialize_enemies(self, contribution_data: ContributionData):
        """Create enemies based on contribution levels."""
        weeks = contribution_data["weeks"]
        for week_idx, week in enumerate(weeks):
            for day_idx, day in enumerate(week["days"]):
                level = day["level"]
                if level <= 0:
                    continue
                enemy = Enemy(x=week_idx, y=day_idx, health=level, game_state=self)
                self.enemies.append(enemy)

    def shoot(self) -> None:
        """
        Ship shoots a bullet and starts cooldown timer.
        """
        bullet = Bullet(int(self.ship.x), game_state=self)
        self.bullets.append(bullet)
        self.ship.shoot_cooldown = SHIP_SHOOT_COOLDOWN_FRAMES

    def is_complete(self) -> bool:
        """Check if game is complete (all enemies destroyed)."""
        return len(self.enemies) == 0

    def can_take_action(self) -> bool:
        """Check if ship can take an action (not moving and can shoot)."""
        return not self.ship.is_moving() and self.ship.can_shoot()

    def animate(self) -> None:
        """Update all game objects for next frame."""
        self.starfield.animate()
        self.ship.animate()
        for enemy in self.enemies:
            enemy.animate()
        for bullet in self.bullets:
            bullet.animate()
        for explosion in self.explosions:
            explosion.animate()

    def draw(self, draw: ImageDraw.ImageDraw, context: "RenderContext") -> None:
        """Draw all game objects including the grid."""
        self.starfield.draw(draw, context)
        for enemy in self.enemies:
            enemy.draw(draw, context)
        for explosion in self.explosions:
            explosion.draw(draw, context)
        for bullet in self.bullets:
            bullet.draw(draw, context)
        self.ship.draw(draw, context)