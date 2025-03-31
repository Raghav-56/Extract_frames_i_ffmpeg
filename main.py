# Extracting I keyframes from videos using FFmpeg

__author__ = {"name": "Raghav Gupta", "username": "Raghav-56"}

import subprocess
import pandas as pd
import pyrallis
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

from config.logger_config import setup_logger
from config.defaults import (
    VALID_EXTENSIONS,
    DEFAULT_THREADS,
    DEFAULT_QUALITY,
    DEFAULT_FORMAT,
    DEFAULT_INPUT_ROOT,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_FFMPEG_PATH,
    DEFAULT_FRAME_PATTERN,
    DEFAULT_OVERWRITE,
    DEFAULT_MAINTAIN_STRUCTURE,
    DEFAULT_LOG_FILE,
    DEFAULT_METADATA_CSV,
)
from lib.video_filename_parser import parse_video_filename

# Configure logging
logger = setup_logger(
    log_dir="logs",
    app_name="frame_extractor",
    console_level=20,
)


@dataclass
class Config:
    input_root: Path = DEFAULT_INPUT_ROOT
    output_root: Path = DEFAULT_OUTPUT_ROOT
    ffmpeg_path: Path = DEFAULT_FFMPEG_PATH
    threads: int = DEFAULT_THREADS
    frame_pattern: str = DEFAULT_FRAME_PATTERN
    output_format: str = DEFAULT_FORMAT
    video_extensions: List[str] = field(default_factory=lambda: VALID_EXTENSIONS)
    quality: int = DEFAULT_QUALITY
    overwrite: bool = DEFAULT_OVERWRITE
    maintain_structure: bool = DEFAULT_MAINTAIN_STRUCTURE
    log_file: Optional[Path] = DEFAULT_LOG_FILE
    metadata_csv: Optional[Path] = DEFAULT_METADATA_CSV


class FrameExtractor:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.log_df = pd.DataFrame(
            columns=[
                "video_path",
                "frame_count",
                "output_dir",
                "status",
                "error",
                "metadata",
            ]
        )
        self.metadata_df = pd.DataFrame()
        logger.info("Initialized FrameExtractor with config: %s", self.cfg)

    def create_output_structure(self, video_path: Path) -> Path:
        if self.cfg.maintain_structure:
            relative_path = video_path.relative_to(self.cfg.input_root)
            output_dir = self.cfg.output_root / relative_path.with_suffix("")
        else:
            output_dir = self.cfg.output_root / video_path.stem

        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Created output directory: %s", output_dir)
        return output_dir

    def build_ffmpeg_command(self, input_path: Path, output_dir: Path) -> List[str]:
        if "%d" not in self.cfg.frame_pattern and "%0" not in self.cfg.frame_pattern:
            frame_pattern = f"frame_%03d.{self.cfg.output_format}"
            logger.warning(
                "Frame pattern doesn't include frame number format. Using %s instead.",
                frame_pattern,
            )
        else:
            frame_pattern = self.cfg.frame_pattern

        cmd = [
            str(self.cfg.ffmpeg_path),
            "-i",
            str(input_path),
            "-threads",
            str(self.cfg.threads),
            "-vf",
            "select='eq(pict_type,I)'",
            "-vsync",
            "vfr",
            "-q:v",
            str(self.cfg.quality),
            "-f",
            "image2",
            str(output_dir / frame_pattern),
        ]

        if self.cfg.overwrite:
            cmd.insert(1, "-y")

        logger.debug("FFmpeg command: %s", " ".join(cmd))
        return cmd

    def process_video(self, video_path: Path):
        try:
            metadata = parse_video_filename(video_path.name)
            logger.info(
                "Processing video: %s (%s in %s)",
                video_path.name,
                metadata["emotion_full"],
                metadata["language_full"],
            )

            output_dir = self.create_output_structure(video_path)
            cmd = self.build_ffmpeg_command(video_path, output_dir)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            frame_count = len(list(output_dir.glob(f"*.{self.cfg.output_format}")))
            logger.info("Extracted %d I-frames from %s", frame_count, video_path.name)

            self._update_log(
                video_path, frame_count, output_dir, "success", metadata=metadata
            )
            self._update_metadata(video_path, metadata, frame_count)

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error("FFmpeg error processing %s: %s", video_path, error_msg)
            self._update_log(video_path, 0, None, "failed", error_msg)
        except Exception as e:
            logger.error("Failed processing %s: %s", video_path, str(e), exc_info=True)
            self._update_log(video_path, 0, None, "failed", str(e))

    def _update_log(
        self, video_path, frame_count, output_dir, status, error=None, metadata=None
    ):
        new_entry = {
            "video_path": str(video_path),
            "frame_count": frame_count,
            "output_dir": str(output_dir) if output_dir else None,
            "status": status,
            "error": error,
            "metadata": metadata,
        }
        self.log_df = pd.concat(
            [self.log_df, pd.DataFrame([new_entry])], ignore_index=True
        )

    def _update_metadata(self, video_path, metadata, frame_count):
        metadata_entry = {
            "video_path": str(video_path),
            "frame_count": frame_count,
            **metadata,
        }
        self.metadata_df = pd.concat(
            [self.metadata_df, pd.DataFrame([metadata_entry])], ignore_index=True
        )

    def process_directory(self):
        logger.info("Searching for videos in %s", self.cfg.input_root)
        video_files = [
            p
            for p in self.cfg.input_root.rglob("*")
            if p.suffix.lower() in self.cfg.video_extensions
        ]

        if not video_files:
            logger.warning("No video files found in %s", self.cfg.input_root)
            return

        logger.info("Found %d videos to process", len(video_files))

        for idx, video_path in enumerate(video_files, 1):
            logger.info("Processing %d/%d: %s", idx, len(video_files), video_path.name)
            self.process_video(video_path)

        if self.cfg.log_file:
            self.log_df.to_csv(self.cfg.log_file, index=False)
            logger.info("Saved extraction log to %s", self.cfg.log_file)

        if self.cfg.metadata_csv and not self.metadata_df.empty:
            self.metadata_df.to_csv(self.cfg.metadata_csv, index=False)
            logger.info("Saved video metadata to %s", self.cfg.metadata_csv)


def main():
    logger.info("Starting frame extraction process")
    cfg = pyrallis.parse(config_class=Config)
    extractor = FrameExtractor(cfg)
    extractor.process_directory()
    logger.info("Frame extraction completed")


if __name__ == "__main__":
    main()
