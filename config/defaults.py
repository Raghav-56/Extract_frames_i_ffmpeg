"""
Default configuration values for the video frame extraction tool.
"""

from pathlib import Path
import os

# Paths - using more general defaults
DEFAULT_INPUT_ROOT = Path("input")
DEFAULT_OUTPUT_ROOT = Path("output")
DEFAULT_FFMPEG_PATH = Path("ffmpeg")
DEFAULT_LOG_FILE = Path("extraction_log.csv")
DEFAULT_METADATA_CSV = Path("video_metadata.csv")

# Valid video file extensions
VALID_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv"]

# Frame extraction defaults
DEFAULT_QUALITY = 1  # Highest quality (1-31 scale where lower is better)
DEFAULT_FORMAT = "png"
DEFAULT_FRAME_PATTERN = "frame_%04d.png"

# Processing settings
DEFAULT_THREADS = 4
DEFAULT_OVERWRITE = False
DEFAULT_MAINTAIN_STRUCTURE = True

# Maximum video file size for web uploads (10MB)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
