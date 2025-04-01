__author__ = {"name": "Raghav Gupta", "username": "Raghav-56"}

# Standard library imports
import os
import shutil
import tempfile
import threading
import time
import zipfile
from pathlib import Path

# Third-party imports
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)

# Local application imports
from main import extract_frames_for_web, Config, logger

app = Flask(__name__, static_folder="static")

# Configure upload settings
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB max

# Initialize with web-specific configuration
OUTPUT_FOLDER = Path("extracted_frames")
OUTPUT_FOLDER.mkdir(exist_ok=True, parents=True)
config = Config(
    input_path=UPLOAD_FOLDER,
    output_root=OUTPUT_FOLDER,
    web_mode=True,
    overwrite=True,
)

# Use a lock to ensure thread-safe updates to the processing status
status_lock = threading.Lock()
processing_status = {
    "is_processing": False,
    "current_video": "",
    "completed": False,
    "error": None,
    "progress": 0,
    "start_time": None,
    "end_time": None,
    "frames": [],
    "output_dir": None,
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/config", methods=["GET"])
def get_config():
    """Get current configuration"""
    current_config = {
        "output_root": str(config.output_root),
        "quality": config.quality,
        "output_format": config.output_format,
        "max_upload_size": app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
        "supported_formats": config.video_extensions,
    }
    return jsonify(current_config)


class ProgressCallback:
    """Thread-safe progress callback for frame extraction"""

    def __init__(self):
        self.progress = 0

    def update(self, current, total):
        if total > 0:
            self.progress = int((current / total) * 100)
            # Update global status with thread safety
            with status_lock:
                processing_status["progress"] = self.progress
                logger.debug(f"Progress updated: {self.progress}%")


def background_process_video(video_path):
    """Background processor for videos with improved status handling"""
    global processing_status
    progress_callback = ProgressCallback()

    try:
        with status_lock:
            processing_status["is_processing"] = True
            processing_status["completed"] = False
            processing_status["error"] = None
            processing_status["progress"] = 0
            processing_status["start_time"] = time.time()
            processing_status["current_video"] = Path(video_path).name
            processing_status["frames"] = []
            # Store the actual output directory path
            output_dir = str(OUTPUT_FOLDER / Path(video_path).stem)
            processing_status["output_dir"] = output_dir

        # Check if file exists
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Process video using the enhanced function
        frame_paths = extract_frames_for_web(
            input_path=video_path,
            output_dir=output_dir,
            progress_callback=progress_callback,
            quality=config.quality,
            output_format=config.output_format,
        )

        # Update status with results
        with status_lock:
            processing_status["progress"] = 100
            processing_status["completed"] = True
            processing_status["end_time"] = time.time()

            # Fix: Ensure frame paths exist and are properly formatted
            if frame_paths and isinstance(frame_paths, list):
                processing_status["frames"] = frame_paths
            else:
                # If no frames were returned, check if they exist in the output directory
                output_path = Path(output_dir)
                if output_path.exists():
                    frames = list(output_path.glob(f"*.{config.output_format}"))
                    processing_status["frames"] = [
                        str(f.relative_to(OUTPUT_FOLDER)) for f in frames
                    ]
                else:
                    processing_status["frames"] = []

            logger.info(
                f"Processing completed. Found {len(processing_status['frames'])} frames."
            )

        # Clean up uploaded file if it's in our upload folder
        if str(video_path).startswith(str(UPLOAD_FOLDER)):
            try:
                Path(video_path).unlink()
                logger.info(f"Cleaned up uploaded file: {video_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file {video_path}: {e}")

    except Exception as e:
        with status_lock:
            processing_status["error"] = str(e)
        logger.error(f"Error in background processing: {e}")
    finally:
        with status_lock:
            processing_status["is_processing"] = False


@app.route("/upload", methods=["POST"])
def upload_video():
    """Handle video file uploads with improved output handling"""
    with status_lock:
        if processing_status["is_processing"]:
            return jsonify({"error": "Processing is already in progress"}), 409

    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]

    if video_file.filename == "":
        return jsonify({"error": "No video file selected"}), 400

    # Save the uploaded file
    filename = Path(video_file.filename).name
    file_path = UPLOAD_FOLDER / filename
    video_file.save(file_path)

    # Define output directory based on video name
    output_dir = OUTPUT_FOLDER / file_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Start processing in background
    processing_thread = threading.Thread(
        target=background_process_video, args=(file_path,)
    )
    processing_thread.daemon = True
    processing_thread.start()

    return jsonify(
        {
            "message": "Video uploaded and processing started",
            "status_endpoint": "/status",
            "filename": filename,
        }
    )


