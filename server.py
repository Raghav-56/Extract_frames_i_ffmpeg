from fastapi import FastAPI, Request, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import os


from dotenv import load_dotenv
from main import extract_frames_for_web
from services.frame_extraction_service import (
    handle_upload_and_extract,
    handle_upload_and_extract_urls,
)
import threading
from pathlib import Path


app = FastAPI(
    title="Frame Extraction API",
    description="Extract I-frames from videos using FFmpeg.",
)


status = {
    "is_processing": False,
    "progress": 0,
    "error": None,
    "frames": [],
    "output_dir": None,
}
status_lock = threading.Lock()


# Load environment variables from .env file
load_dotenv()
STATIC_ROOT = os.environ.get("STATIC_ROOT", "extracted_frames")
os.makedirs(STATIC_ROOT, exist_ok=True)
app.mount("/frames-static", StaticFiles(directory=STATIC_ROOT), name="frames-static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(request: Request, background_tasks: BackgroundTasks):
    with status_lock:
        if status["is_processing"]:
            return JSONResponse(
                {"error": "Processing already in progress"}, status_code=409
            )

    data = await request.json()
    input_path = data.get("input_path")
    output_dir = data.get("output_dir")
    if not input_path:
        return JSONResponse({"error": "Missing input_path"}, status_code=400)

    if output_dir:
        output_dir_path = Path(output_dir).resolve()
        static_root_path = Path(STATIC_ROOT).resolve()
        if not str(output_dir_path).startswith(str(static_root_path)):
            return JSONResponse(
                {"error": "output_dir must be inside the static root directory."},
                status_code=400,
            )
    else:
        output_dir = STATIC_ROOT

    def progress_callback(current, total):
        with status_lock:
            status["progress"] = int((current / total) * 100) if total else 0

    def process():
        with status_lock:
            status["is_processing"] = True
            status["progress"] = 0
            status["error"] = None
            status["frames"] = []
            status["output_dir"] = output_dir
        try:
            frames = extract_frames_for_web(
                input_path=input_path,
                output_dir=output_dir,
                progress_callback=progress_callback,
            )
            frame_urls = []
            if frames:
                if isinstance(frames, dict):
                    for video, frame_list in frames.items():
                        for f in frame_list:
                            replaced = f.replace("\\", "/").lstrip("/")
                            frame_urls.append(f"/frames-static/{replaced}")
                elif isinstance(frames, list):
                    for f in frames:
                        replaced = f.replace("\\", "/").lstrip("/")
                        frame_urls.append(f"/frames-static/{replaced}")
            with status_lock:
                status["frames"] = frame_urls
        except Exception as e:
            with status_lock:
                status["error"] = str(e)
        finally:
            with status_lock:
                status["is_processing"] = False
                status["progress"] = 100

    background_tasks.add_task(process)
    return {"message": "Extraction started"}


@app.get("/status")
async def get_status():
    with status_lock:
        return status.copy()


@app.get("/frames")
async def get_frames():
    with status_lock:
        return {"frames": status.get("frames", [])}


@app.post("/upload")
async def upload_and_extract(video: UploadFile = File(...)):
    if not video.content_type or not video.content_type.startswith("video/"):
        return JSONResponse(
            {"error": "Invalid file type. Please upload a video file."}, status_code=400
        )
    # Use the service function
    frame_data, video_filename, video_info = handle_upload_and_extract(
        video, STATIC_ROOT
    )
    if not frame_data:
        return JSONResponse(
            {"error": "No I-frames found in the video."}, status_code=404
        )
    return {
        "message": "Frames extracted successfully",
        "video_filename": video_filename,
        "frame_count": len(frame_data),
        "frames": frame_data,
        "video_info": video_info,
    }


@app.post("/upload-urls")
async def upload_and_extract_urls(video: UploadFile = File(...)):
    if not video.content_type or not video.content_type.startswith("video/"):
        return JSONResponse(
            {"error": "Invalid file type. Please upload a video file."}, status_code=400
        )
    frame_urls, video_filename, output_dir, video_info = handle_upload_and_extract_urls(
        video, STATIC_ROOT
    )
    if not frame_urls:
        return JSONResponse(
            {"error": "No I-frames found in the video."}, status_code=404
        )
    return {
        "message": "Frames extracted successfully",
        "video_filename": video_filename,
        "frame_count": len(frame_urls),
        "frames": frame_urls,
        "output_directory": str(output_dir),
        "video_info": video_info,
    }


@app.get("/")
async def root():
    """Serve the test page"""
    return FileResponse("test_upload.html")
