import shutil
import base64
from pathlib import Path
from main import extract_frames_for_web
from lib.video_filename_parser import parse_video_filename
import tempfile


def save_upload_file(upload_file, destination: Path) -> Path:
    """Save uploaded file to destination and return the path."""
    with open(destination, "wb") as buffer:
        content = upload_file.file.read()
        buffer.write(content)
    return destination


def extract_and_encode_frames(temp_video_path, temp_output_dir):
    """Extract frames and encode them as base64."""
    frames = extract_frames_for_web(
        input_path=str(temp_video_path),
        output_dir=str(temp_output_dir),
        progress_callback=None,
    )
    if not frames:
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        return None, None
    frame_data = []
    frame_paths = []
    if isinstance(frames, dict):
        for video_name, frame_list in frames.items():
            frame_paths.extend(frame_list)
    elif isinstance(frames, list):
        frame_paths = frames
    for frame_path in frame_paths:
        full_path = (temp_output_dir / frame_path).resolve()
        if not full_path.exists():
            alt_path = temp_output_dir / Path(frame_path).name
            if alt_path.exists():
                full_path = alt_path
            else:
                continue
        with open(full_path, "rb") as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            frame_data.append(
                {
                    "filename": Path(frame_path).name,
                    "data": f"data:image/jpeg;base64,{img_base64}",
                }
            )
    return frame_data, frame_paths


def handle_upload_and_extract(video, static_root):
    output_dir_name = f"upload_{Path(video.filename).stem}"
    temp_output_dir = Path(static_root) / output_dir_name
    temp_output_dir.mkdir(parents=True, exist_ok=True)
    temp_video_path = temp_output_dir / f"upload_{video.filename}"
    # Save file
    with open(temp_video_path, "wb") as buffer:
        content = video.file.read()
        buffer.write(content)
    frame_data, _ = extract_and_encode_frames(temp_video_path, temp_output_dir)
    # Remove the uploaded video after extraction
    try:
        temp_video_path.unlink(missing_ok=True)
    except Exception:
        pass
    if not frame_data:
        return None, None, None
    video_info = parse_video_filename(video.filename)
    return frame_data, video.filename, video_info


def handle_upload_and_extract_urls(video, static_root):
    temp_dir = tempfile.mkdtemp()
    temp_video_path = Path(temp_dir) / f"upload_{video.filename}"
    output_dir_name = f"upload_{Path(video.filename).stem}"
    output_dir = Path(static_root) / output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(temp_video_path, "wb") as buffer:
        content = video.file.read()
        buffer.write(content)
    frames = extract_frames_for_web(
        input_path=str(temp_video_path),
        output_dir=str(output_dir),
        progress_callback=None,
    )
    if not frames:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None, None, None, None
    frame_urls = []
    frame_paths = []
    if isinstance(frames, dict):
        for video_name, frame_list in frames.items():
            frame_paths.extend(frame_list)
    elif isinstance(frames, list):
        frame_paths = frames
    video_info = parse_video_filename(video.filename)
    for frame_path in frame_paths:
        relative_path = Path(frame_path).relative_to(Path(static_root))
        replaced = str(relative_path).replace("\\", "/")
        url = f"/frames-static/{replaced}"
        frame_urls.append({"filename": Path(frame_path).name, "url": url})
    shutil.rmtree(temp_dir, ignore_errors=True)
    return frame_urls, video.filename, output_dir, video_info