@app.route("/process", methods=["POST"])
def process_videos():
    """Handle processing request for local video path"""
    with status_lock:
        if processing_status["is_processing"]:
            return jsonify({"error": "Processing is already in progress"}), 409

    # Get video path
    video_path = request.form.get("video_path")
    if not video_path:
        return jsonify({"error": "Video path is required"}), 400

    # Validate that the path exists
    if not Path(video_path).exists():
        return jsonify({"error": "Video file not found at specified path"}), 404

    # Start processing in background
    processing_thread = threading.Thread(
        target=background_process_video, args=(video_path,)
    )
    processing_thread.daemon = True
    processing_thread.start()

    return jsonify(
        {
            "message": "Processing started",
            "status_endpoint": "/status",
            "filename": Path(video_path).name,
        }
    )


@app.route("/status", methods=["GET"])
def get_status():
    """Get the current processing status with thread safety"""
    with status_lock:
        result = {**processing_status}

        # Calculate elapsed time
        if result.get("is_processing") and result.get("start_time"):
            result["elapsed_seconds"] = int(time.time() - result["start_time"])
        elif result.get("start_time") and result.get("end_time"):
            result["elapsed_seconds"] = int(result["end_time"] - result["start_time"])

    return jsonify(result)


@app.route("/frames", methods=["GET"])
def list_frames():
    """List all extracted frames with improved directory handling"""
    if not OUTPUT_FOLDER.exists():
        return jsonify({"error": "Output directory does not exist"}), 404

    video_path = request.args.get("video_path")
    result = []

    # Find all output directories
    for video_dir in OUTPUT_FOLDER.glob("*"):
        if not video_dir.is_dir():
            continue

        # Filter by video name if specified
        if video_path and video_dir.name != Path(video_path).stem:
            continue

        frames = list(video_dir.glob(f"*.{config.output_format}"))
        frames.sort()  # Sort frames for consistent order

        if frames:
            result.append(
                {
                    "video_name": video_dir.name,
                    "path": str(video_dir.relative_to(OUTPUT_FOLDER)),
                    "frame_count": len(frames),
                    "frames": [str(f.relative_to(OUTPUT_FOLDER)) for f in frames],
                }
            )

    return jsonify(result)


@app.route("/frames/<path:frame_path>")
def serve_frame(frame_path):
    """Serve a specific frame"""
    return send_from_directory(str(OUTPUT_FOLDER), frame_path)


@app.route("/download_frames", methods=["GET"])
def download_frames():
    """Download frames as a ZIP archive"""
    video_path = request.args.get("video_path")
    if not video_path:
        return jsonify({"error": "Video path parameter is required"}), 400

    # Find the output directory for this video
    video_name = Path(video_path).stem
    video_output_dir = OUTPUT_FOLDER / video_name

    if not video_output_dir.exists():
        return jsonify({"error": f"No frames found for {video_name}"}), 404

    # Create a temporary zip file
    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / f"{video_name}_frames.zip"

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for frame in video_output_dir.glob(f"*.{config.output_format}"):
            zipf.write(frame, arcname=frame.name)

    return send_file(
        zip_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{video_name}_frames.zip",
    )


if __name__ == "__main__":
    # Create necessary folders
    static_folder = Path(app.root_path) / "static"
    static_folder.mkdir(exist_ok=True)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
