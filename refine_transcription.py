import os
import sys
import google.generativeai as genai

def refine_transcription(input_transcription_path, output_refined_path):
    # Check if API key exists before configuring
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Google API Key not found.", file=sys.stderr)
        print("Please set the GOOGLE_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)
    
    # Configure the API key
    genai.configure(api_key=api_key)
    # Configure the API key
    # Set up the model
    generation_config = {
        "temperature": 0.5,
        "top_p": 0.95,
        "top_k": 60,
        "max_output_tokens": 400000,
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config,
    )

    with open(input_transcription_path, 'r', encoding='utf-8') as f:
        raw_transcription = f.read()

    system_prompt = """
You are an expert transcriber and text parser. Your task is to process raw transcriptions of a video transcript from an open whisper model
``` rest of system prompt for the specific use case, add number of narrators and context for better refinement
"""

    full_prompt = f"{system_prompt}\n\nActual Transcription to process:\n```\n{raw_transcription}\n```"

    try:
        response = model.generate_content([full_prompt])
        refined_text = response.text
    except Exception as e:
        print(f"Error calling LLM: {e}", file=sys.stderr)
        sys.exit(1)
    # Save the refined transcription
    with open(output_refined_path, 'w+', encoding='utf-8') as f:
        f.write(refined_text)

    print(f"Refined transcription saved to: {output_refined_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python refine_transcription.py <input_transcription_file> <output_refined_file>")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    refine_transcription(input_file, output_file)
