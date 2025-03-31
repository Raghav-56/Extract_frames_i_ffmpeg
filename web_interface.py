__author__ = {"name": "Raghav Gupta", "username": "Raghav-56"}

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_from_directory,
)
from pathlib import Path
import threading

from main import Config, FrameExtractor, logger

app = Flask(__name__, static_folder="static")

config = Config()
extractor = FrameExtractor(config)

processing_status = {
    "is_processing": False,
    "current_video": "",
    "completed": False,
    "error": None,
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/config", methods=["GET"])
def get_config():
    """Get current configuration"""
    current_config = {
        "input_root": str(config.input_root),
        "output_root": str(config.output_root),
        "quality": config.quality,
        "output_format": config.output_format,
    }
    return jsonify(current_config)


def background_process_videos(video_path):
    """Background processor for videos"""
    global processing_status

    try:
        processing_status["is_processing"] = True
        processing_status["completed"] = False
        processing_status["error"] = None

        # Process video
        processing_status["current_video"] = Path(video_path).name
        extractor.process_video(Path(video_path))

        processing_status["completed"] = True
    except Exception as e:
        processing_status["error"] = str(e)
        logger.error(f"Error in background processing: {str(e)}")
    finally:
        processing_status["is_processing"] = False


@app.route("/process", methods=["POST"])
def process_videos():
    """Handle processing request"""
    global processing_status

    if processing_status["is_processing"]:
        return jsonify({"error": "Processing is already in progress"}), 409

    # Get video path and configuration
    video_path = request.form.get("video_path")
    if not video_path:
        return jsonify({"error": "Video path is required"}), 400

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

    return jsonify({"message": "Processing started", "status_endpoint": "/status"})


@app.route("/status", methods=["GET"])
def get_status():
    """Get the current processing status"""
    return jsonify(processing_status)


@app.route("/frames", methods=["GET"])
def list_frames():
    """List all extracted frames"""
    if not config.output_root.exists():
        return jsonify({"error": "Output directory does not exist"}), 404

    result = []
    for video_dir in config.output_root.glob("**/"):
        if video_dir == config.output_root:
            continue

        frames = list(video_dir.glob(f"*.{config.output_format}"))
        if frames:
            result.append(
                {
                    "video_name": video_dir.name,
                    "path": str(video_dir.relative_to(config.output_root)),
                    "frame_count": len(frames),
                    "sample_frame": (
                        str(frames[0].relative_to(config.output_root))
                        if frames
                        else None
                    ),
                }
            )

    return jsonify(result)


@app.route("/frames/<path:frame_path>")
def serve_frame(frame_path):
    """Serve a specific frame"""
    return send_from_directory(str(config.output_root), frame_path)


if __name__ == "__main__":
    # Make sure the static folder exists
    static_folder = Path(app.root_path) / "static"
    static_folder.mkdir(exist_ok=True)

    app.run(debug=True)
