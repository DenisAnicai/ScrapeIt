import os
import fastapi

# Adjust this import path based on your actual project structure.
# If "images.py" is in "src/backend/scrapers/", this would work:
from src.backend.scrapers.images import (
    sanitize_url,
    scrape,
    scrape_videos,
    get_downloads
)

root_router = fastapi.routing.APIRouter(prefix="/api")

@root_router.get("/scrape/images")
async def scrape_images_endpoint(url: str):
    """
    Endpoint to scrape images for a given URL.
    If the directory for this URL (based on its hash) already exists,
    it simply returns the location without scraping again.
    """
    hashed_dir = sanitize_url(url)
    if os.path.isdir(os.path.join('downloads', hashed_dir)):
        return {
            "Images are available for download at":
            f"http://127.0.0.1:8000/api/downloads/{hashed_dir}"
        }
    return scrape(url)

@root_router.get("/scrape/videos")
async def scrape_videos_endpoint(url: str):
    """
    Endpoint to scrape videos for a given URL.
    Currently a placeholder pointing to the images.py scrape_videos function.
    """
    return scrape_videos(url)

@root_router.get("/downloads/{hash_value}")
async def downloads_endpoint(hash_value: str):
    """
    Endpoint to list all downloaded images in a specific hashed directory.
    """
    return get_downloads(hash_value)
