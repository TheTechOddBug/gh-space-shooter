"""Renderer for drawing game frames using Pillow."""

from PIL import Image, ImageDraw

from ..constants import NUM_WEEKS, SHIP_POSITION_Y
from .game_state import GameState
from .render_context import RenderContext

class Renderer:
    """Renders game state as PIL Images."""
    def __init__(self, game_state: GameState, render_context: RenderContext):
        """
        Initialize renderer.

        Args:
            game_state: The game state to render
            render_context: Rendering configuration and theming
        """
        self.game_state = game_state

        self.context = render_context

        self.grid_width = NUM_WEEKS * (self.context.cell_size + self.context.cell_spacing)
        self.grid_height = SHIP_POSITION_Y * (self.context.cell_size + self.context.cell_spacing)
        self.width = self.grid_width + 2 * self.context.padding
        self.height = self.grid_height + 2 * self.context.padding

    def render_frame(self) -> Image.Image:
        """
        Render the current game state as an image.

        Returns:
            PIL Image of the current frame
        """
        # Create image with background color
        img = Image.new("RGB", (self.width, self.height), self.context.grid_color)
        
        # Draw game state
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")
        self.game_state.draw(draw, self.context)
        combined = Image.alpha_composite(img.convert("RGBA"), overlay)
        
        return combined.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE)
