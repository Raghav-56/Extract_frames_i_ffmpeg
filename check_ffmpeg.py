"""
Check if FFmpeg is available and working in the system.
"""

import os
import subprocess
from pathlib import Path

def check_path_exists(path):
    """Check if a file exists at the given path"""
    try:
        path_obj = Path(path)
        if path_obj.exists():
            return f"✅ File exists: {path_obj.absolute()}"
        else:
            return f"❌ File NOT found: {path_obj.absolute()}"
    except Exception as e:
        return f"❌ Error checking path: {e}"

def run_ffmpeg_test(ffmpeg_path="ffmpeg"):
    """Try to run FFmpeg and get version info"""
    try:
        result = subprocess.run([ffmpeg_path, "-version"], 
                               capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            return f"✅ FFmpeg is working: {version}"
        else:
            return f"❌ FFmpeg error: {result.stderr}"
    except FileNotFoundError:
        return f"❌ FFmpeg not found at path: {ffmpeg_path}"
    except Exception as e:
        return f"❌ Error running FFmpeg: {e}"

def main():
    print("=" * 60)
    print("FFmpeg Checker - Troubleshooting Tool")
    print("=" * 60)
    
    # Check common paths
    print("\nChecking common FFmpeg locations:")
    paths_to_check = [
        "ffmpeg",
        "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\Users\\priya\\Downloads\\ffmpeg-master-latest-win64-gpl-shared\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe",
    ]
    
    for path in paths_to_check:
        print(f"- {check_path_exists(path)}")
    
    # Check PATH environment variable
    print("\nChecking system PATH:")
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    ffmpeg_found_in_path = False
    
    for directory in path_dirs:
        ffmpeg_path = Path(directory) / "ffmpeg.exe"
        if ffmpeg_path.exists():
            ffmpeg_found_in_path = True
            print(f"✅ FFmpeg found in PATH: {ffmpeg_path}")
    
    if not ffmpeg_found_in_path:
        print("❌ FFmpeg not found in any PATH directory")
    
    # Try to run FFmpeg
    print("\nTrying to run FFmpeg:")
    print(run_ffmpeg_test())
    
    # Try the specific path
    specific_path = "C:\\Users\\priya\\Downloads\\ffmpeg-master-latest-win64-gpl-shared\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe"
    print(f"\nTrying to run FFmpeg at specific path:")
    print(run_ffmpeg_test(specific_path))
    
    print("\n" + "=" * 60)
    print("Troubleshooting recommendations:")
    print("1. If FFmpeg is not found, download it from: https://ffmpeg.org/download.html")
    print("2. Extract the downloaded files to C:\\ffmpeg")
    print("3. Add C:\\ffmpeg\\bin to your PATH environment variable")
    print("4. Restart your command prompt and try again")
    print("=" * 60)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
