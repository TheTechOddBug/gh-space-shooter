# gh-space-shooter 🚀

Transform your GitHub contribution graph into an epic space shooter game!

![Example Game](example.gif)

## Usage

### Onetime Generation

A [web interface](https://gh-space-shooter.kiyo-n-zane.com) is available for on-demand GIF generation without installing anything locally.

### GitHub Action

Automatically update your game GIF daily using GitHub Actions! Add this workflow to your repository at `.github/workflows/update-game.yml`:

```yaml
name: Update Space Shooter Game

on:
  schedule:
    - cron: '0 0 * *'  # Daily at midnight UTC
  workflow_dispatch:  # Allow manual trigger

permissions:
  contents: write

jobs:
  update-game:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: czl9707/gh-space-shooter@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          output-path: 'game.gif'
          strategy: 'random'
```

Then display it in your README:

```markdown
![My GitHub Game](game.gif)
```

**Action Inputs:**
- `github-token` (required): GitHub token for fetching contributions
- `username` (optional): Username to generate game for (defaults to repo owner)
- `output-path` (optional): Where to save the animation, supports `.gif` or `.webp` (default: `gh-space-shooter.gif`)
- `write-dataurl-to` (optional): Write WebP as HTML `<img>` data URL to text file (supports `<!-- space-shooter -->` marker injection or append mode)
- `strategy` (optional): Attack pattern - `column`, `row`, or `random` (default: `random`)
- `fps` (optional): Frames per second for animation (default: `40`)
- `commit-message` (optional): Commit message for update

### From PyPI

```bash
# Install dependencies (uses uv package manager)
uv sync

# Or with pip
pip install gh-space-shooter
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/gh-space-shooter.git
cd gh-space-shooter

# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Setup

1. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `read:user`
   - Copy the generated token

2. Set up your environment:
   ```bash
   # Copy the example env file
   touch .env
   echo "GH_TOKEN=your_token_here" >> .env
   ```
   Alternatively, export the token directly:
   ```bash
   export GH_TOKEN=your_token_here
   ```

## Project Context

**Current main usage**: GitHub Action that automatically updates a game GIF in user repositories daily (see `.github/workflows/` for action definition).

**Web App**: A FastAPI-based web application is available in the `app/` directory for on-demand GIF generation. See `app/README.md` for details.

## Architecture Overview

This is a CLI tool that transforms GitHub contribution graphs into animated space shooter GIFs using Pillow.

### Core Flow

1. **CLI (`cli.py`)** - Typer-based entry point that orchestrates the pipeline
2. **GitHubClient (`github_client.py`)** - Fetches contribution data via GitHub GraphQL API, returns typed `ContributionData` dict
3. **Animator (`game/animator.py`)** - Main game loop that coordinates strategy execution and frame generation
4. **GameState (`game/game_state.py`)** - Central state container holding ship, enemies, bullets, explosions
5. **Renderer (`game/renderer.py`)** - Converts GameState to PIL Images each frame

### Strategy Pattern

Strategies (`game/strategies/`) define how the ship clears enemies:
- `BaseStrategy` - Abstract base defining `generate_actions(game_state) -> Iterator[Action]`
- `ColumnStrategy` - Clears enemies column by column (left to right)
- `RowStrategy` - Clears enemies row by row (top to bottom)
- `RandomStrategy` - Targets enemies in random order

Strategies yield `Action(x, shoot)` objects. The Animator processes these: moving the ship to position `x`, waiting for movement/cooldown to complete, then shooting if `shoot=True`.

### Drawable System

All game objects inherit from `Drawable` (`game/drawables/drawable.py`):
- `animate(delta_time)` - Update state (position, cooldowns, particles)
- `draw(draw, context)` - Render to PIL ImageDraw

Drawables: `Ship`, `Enemy`, `Bullet`, `Explosion`, `Starfield`

The `RenderContext` (`game/render_context.py`) holds theming (colors, cell sizes, padding) and coordinate conversion helpers.

### Animation Loop

In `Animator._generate_frames()`:
1. Strategy yields next action
2. Ship moves to target x position (animate frames until arrived)
3. Ship shoots if action.shoot (animate frames for bullet travel + explosions)
4. Repeat until all enemies destroyed

Frame rate is configurable (default 40 FPS). All speeds use delta_time for frame-rate independence.

### Key Constants (`constants.py`)

- `NUM_WEEKS = 52` - Contribution graph width
- `NUM_DAYS = 7` - Contribution graph height
- Speeds are in cells/second, durations in seconds

### Output Providers

Output providers encode frames to different formats for writing:
- **`GifOutputProvider`** - Animated GIF format
- **`WebPOutputProvider`** - Animated WebP format
- **`WebpDataUrlOutputProvider`** - HTML `<img>` tag with WebP data URL for direct embedding

Each provider implements:
- `encode(frames, frame_duration) -> bytes` - Encode frames to output format
- `write(path, data) -> None` - Write encoded data to file (providers store path from constructor)

## License

MIT
