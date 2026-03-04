# apps/backend/app/routes/images.py
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()

# Define the absolute path to the image directory.
# This assumes the script is run from the root of the 'IcfesLeveling' project.
IMAGE_DIRECTORY = os.path.abspath("database/allquestions")

# Mount the static files directory.
# The {path:path} parameter allows matching nested file paths.
# The endpoint will be accessible at /api/v1/images/...
router.mount(
    "/", 
    StaticFiles(directory=IMAGE_DIRECTORY, html=False), 
    name="images"
)
