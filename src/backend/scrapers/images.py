import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from fastapi import HTTPException

def random_user_agent():
    """
    Returns a random User-Agent string from a predefined list.
    This helps disguise automated scraping requests.
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Mobile Safari/537.36",
    ]
    return random.choice(user_agents)

def sanitize_url(url: str) -> str:
    """
    Creates a hash of the URL to use as a directory name for downloads.

    Args:
        url (str): The URL to be hashed.

    Returns:
        str: The MD5 hash of the URL.
    """
    return hashlib.md5(url.encode()).hexdigest()

def sanitize_image_name(image_url: str) -> str:
    """
    Sanitizes the image URL to create a valid local filename. Strips off
    query parameters and replaces invalid characters with underscores.

    Args:
        image_url (str): The raw image URL.

    Returns:
        str: A sanitized filename.
    """
    # Remove query parameters
    image_url = re.sub(r"\?.*", "", image_url)
    # Extract the image name from the URL
    image_name = os.path.basename(image_url)
    # Replace invalid characters with underscores
    image_name = re.sub(r"[^a-zA-Z0-9\-.]", "_", image_name)
    return image_name

def resolve_url(url: str, base_url: str) -> str:
    """
    Resolves relative URLs to absolute ones using the base URL.

    Args:
        url (str): The (relative or absolute) URL found in the page.
        base_url (str): The main domain or base URL of the page.

    Returns:
        str: An absolute URL that can be requested directly.
    """
    if not url.startswith(("http", "https")):
        if url.startswith("//"):
            return "https:" + url
        elif url.startswith("/"):
            return base_url.rstrip("/") + "/" + url.lstrip("/")
        else:
            return base_url.rstrip("/") + "/" + url
    return url

def download_image_if_valid(session: requests.Session, image_url: str, save_path: str) -> str:
    """
    Checks if a URL is a valid image by attempting to open it with PIL.
    If valid, the image is downloaded and saved locally.

    Args:
        session (requests.Session): A requests Session object with set headers.
        image_url (str): The full URL of the image to download.
        save_path (str): The local filesystem path where the image will be saved.

    Returns:
        str: The image_url if download is successful, otherwise None.
    """
    try:
        response = session.get(image_url)
        response.raise_for_status()  # Ensure the request was successful

        # Attempt to parse the image to check if it's valid
        img = Image.open(BytesIO(response.content))

        # Accept only common formats
        if img.format in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP']:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"[INFO] Downloaded: {save_path}")
            return image_url
    except Exception as e:
        print(f"[ERROR] Failed processing {image_url}: {e}")
    return None

def scrape_images(soup: BeautifulSoup, base_url: str, session: requests.Session, download_dir: str) -> list:
    """
    Scrapes all potential image URLs in the given BeautifulSoup object.
    Downloads valid images concurrently using a ThreadPoolExecutor.

    Args:
        soup (BeautifulSoup): Parsed HTML content of the page.
        base_url (str): The main domain to resolve relative image paths.
        session (requests.Session): A requests Session object with set headers.
        download_dir (str): Directory path (already hashed) where images will be downloaded.

    Returns:
        list: A list of successfully downloaded image URLs.
    """
    images_downloaded = []
    potential_image_urls = []

    # Common file extensions for images
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

    # Collect all potential image URLs from 'img' and 'a' tags
    for tag in soup.find_all(['img', 'a']):
        for attr in ['href', 'src']:
            url = tag.get(attr)
            if url and any(url.lower().endswith(ext) for ext in image_extensions):
                potential_image_urls.append(url)

    # Create local folder for this specific URL's images
    local_download_path = os.path.join("downloads", download_dir)
    os.makedirs(local_download_path, exist_ok=True)

    # Validate and download images concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                download_image_if_valid,
                session,
                resolve_url(url, base_url),
                os.path.join(local_download_path, sanitize_image_name(url))
            )
            for url in potential_image_urls
        ]
        for future in as_completed(futures):
            result = future.result()
            if result:
                images_downloaded.append(result)

    return images_downloaded

def scrape(url: str) -> dict:
    """
    Main function to scrape images from the given URL and save them to a hashed directory.

    Args:
        url (str): The webpage URL to scrape.

    Returns:
        dict: A response with the location where the images are available.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': random_user_agent(),
        'Referer': url,
    })

    # Attempt to fetch the page
    try:
        response = session.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Could not access {url}: {e}")
        return {}

    # Parse HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Generate hash-based folder name
    hashed_dir = sanitize_url(url)

    # Build base URL for relative resources
    base_domain = "https://" + url.split('/')[2]

    # Scrape and download images
    scrape_images(soup, base_domain, session, hashed_dir)

    return {
        "Images are available for download at": f"http://127.0.0.1:8000/api/downloads/{hashed_dir}"
    }

def get_downloads(hash_value: str) -> dict:
    """
    Fetches and lists the downloaded images from a specific hash-based directory.

    Args:
        hash_value (str): The hashed directory name for a specific URL's downloads.

    Returns:
        dict: JSON response containing URLs of downloadable images.
    """
    download_path = os.path.join('downloads', hash_value)

    # Check if the download directory exists
    if not os.path.isdir(download_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    # Collect all image files in the directory
    image_files = []
    for filename in os.listdir(download_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
            # Generate the URL path for each image file
            image_url = f"/downloads/{hash_value}/{filename}"
            image_files.append(image_url)

    if not image_files:
        raise HTTPException(status_code=404, detail="No images found in the directory")

    return {"images": image_files}

def scrape_videos(url: str) -> dict:
    """
    Placeholder function for scraping videos. Not yet implemented.

    Args:
        url (str): The webpage URL to scrape for videos.

    Returns:
        dict: Placeholder response.
    """
    return {
        "message": "Scraping videos is not yet implemented."
    }
