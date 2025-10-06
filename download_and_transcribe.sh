#!/bin/bash

# Check if an input URL is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <video_url> [output_refined_transcription_file]"
  exit 1
fi

VIDEO_URL="$1"
# Default output file for the refined transcription
OUTPUT_REFINED_TRANSCRIPTION_FILE="${2:-refined_transcription.txt}"

# Create a temporary directory for downloaded videos and intermediate transcription
TEMP_DIR=$(mktemp -d -t video_processing_XXXX)
echo "Created temporary directory: $TEMP_DIR"

# Define paths for intermediate files
RAW_TRANSCRIPTION_FILE="$TEMP_DIR/raw_transcription.txt"
DOWNLOADED_VIDEO_PATH="" # Will be set after download

# --- Step 1: Download the video ---
echo "Downloading video from $VIDEO_URL to $TEMP_DIR..."
python generic_video_downloader.py "$VIDEO_URL" -o "$TEMP_DIR"

# Find the downloaded video file
DOWNLOADED_VIDEO_PATH=$(find "$TEMP_DIR" -type f -print -quit)

if [ -z "$DOWNLOADED_VIDEO_PATH" ]; then
  echo "Error: No video file found in $TEMP_DIR after download."
  rm -rf "$TEMP_DIR"
  exit 1
fi

echo "Video downloaded to: $DOWNLOADED_VIDEO_PATH"

# --- Step 2: Transcribe the video ---
echo "Transcribing video and saving raw transcription to $RAW_TRANSCRIPTION_FILE..."
python transcribe.py "$DOWNLOADED_VIDEO_PATH" > "$RAW_TRANSCRIPTION_FILE"

if [ ! -s "$RAW_TRANSCRIPTION_FILE" ]; then
  echo "Error: Raw transcription file is empty or not created."
  rm -rf "$TEMP_DIR"
  exit 1
fi

echo "Raw transcription saved to: $RAW_TRANSCRIPTION_FILE"

# --- Step 3: Refine the transcription using the LLM ---
echo "Refining transcription using Google Flash 2.5 LLM..."
python refine_transcription.py "$RAW_TRANSCRIPTION_FILE" "$OUTPUT_REFINED_TRANSCRIPTION_FILE"

if [ ! -s "$OUTPUT_REFINED_TRANSCRIPTION_FILE" ]; then
  echo "Error: Refined transcription file is empty or not created."
  # Attempt to print the raw transcription for debugging if LLM failed
  echo "Contents of raw transcription for debugging:"
  cat "$RAW_TRANSCRIPTION_FILE"
  # rm -rf "$TEMP_DIR"
  exit 1
fi

echo "Final refined transcription saved to: $OUTPUT_REFINED_TRANSCRIPTION_FILE"

# Clean up the temporary directory
echo "Cleaning up temporary directory: $TEMP_DIR..."
rm -rf "$TEMP_DIR"
echo "Done."
