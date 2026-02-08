"""FastAPI web app for gh-space-shooter GIF generation."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, Response
# from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gh_space_shooter.game import Animator, ColumnStrategy, RandomStrategy, RowStrategy, BaseStrategy
from gh_space_shooter.github_client import GitHubAPIError, GitHubClient
from gh_space_shooter.output import resolve_output_provider

load_dotenv()

app = FastAPI(title="GitHub Space Shooter")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
# app.mount("/public", StaticFiles(directory=Path(__file__).parent / "public"), name="public")


STRATEGY_MAP: dict[str, type[BaseStrategy]] = {
    "column": ColumnStrategy,
    "row": RowStrategy,
    "random": RandomStrategy,
}


def generate_animation(username: str, strategy: str, token: str, output_format: str = "gif") -> tuple[bytes, str]:
    """Generate a space shooter animation for a GitHub user."""
    with GitHubClient(token) as client:
        data = client.get_contribution_graph(username)

    strategy_class: type[BaseStrategy] = STRATEGY_MAP.get(strategy, RandomStrategy)
    strat = strategy_class()

    animator = Animator(data, strat, fps=25, watermark=True)

    # Resolve provider based on requested format
    fake_path = f"output.{output_format}"
    provider = resolve_output_provider(fake_path, fps=25, watermark=True)

    encoded = provider.encode(animator.generate_frames())

    # Determine media type
    media_type = f"image/{output_format}"
    return encoded, media_type

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/generate")
async def generate(
    username: str = Query(..., min_length=1, description="GitHub username"),
    strategy: str = Query("random", description="Animation strategy"),
    format: str = Query("gif", description="Output format: gif, webp"),
):
    """Generate and return a space shooter animation."""
    token = os.getenv("GH_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    if strategy not in STRATEGY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Choose from: {', '.join(STRATEGY_MAP.keys())}",
        )

    try:
        encoded, media_type = generate_animation(username, strategy, token, format)
        return Response(
            content=encoded,
            media_type=media_type,
            headers={
                "Response-Type": "blob",
                "Content-Disposition": f"inline; filename={username}-space-shooter.{format}"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GitHubAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate animation: {e}")
