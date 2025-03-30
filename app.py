from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, session
import os
import tempfile
import uuid
import subprocess
import sys
from werkzeug.utils import secure_filename
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'keyframe-extractor-secret-key'

# Configuration
UPLOAD_FOLDER = Path('static/uploads')
FRAMES_FOLDER = Path('static/frames')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# Create directories if they don't exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
FRAMES_FOLDER.mkdir(parents=True, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FRAMES_FOLDER'] = FRAMES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload size

# Try to import from the existing project
try:
    sys.path.append(str(Path(__file__).parent / 'Extract_frames_i_ffmpeg'))
    from Extract_frames_i_ffmpeg.config.defaults import DEFAULT_FFMPEG_PATH
    FFMPEG_PATH = DEFAULT_FFMPEG_PATH
except ImportError:
    # Default to 'ffmpeg' command if module not found
    FFMPEG_PATH = 'ffmpeg'

def find_ffmpeg():
    """Find the FFmpeg executable"""
    # Check if path is stored in session
    if 'ffmpeg_path' in session and Path(session['ffmpeg_path']).exists():
        return session['ffmpeg_path']
    
    # First try using the configured path
    if FFMPEG_PATH and Path(FFMPEG_PATH).exists():
        return str(FFMPEG_PATH)
    
    # Try to find ffmpeg in common locations
    common_locations = [
        'ffmpeg',
        'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Users\\priya\\Downloads\\ffmpeg-master-latest-win64-gpl-shared\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe',
        Path(__file__).parent / 'Extract_frames_i_ffmpeg' / 'ffmpeg.exe',
        # Add current user's Downloads folder as a fallback
        Path.home() / 'Downloads' / 'ffmpeg-master-latest-win64-gpl-shared' / 'ffmpeg-master-latest-win64-gpl-shared' / 'bin' / 'ffmpeg.exe'
    ]
    
    for location in common_locations:
        try:
            location_str = str(location)
            # Check if we can run ffmpeg -version
            result = subprocess.run([location_str, '-version'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return location_str
        except FileNotFoundError:
            continue
    
    raise FileNotFoundError("FFmpeg executable not found. Please install FFmpeg or provide the correct path.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_keyframes(video_path, output_dir):
    """Extract I-frames from the video using FFmpeg"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find ffmpeg executable
    ffmpeg_path = find_ffmpeg()
    
    # Build FFmpeg command to extract I-frames
    cmd = [
        ffmpeg_path,
        '-i', str(video_path),
        '-vf', "select='eq(pict_type,I)'",
        '-vsync', 'vfr',
        '-q:v', '1',
        '-f', 'image2',
        f'{output_dir}/frame_%04d.png'
    ]
    
    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    
    # Return list of extracted frames
    frames = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
    return frames

def check_templates():
    """Check if templates directory and required templates exist"""
    templates_dir = Path(__file__).parent / 'templates'
    if not templates_dir.exists():
        print(f"WARNING: Templates directory not found: {templates_dir}")
        return False
    
    required_templates = ['index.html', 'results.html', 'ffmpeg_status.html', 'set_ffmpeg_path.html']
    missing_templates = []
    
    for template in required_templates:
        if not (templates_dir / template).exists():
            missing_templates.append(template)
    
    if missing_templates:
        print(f"WARNING: Missing templates: {', '.join(missing_templates)}")
        return False
    
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file part exists in the request
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    # Check if file is allowed
    if file and allowed_file(file.filename):
        # Generate unique ID for this upload
        session_id = str(uuid.uuid4())
        
        # Create directories for this session
        session_upload_dir = app.config['UPLOAD_FOLDER'] / session_id
        session_frames_dir = app.config['FRAMES_FOLDER'] / session_id
        os.makedirs(session_upload_dir, exist_ok=True)
        os.makedirs(session_frames_dir, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = session_upload_dir / filename
        file.save(file_path)
        
        try:
            # Extract keyframes
            frames = extract_keyframes(file_path, session_frames_dir)
            
            # Redirect to results page
            return redirect(url_for('results', session_id=session_id))
        except Exception as e:
            flash(f"Error processing video: {str(e)}")
            return redirect(url_for('index'))
    
    flash('File type not allowed')
    return redirect(url_for('index'))

@app.route('/results/<session_id>')
def results(session_id):
    # Get all frames for this session
    frames_dir = app.config['FRAMES_FOLDER'] / session_id
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
    
    if not frames:
        flash('No frames were extracted from this video')
        return redirect(url_for('index'))
    
    return render_template('results.html', 
                          session_id=session_id, 
                          frames=frames)

@app.route('/frames/<session_id>/<filename>')
def serve_frame(session_id, filename):
    return send_from_directory(app.config['FRAMES_FOLDER'] / session_id, filename)

@app.route('/ffmpeg-status')
def ffmpeg_status():
    """Check FFmpeg availability and return status"""
    try:
        ffmpeg_path = find_ffmpeg()
        result = subprocess.run([ffmpeg_path, '-version'], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0:
            # Extract version info from the output
            version_info = result.stdout.split('\n')[0] if result.stdout else "FFmpeg found"
            return render_template('ffmpeg_status.html', 
                                  status="available", 
                                  version=version_info,
                                  path=ffmpeg_path)
        else:
            return render_template('ffmpeg_status.html', 
                                  status="error",
                                  error=result.stderr)
    except Exception as e:
        return render_template('ffmpeg_status.html', 
                              status="not_found",
                              error=str(e))

@app.route('/set-ffmpeg-path', methods=['GET', 'POST'])
def set_ffmpeg_path():
    if request.method == 'POST':
        ffmpeg_path = request.form.get('ffmpeg_path')
        if ffmpeg_path:
            # Validate the path
            path = Path(ffmpeg_path)
            if path.exists() and path.is_file():
                try:
                    # Test if it's actually ffmpeg
                    result = subprocess.run([str(path), '-version'], 
                                          capture_output=True, text=True, check=True)
                    # Store in session
                    session['ffmpeg_path'] = str(path)
                    flash('FFmpeg path successfully set!', 'success')
                    return redirect(url_for('ffmpeg_status'))
                except (subprocess.SubprocessError, OSError):
                    flash('The specified file is not a valid FFmpeg executable.', 'danger')
            else:
                flash('The specified path does not exist or is not a file.', 'danger')
        else:
            flash('Please provide a valid path.', 'danger')
    
    return render_template('set_ffmpeg_path.html')

if __name__ == "__main__":
    try:
        # Check templates first
        if not check_templates():
            print("WARNING: Some templates are missing. The application may not work correctly.")
        
        # Make sure to use host='127.0.0.1' instead of '0.0.0.0' which might cause issues
        print("Starting Flask application...")
        print("Open your browser and navigate to: http://localhost:5000")
        print("Press CTRL+C to stop the server")
        app.run(debug=True, host='127.0.0.1', port=5000)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"ERROR: Port 5000 is already in use.")
            print("Try using a different port with:")
            print("python -m flask --app app run --port 8080")
        else:
            print(f"Error starting Flask application: {str(e)}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"Error starting Flask application: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nTry running the application with:")
        print("python -m flask --app app run --debug")
        input("Press Enter to exit...")