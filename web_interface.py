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
from main import Config, FrameExtractor, logger
from lib.video_filename_parser import parse_video_filename

app = Flask(__name__, static_folder="static")

# Configure upload settings
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB max

# Initialize with more general configuration
config = Config()

# Set more appropriate default paths for web interface
config.input_root = UPLOAD_FOLDER  # Set uploads as the input root
config.output_root = Path("extracted_frames")  # Set a general output location
config.output_root.mkdir(exist_ok=True, parents=True)

extractor = FrameExtractor(config)

processing_status = {
    "is_processing": False,
    "current_video": "",
    "completed": False,
    "error": None,
    "progress": 0,
    "start_time": None,
    "end_time": None,
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
    """Progress callback for frame extraction"""

    def __init__(self):
        self.progress = 0

    def update(self, current, total):
        if total > 0:
            self.progress = int((current / total) * 100)
        else:
            self.progress = 0


def background_process_videos(video_path):
    """Background processor for videos"""
    global processing_status
    progress_callback = ProgressCallback()

    try:
        processing_status["is_processing"] = True
        processing_status["completed"] = False
        processing_status["error"] = None
        processing_status["progress"] = 0
        processing_status["start_time"] = time.time()

        # Check if file exists
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Extract metadata if possible
        try:
            video_name = Path(video_path).name
            metadata = parse_video_filename(video_name)
            processing_status["metadata"] = metadata
        except Exception as e:
            logger.warning(f"Could not parse video metadata: {str(e)}")
            processing_status["metadata"] = None

        # Process video
        processing_status["current_video"] = Path(video_path).name

        # Hook up progress callback to extractor
        extractor.process_video(Path(video_path), progress_callback)

        # Update progress from callback
        processing_status["progress"] = 100
        processing_status["completed"] = True
        processing_status["end_time"] = time.time()

        # Clean up uploaded file if it's in our upload folder
        if str(video_path).startswith(str(UPLOAD_FOLDER)):
            try:
                Path(video_path).unlink()
                logger.info(f"Cleaned up uploaded file: {video_path}")
            except Exception as e:
                logger.warning(
                    f"Could not remove temporary file {video_path}: {str(e)}"
                )

    except Exception as e:
        processing_status["error"] = str(e)
        logger.error(f"Error in background processing: {str(e)}")
    finally:
        processing_status["is_processing"] = False


@app.route("/upload", methods=["POST"])
def upload_video():
    """Handle video file uploads"""
    if processing_status["is_processing"]:
        return jsonify({"error": "Processing is already in progress"}), 409

    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]

    if video_file.filename == "":
        return jsonify({"error": "No video file selected"}), 400

    # Save the uploaded file
    filename = Path(video_file.filename).name
    file_path = app.config["UPLOAD_FOLDER"] / filename
    video_file.save(file_path)

    # Update configuration from form data
    output_root = request.form.get("output_root", str(config.output_root))
    quality = int(request.form.get("quality", config.quality))
    output_format = request.form.get("output_format", config.output_format)

    # Update configuration
    config.output_root = Path(output_root)
    config.quality = quality
    config.output_format = output_format

    # Ensure input_root is set to the uploads folder for uploaded files
    config.input_root = UPLOAD_FOLDER

    # Start processing in background
    processing_thread = threading.Thread(
        target=background_process_videos, args=(file_path,)
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
    if processing_status["is_processing"]:
        return jsonify({"error": "Processing is already in progress"}), 409

    # Get video path and configuration
    video_path = request.form.get("video_path")
    if not video_path:
        return jsonify({"error": "Video path is required"}), 400

    # Validate that the path exists
    if not Path(video_path).exists():
        return jsonify({"error": "Video file not found at specified path"}), 404

    output_root = request.form.get("output_root", str(config.output_root))
    quality = int(request.form.get("quality", config.quality))
    output_format = request.form.get("output_format", config.output_format)

    # Update configuration
    config.output_root = Path(output_root)
    config.quality = quality
    config.output_format = output_format

    # Start processing in background
    processing_thread = threading.Thread(
        target=background_process_videos, args=(video_path,)
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
    """Get the current processing status"""
    # If processing is done and successful, include detailed frame info
    if processing_status.get("completed", False) and not processing_status.get("error"):
        video_name = processing_status.get("current_video")
        if video_name:
            # Find the frames for this video
            video_output_dir = None
            for video_dir in config.output_root.glob("**/"):
                if video_dir.name == Path(video_name).stem:
                    video_output_dir = video_dir
                    break

            if video_output_dir:
                frames = list(video_output_dir.glob(f"*.{config.output_format}"))
                processing_status["frame_count"] = len(frames)
                processing_status["output_dir"] = str(video_output_dir)
                # Add frame paths for preview
                if frames:
                    processing_status["frames"] = [
                        str(frame.relative_to(config.output_root)) for frame in frames
                    ]

    # Calculate elapsed time if processing
    if processing_status.get("is_processing") and processing_status.get("start_time"):
        processing_status["elapsed_seconds"] = int(
            time.time() - processing_status["start_time"]
        )
    elif (
        processing_status.get("completed")
        and processing_status.get("start_time")
        and processing_status.get("end_time")
    ):
        processing_status["elapsed_seconds"] = int(
            processing_status["end_time"] - processing_status["start_time"]
        )

    return jsonify(processing_status)


@app.route("/frames", methods=["GET"])
def list_frames():
    """List all extracted frames"""
    if not config.output_root.exists():
        return jsonify({"error": "Output directory does not exist"}), 404

    video_path = request.args.get("video_path")

    result = []
    for video_dir in config.output_root.glob("**/"):
        if video_dir == config.output_root:
            continue

        # If specific video path requested, filter results
        if video_path and video_dir.name != Path(video_path).stem:
            continue

        frames = list(video_dir.glob(f"*.{config.output_format}"))
        if frames:
            result.append(
                {
                    "video_name": video_dir.name,
                    "path": str(video_dir.relative_to(config.output_root)),
                    "frame_count": len(frames),
                    "frames": [str(f.relative_to(config.output_root)) for f in frames],
                }
            )

    return jsonify(result)


@app.route("/frames/<path:frame_path>")
def serve_frame(frame_path):
    """Serve a specific frame"""
    return send_from_directory(str(config.output_root), frame_path)


@app.route("/download_frames", methods=["GET"])
def download_frames():
    """Download frames as a ZIP archive"""
    video_path = request.args.get("video_path")
    if not video_path:
        return jsonify({"error": "Video path parameter is required"}), 400

    # Find the output directory for this video
    video_name = Path(video_path).stem
    video_output_dir = None

    for dir_path in config.output_root.glob("**/"):
        if dir_path.name == video_name:
            video_output_dir = dir_path
            break

    if not video_output_dir or not video_output_dir.exists():
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


@app.route("/create_default_folders", methods=["POST"])
def create_default_folders():
    """Create default folders if they don't exist"""
    try:
        # Create output folder if it doesn't exist
        config.output_root.mkdir(exist_ok=True, parents=True)
        return jsonify({"success": True, "output_folder": str(config.output_root)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Create necessary folders
    static_folder = Path(app.root_path) / "static"
    static_folder.mkdir(exist_ok=True)
    UPLOAD_FOLDER.mkdir(exist_ok=True)

    # Create default output folder
    config.output_root.mkdir(exist_ok=True, parents=True)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
