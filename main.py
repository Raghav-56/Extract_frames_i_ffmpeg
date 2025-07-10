import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Union
import os
import pandas as pd
import pyrallis

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
    STATIC_ROOT,
)
from lib.video_filename_parser import parse_video_filename

logger = setup_logger(
    log_dir="logs",
    app_name="frame_extractor",
    console_level=20,
)


@dataclass
class Config:
    """Configuration for frame extraction from videos."""

    input_path: Path = DEFAULT_INPUT_ROOT
    output_root: Optional[Path] = DEFAULT_OUTPUT_ROOT
    ffmpeg_path: Path = DEFAULT_FFMPEG_PATH
    threads: int = DEFAULT_THREADS
    frame_pattern: str = DEFAULT_FRAME_PATTERN
    output_format: str = DEFAULT_FORMAT
    video_extensions: List[str] = field(default_factory=lambda: VALID_EXTENSIONS)
    quality: int = DEFAULT_QUALITY
    overwrite: bool = DEFAULT_OVERWRITE
    maintain_structure: bool = DEFAULT_MAINTAIN_STRUCTURE
    use_parent_dir: bool = False
    web_mode: bool = False
    log_file: Optional[Path] = DEFAULT_LOG_FILE
    metadata_csv: Optional[Path] = DEFAULT_METADATA_CSV

    def validate_paths(self):
        if self.web_mode:
            static_root = Path(STATIC_ROOT).resolve()
            if self.output_root:
                output_root_path = Path(self.output_root).resolve()
                if not str(output_root_path).startswith(str(static_root)):
                    raise ValueError(
                        "output_root must be inside the static root directory."
                    )


