from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

STATIC_ROOT = os.environ.get("STATIC_ROOT", "extracted_frames")
DEFAULT_INPUT_ROOT = Path(os.environ.get("DEFAULT_INPUT_ROOT", "uploads"))
DEFAULT_OUTPUT_ROOT = Path(STATIC_ROOT)
DEFAULT_FFMPEG_PATH = Path(os.environ.get("FFMPEG_PATH", "ffmpeg"))
DEFAULT_LOG_FILE = Path(os.environ.get("DEFAULT_LOG_FILE", "extraction_log.csv"))
DEFAULT_METADATA_CSV = Path(
    os.environ.get("DEFAULT_METADATA_CSV", "video_metadata.csv")
)

VALID_EXTENSIONS = [".mp4"]

DEFAULT_QUALITY = 1  # Highest quality (1-31 scale where lower is better)
DEFAULT_FORMAT = "png"
DEFAULT_FRAME_PATTERN = "frame_%04d.png"

DEFAULT_THREADS = 4
DEFAULT_OVERWRITE = False
DEFAULT_MAINTAIN_STRUCTURE = True
