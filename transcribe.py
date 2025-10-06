from faster_whisper import WhisperModel
import sys
import os

WHISPER_MODEL = 'medium' # try small or large variants as per requirements
# You can specify the device. 'cuda' for NVIDIA GPUs, 'cpu' for CPU, or 'cpu' for Apple Silicon.
# If you have a CUDA-enabled GPU, 'cuda' would generally be faster.
DEVICE = 'cpu'
COMPUTE_TYPE = 'int8' # Use int8 for quantized model as suggested in the documentation

def transcribe_audio(file_path):
    """Transcribes the given audio file using a faster Whisper model."""
    # Load the model with specified device and compute type for optimized performance
    model = WhisperModel(WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
    segments, info = model.transcribe(file_path, beam_size=5)

    transcript_parts = []
    for segment in segments:
        transcript_parts.append(segment.text)
    return "".join(transcript_parts)


def main(audio_file=None):
    if len(sys.argv) < 2 and audio_file is None:
        print("Usage: python ingest.py <path_to_audio_file>")
        return

    audio_file_path = sys.argv[1] if audio_file is None else audio_file

    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at '{audio_file_path}'")
        return

    transcript = transcribe_audio(audio_file_path)

    print(transcript)

if __name__ == "__main__":
    main()
