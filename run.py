"""
Simple script to run the Flask application.
This provides better error reporting and helps troubleshoot startup issues.
"""

import os
import sys
from pathlib import Path

# Ensure we're in the correct directory
os.chdir(Path(__file__).parent)

# Try to import Flask
try:
    from flask import Flask
    print("Flask is installed.")
except ImportError:
    print("ERROR: Flask is not installed.")
    print("Please install it with: pip install flask")
    sys.exit(1)

# Try to run the app
try:
    print("Starting application...")
    print("=" * 50)
    
    # Try different ports if 5000 is not available
    ports_to_try = [5000, 8080, 3000, 8000]
    
    for port in ports_to_try:
        try:
            print(f"Trying to start server on port {port}...")
            print(f"Open your browser and navigate to: http://localhost:{port}")
            print("Press CTRL+C to stop the server")
            print("=" * 50)
            
            # Import the app
            from app import app
            app.run(debug=True, host='127.0.0.1', port=port)
            break  # If successful, exit the loop
            
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} is already in use, trying another port...")
            else:
                raise  # Re-raise if it's a different OSError
    
except Exception as e:
    print(f"\nERROR: Could not start the application: {str(e)}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("TROUBLESHOOTING STEPS:")
    print("1. Make sure all required packages are installed:")
    print("   pip install flask werkzeug")
    print("\n2. Check FFmpeg installation:")
    print("   Make sure FFmpeg is installed and in your PATH")
    print(f"   Check C:\\Users\\priya\\Downloads\\ffmpeg-master-latest-win64-gpl-shared\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffmpeg.exe")
    print("\n3. Try running with Python directly:")
    print("   python -m flask --app app run --debug")
    print("=" * 50)
    
    input("\nPress Enter to exit...")
