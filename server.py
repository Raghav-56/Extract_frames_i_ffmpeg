from fastapi import FastAPI, Request, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import os
import tempfile
import shutil
import base64
from typing import Optional, List
from dotenv import load_dotenv
from main import extract_frames_for_web
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
    output_dir_name = f"upload_{Path(video.filename).stem}"
    temp_output_dir = Path(STATIC_ROOT) / output_dir_name
    temp_output_dir.mkdir(parents=True, exist_ok=True)
    temp_video_path = temp_output_dir / f"upload_{video.filename}"
    with open(temp_video_path, "wb") as buffer:
        content = await video.read()
        buffer.write(content)
    frames = extract_frames_for_web(
        input_path=str(temp_video_path),
        output_dir=str(temp_output_dir),
        progress_callback=None,
    )
    # Remove the uploaded video after extraction
    try:
        temp_video_path.unlink(missing_ok=True)
    except Exception:
        pass
    if not frames:
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        return JSONResponse(
            {"error": "No I-frames found in the video."}, status_code=404
        )
    frame_data = []
    frame_paths = []
    if isinstance(frames, dict):
        for video_name, frame_list in frames.items():
            frame_paths.extend(frame_list)
    elif isinstance(frames, list):
        frame_paths = frames
    for frame_path in frame_paths:
        full_path = temp_output_dir / Path(frame_path).name
        if full_path.exists():
            with open(full_path, "rb") as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode("utf-8")
                frame_data.append(
                    {
                        "filename": Path(frame_path).name,
                        "data": f"data:image/jpeg;base64,{img_base64}",
                    }
                )
    # Optionally, clean up the frames after sending (uncomment if you want to auto-delete)
    # shutil.rmtree(temp_output_dir, ignore_errors=True)
    return {
        "message": "Frames extracted successfully",
        "video_filename": video.filename,
        "frame_count": len(frame_data),
        "frames": frame_data,
    }


@app.post("/upload-urls")
async def upload_and_extract_urls(video: UploadFile = File(...)):
    if not video.content_type or not video.content_type.startswith("video/"):
        return JSONResponse(
            {"error": "Invalid file type. Please upload a video file."}, status_code=400
        )
    temp_dir = tempfile.mkdtemp()
    temp_video_path = Path(temp_dir) / f"upload_{video.filename}"
    output_dir_name = f"upload_{Path(video.filename).stem}"
    output_dir = Path(STATIC_ROOT) / output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(temp_video_path, "wb") as buffer:
        content = await video.read()
        buffer.write(content)
    frames = extract_frames_for_web(
        input_path=str(temp_video_path),
        output_dir=str(output_dir),
        progress_callback=None,
    )
    if not frames:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return JSONResponse(
            {"error": "No I-frames found in the video."}, status_code=404
        )
    frame_urls = []
    frame_paths = []
    if isinstance(frames, dict):
        for video_name, frame_list in frames.items():
            frame_paths.extend(frame_list)
    elif isinstance(frames, list):
        frame_paths = frames
    for frame_path in frame_paths:
        relative_path = Path(frame_path).relative_to(Path(STATIC_ROOT))
        replaced = str(relative_path).replace("\\", "/")
        url = f"/frames-static/{replaced}"
        frame_urls.append({"filename": Path(frame_path).name, "url": url})
    shutil.rmtree(temp_dir, ignore_errors=True)
    return {
        "message": "Frames extracted successfully",
        "video_filename": video.filename,
        "frame_count": len(frame_urls),
        "frames": frame_urls,
        "output_directory": str(output_dir),
    }


@app.get("/")
async def root():
    """Serve the test page"""
    return FileResponse("test_upload.html")
