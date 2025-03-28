"""
Default configuration values for the video frame extraction tool.
"""

from pathlib import Path

# Paths
DEFAULT_INPUT_ROOT = Path("D:/Programming/DIC/Extract_frames_i_ffmpeg/videos")
DEFAULT_OUTPUT_ROOT = Path(
    "D:/Programming/DIC/Extract_frames_i_ffmpeg/extracted_frames"
)
DEFAULT_FFMPEG_PATH = Path("ffmpeg")
DEFAULT_LOG_FILE = Path("extraction_log.csv")
DEFAULT_METADATA_CSV = Path("video_metadata.csv")

# Valid video file extensions
VALID_EXTENSIONS = [".mp4"]

# Frame extraction defaults
DEFAULT_QUALITY = 1  # Highest quality (1-31 scale where lower is better)
DEFAULT_FORMAT = "png"
DEFAULT_FRAME_PATTERN = "frame_%04d.png"

# Processing settings
DEFAULT_THREADS = 4
DEFAULT_OVERWRITE = False
DEFAULT_MAINTAIN_STRUCTURE = True
