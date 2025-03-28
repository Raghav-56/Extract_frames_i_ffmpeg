# Video Frame Extractor

A Python tool for extracting I-frames (keyframes) from video files using FFmpeg while preserving metadata from structured filenames.

## Overview

This tool processes video files with structured filenames that contain metadata about speakers, languages, emotions, and sentences. It extracts I-frames (keyframes) from these videos and organizes them in a directory structure that mirrors the input or in a customized hierarchy.

## Features

- Extract I-frames (keyframes) from video files using FFmpeg
- Parse structured video filenames to extract metadata
- Maintain directory structure from input to output
- Generate metadata CSV with information about processed videos
- Customizable output format and quality
- Detailed logging system

## Requirements

- Python 3.7+
- FFmpeg installed and available in PATH (or specified in configuration)
- Required Python packages:
  - pandas
  - pyrallis
  - logging

## Installation

1. Clone this repository
2. Install the required Python packages:

```bash
pip install pandas pyrallis
```

3. Ensure FFmpeg is installed on your system:
   - For Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - For Linux: `sudo apt install ffmpeg` (Ubuntu/Debian) or equivalent
   - For macOS: `brew install ffmpeg` (using Homebrew)

## Usage

### Basic Usage

Run the frame extraction with default settings:

```bash
python main.py
```

### Custom Configuration

You can customize the behavior using command-line arguments:

```bash
python main.py --input_root /path/to/videos --output_root /path/to/output --quality 2
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `input_root` | Directory containing input videos | `D:\Programming\DIC\Samvedna_Sample\Sample_vid` |
| `output_root` | Directory for extracted frames | `D:\Programming\DIC\Samvedna_Sample\Sample_vid\extracted_frames` |
| `ffmpeg_path` | Path to FFmpeg executable | `ffmpeg` |
| `threads` | Number of threads for FFmpeg | `4` |
| `frame_pattern` | Pattern for output frame filenames | `frame_%04d.png` |
| `output_format` | Output image format | `png` |
| `quality` | Image quality (1-31, lower is better) | `1` |
| `overwrite` | Whether to overwrite existing files | `False` |
| `maintain_structure` | Maintain directory structure from input | `True` |
| `log_file` | Path to log file | `extraction_log.csv` |
| `metadata_csv` | Path to metadata CSV file | `video_metadata.csv` |

## Video Filename Format

The tool expects video filenames in the following format:

```
SPEAKER_LANGUAGE_EMOTION_SENTENCE.mp4
```

Example: `A1_EN_H_S5.mp4` (Speaker One, English, Happy, Sentence 5)

### Metadata Components

- **Speaker**: Identifies the person speaking (A1-A25)
- **Language**: Language code (EN for English, HI for Hindi)
- **Emotion**: Emotion code (A for Anger, D for Disgust, F for Fear, H/Ha for Happy, N for Neutral, S for Sad)
- **Sentence**: Sentence code (S1-S18)

## Directory Structure

```
Extract_frames_i_ffmpeg/
├── config/
│   ├── defaults.py       # Default configuration values
│   └── logger_config.py  # Logging configuration
├── lib/
│   └── video_filename_parser.py  # Parse metadata from filenames
├── logs/                 # Log files directory
├── videos/               # Input videos
├── extracted_frames/     # Output frames
├── main.py               # Main execution script
└── README.md             # This file
```

## Output

The tool generates:

1. Extracted I-frames in the specified output directory
2. A log file with processing results
3. A metadata CSV file with information about each video and extracted frames

## License

MIT License or specify your preferred license