class FrameExtractor:

    def __init__(self, cfg: Config):
        cfg.validate_paths()
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

        if cfg.use_parent_dir and cfg.input_path.is_file():
            self.cfg.output_root = cfg.input_path.parent
            logger.info(f"Using parent directory as output: {self.cfg.output_root}")

        if self.cfg.output_root:
            self.cfg.output_root.mkdir(parents=True, exist_ok=True)

        logger.info("Initialized FrameExtractor with config: %s", self.cfg)

    def create_output_structure(self, video_path: Path) -> Path:
        try:
            if self.cfg.use_parent_dir:
                output_dir = video_path.parent / video_path.stem
            else:
                base_path = (
                    self.cfg.input_path
                    if self.cfg.input_path.is_dir()
                    else self.cfg.input_path.parent
                )

                if self.cfg.maintain_structure and video_path.is_relative_to(base_path):
                    relative_path = video_path.relative_to(base_path)
                    output_dir = self.cfg.output_root / relative_path.with_suffix("")
                else:
                    output_dir = self.cfg.output_root / video_path.stem

            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir
        except Exception as e:
            logger.warning(
                f"Error creating output structure: {e}. Using fallback path."
            )
            fallback_dir = self.cfg.output_root / video_path.stem
            fallback_dir.mkdir(parents=True, exist_ok=True)
            return fallback_dir

    def build_ffmpeg_command(self, input_path: Path, output_dir: Path) -> List[str]:
        frame_pattern = self.cfg.frame_pattern
        if "%d" not in frame_pattern and "%0" not in frame_pattern:
            frame_pattern = f"frame_%03d.{self.cfg.output_format}"
            logger.warning(f"Using default frame pattern: {frame_pattern}")

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

        return cmd

    def process_video(
        self, video_path: Path, progress_callback=None
    ) -> Optional[List[str]]:
        output_dir = None
        frame_count = 0
        frame_paths = []

        def update_progress(percent):
            if progress_callback:
                progress_callback.update(percent, 100)

        try:
            metadata = parse_video_filename(video_path.name)
            emotion = metadata.get("emotion_full", "unknown")
            language = metadata.get("language_full", "unknown")

            logger.info(
                f"Processing video: {video_path.name} ({emotion} in {language})"
            )
            update_progress(10)

            # Clear any existing output directory if in web mode and overwrite enabled
            output_dir = self.create_output_structure(video_path)
            if self.cfg.web_mode and self.cfg.overwrite and output_dir.exists():
                for existing_file in output_dir.glob(f"*.{self.cfg.output_format}"):
                    try:
                        existing_file.unlink()
                        logger.debug(f"Removed old frame: {existing_file}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to remove old frame {existing_file}: {e}"
                        )

            cmd = self.build_ffmpeg_command(video_path, output_dir)
            update_progress(20)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Improved progress tracking for FFmpeg
            for line in process.stderr:
                if "frame=" in line:
                    try:
                        # Attempt to parse progress from FFmpeg output
                        frame_info = line.strip().split("frame=")[1].split()[0].strip()
                        if frame_info.isdigit():
                            progress = min(20 + int(int(frame_info) / 10), 90)
                            update_progress(progress)
                    except Exception:
                        # Fallback if we can't parse the frame number
                        update_progress(50)

            process.wait()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)

            frame_files = list(output_dir.glob(f"*.{self.cfg.output_format}"))
            frame_count = len(frame_files)

            if self.cfg.web_mode:
                # Fix: Convert absolute paths to relative paths for web interface
                output_dir_str = str(output_dir)
                frame_paths = []
                for f in frame_files:
                    # Create a path relative to the output root for web display
                    if self.cfg.output_root and str(f).startswith(
                        str(self.cfg.output_root)
                    ):
                        rel_path = str(f.relative_to(self.cfg.output_root))
                    else:
                        # Fallback to just the filename if we can't create relative path
                        rel_path = str(output_dir.name) + "/" + f.name
                    frame_paths.append(rel_path)

                # Sort frames by name to ensure correct order
                frame_paths.sort()

            logger.info(f"Extracted {frame_count} I-frames from {video_path.name}")
            update_progress(100)

            self._update_log(
                video_path, frame_count, output_dir, "success", metadata=metadata
            )
            self._update_metadata(video_path, metadata, frame_count)

            return frame_paths if self.cfg.web_mode else None

        except Exception as e:
            error_type = (
                "FFmpeg error"
                if isinstance(e, subprocess.CalledProcessError)
                else "Error"
            )
            logger.error(f"{error_type} processing {video_path}: {e}")
            self._update_log(video_path, frame_count, output_dir, "failed", str(e))

            return [] if self.cfg.web_mode else None

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

    def process_input(self) -> Optional[Union[List[str], Dict[str, List[str]]]]:
        logger.info(f"Processing input: {self.cfg.input_path}")

        if self.cfg.input_path.is_file():
            if self.cfg.input_path.suffix.lower() in self.cfg.video_extensions:
                return self.process_video(self.cfg.input_path)
            else:
                logger.warning(
                    f"Input file {self.cfg.input_path} is not a supported video format"
                )
                return None
        elif self.cfg.input_path.is_dir():
            return self.process_directory()
        else:
            logger.error(f"Input path {self.cfg.input_path} does not exist")
            return None

    def process_directory(self) -> Optional[Dict[str, List[str]]]:
        video_files = [
            p
            for p in self.cfg.input_path.rglob("*")
            if p.suffix.lower() in self.cfg.video_extensions
        ]
        if not video_files:
            return {} if self.cfg.web_mode else None
        if not self.cfg.web_mode and self.cfg.use_parent_dir:
            self.cfg.output_root = self.cfg.input_path
        all_frames = {} if self.cfg.web_mode else None
        for video_path in video_files:
            result = self.process_video(video_path)
            if self.cfg.web_mode and result:
                all_frames[video_path.name] = result
        self._save_logs_and_metadata()
        return all_frames

    def _save_logs_and_metadata(self):
        if self.cfg.log_file:
            self.log_df.to_csv(self.cfg.log_file, index=False)
            logger.info("Saved extraction log to %s", self.cfg.log_file)

        if self.cfg.metadata_csv and not self.metadata_df.empty:
            self.metadata_df.to_csv(self.cfg.metadata_csv, index=False)
            logger.info("Saved video metadata to %s", self.cfg.metadata_csv)


def main():
    logger.info("Starting frame extraction process")
    cfg = pyrallis.parse(config_class=Config)
    # For CLI mode, default to using parent directory as output
    cfg.use_parent_dir = True
    extractor = FrameExtractor(cfg)
    extractor.process_input()
    logger.info("Frame extraction completed")


def extract_frames_for_web(
    input_path, output_dir=None, progress_callback=None, **kwargs
):
    config_args = {
        "input_path": Path(input_path),
        "web_mode": True,
        "use_parent_dir": output_dir is None,
        "overwrite": True,
    }

    static_root = Path(STATIC_ROOT).resolve()
    if output_dir:
        output_dir_path = Path(output_dir).resolve()
        if not str(output_dir_path).startswith(str(static_root)):
            raise ValueError("output_dir must be inside the static root directory.")
        config_args["output_root"] = output_dir_path
        Path(output_dir_path).mkdir(parents=True, exist_ok=True)
    else:
        config_args["output_root"] = static_root
        static_root.mkdir(parents=True, exist_ok=True)

    config_args.update(kwargs)
    cfg = Config(**config_args)

    extractor = FrameExtractor(cfg)

    if Path(input_path).is_file():
        return extractor.process_video(Path(input_path), progress_callback)
    else:
        return extractor.process_input()


if __name__ == "__main__":
    main()
