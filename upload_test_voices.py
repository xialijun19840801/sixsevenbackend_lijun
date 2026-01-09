#!/usr/bin/env python3
"""
Script to convert voice files from test_files to WAV format,
upload them to Firebase bucket, and save them to the voices collection.
"""

import os
import uuid
from pathlib import Path
from firebase.firebase_init import initialize_firebase
from firebase_service import FirebaseService

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    print("pydub imported successfully")
except ImportError as e:
    PYDUB_AVAILABLE = False
    print(f"Warning: pydub not available ({e}). Will try ffmpeg directly...")

def convert_to_wav(input_path: str, output_path: str) -> bool:
    """
    Convert audio file to WAV format.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to output WAV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Try using ffmpeg directly (most reliable for m4a files)
        import subprocess
        import shutil
        
        # Check if ffmpeg is available
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            print("ERROR: ffmpeg is not installed or not in PATH")
            print("Please install ffmpeg:")
            print("  macOS: brew install ffmpeg")
            print("  Linux: sudo apt-get install ffmpeg (or similar)")
            print("  Windows: Download from https://ffmpeg.org/download.html")
            return False
        
        print(f"Converting {input_path} to WAV using ffmpeg...")
        result = subprocess.run(
            [ffmpeg_path, '-i', input_path, '-y', '-ar', '44100', '-ac', '1', output_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"Successfully converted {input_path} to {output_path}")
            return True
        else:
            print(f"Error converting {input_path}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error converting {input_path} to WAV: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def process_voice_file(file_path: str, creator_id: str = 'test'):
    """
    Process a single voice file: convert to WAV, upload to Firebase, and save to voices collection.
    
    Args:
        file_path: Path to the voice file
        creator_id: Creator ID for the voice (default: 'test')
    """
    try:
        # Get filename without extension for voice_name
        file_name = Path(file_path).stem
        file_ext = Path(file_path).suffix
        
        print(f"\nProcessing {file_path}...")
        print(f"Voice name will be: {file_name}")
        
        # Generate random voice_id
        voice_id = str(uuid.uuid4())
        print(f"Generated voice_id: {voice_id}")
        
        # Convert to WAV
        wav_output_path = os.path.join('test_data', f"{file_name}.wav")
        os.makedirs('test_data', exist_ok=True)
        
        if not convert_to_wav(file_path, wav_output_path):
            print(f"Failed to convert {file_path} to WAV")
            return False
        
        # Read WAV file
        with open(wav_output_path, 'rb') as f:
            wav_data = f.read()
        
        print(f"WAV file size: {len(wav_data)} bytes")
        
        # Upload to Firebase bucket
        bucket_path = f"voices/{voice_id}.wav"
        print(f"Uploading to Firebase bucket: {bucket_path}")
        voice_url, file_size = FirebaseService.save_to_bucket(
            bucket_path,
            wav_data,
            content_type='audio/wav'
        )
        print(f"Uploaded successfully. URL: {voice_url}")
        
        # Save to voices collection
        print(f"Saving to voices collection...")
        voice_data = FirebaseService.add_voice(
            voice_id=voice_id,
            creator_id=creator_id,
            voice_name=file_name,
            voice_url=voice_url
        )
        print(f"Saved to voices collection: {voice_data}")
        
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to process all voice files in test_files directory."""
    # Initialize Firebase
    print("Initializing Firebase...")
    try:
        initialize_firebase()
        print("Firebase initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Firebase: {str(e)}")
        return
    
    # Get all audio files from test_files directory
    test_files_dir = Path('test_files')
    if not test_files_dir.exists():
        print(f"Error: {test_files_dir} directory does not exist")
        return
    
    # Find all audio files (m4a, mp3, wav, etc.)
    audio_files = []
    for ext in ['.m4a', '.mp3', '.wav', '.aac', '.ogg']:
        audio_files.extend(list(test_files_dir.glob(f'*{ext}')))
    
    if not audio_files:
        print(f"No audio files found in {test_files_dir}")
        return
    
    print(f"\nFound {len(audio_files)} audio file(s) to process:")
    for f in audio_files:
        print(f"  - {f.name}")
    
    # Process each file
    success_count = 0
    for audio_file in audio_files:
        if process_voice_file(str(audio_file), creator_id='test'):
            success_count += 1
        else:
            print(f"Failed to process {audio_file.name}")
    
    print(f"\n{'='*50}")
    print(f"Processing complete: {success_count}/{len(audio_files)} files processed successfully")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()

