import fastapi
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.backend.routers.root import root_router

app = fastapi.FastAPI()
app.include_router(root_router)

print(str(Path(__file__).resolve().parent.parent))
# Path to the directory containing the React build files
BUILD_DIR = Path("../frontend/build")

app.mount("/static", StaticFiles(directory=BUILD_DIR / "static"), name="static")

# Serve downloads directory for images
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")


@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    """
    Catch-all route to serve React's index.html for non-API routes.
    This allows React to handle client-side routing.
    """
    if full_path.startswith("api"):
        # Return 404 for routes that start with `/api` but are undefined
        return fastapi.responses.JSONResponse(status_code=404, content={"detail": "Not Found"})
    # Serve the React index.html for all other routes
    return FileResponse(BUILD_DIR / "index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
