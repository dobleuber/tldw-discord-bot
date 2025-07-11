"""
Gemini AI service for generating summaries.
"""
import os
import google.generativeai as genai

# Default Gemini model to use
DEFAULT_GEMINI_MODEL = "models/gemini-2.5-flash-lite-preview-06-17"

def setup_gemini():
    """Configure the Gemini AI API.
    
    Raises:
        ValueError: If the GOOGLE_API_KEY environment variable is not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in the .env file")
    genai.configure(api_key=api_key)

async def generate_summary_with_gemini(transcript: str) -> str:
    """Generate a summary of a transcript using Gemini AI.
    
    Args:
        transcript: The transcript to summarize.
        
    Returns:
        A summary of the transcript as a string.
        
    Raises:
        ValueError: If the specified model is not available.
    """
    # Make sure Gemini AI is configured
    setup_gemini()
    
    # Get model name from environment variable or use default
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    
    # Verify if the model is available
    available_models = []
    for model in genai.list_models():
        if "generateContent" in model.supported_generation_methods:
            available_models.append(model.name)
            
    if model_name not in available_models:
        raise ValueError(f"Model {model_name} not available. Available models: {available_models}")
    
    # Create the model instance
    model = genai.GenerativeModel(model_name)
    
    # Create a prompt for the summary
    prompt = f"""Please provide a concise summary of the following transcript from a YouTube video. 
    Focus on the main points and key takeaways. Format the summary as bullet points, omit any sponsorship messages, and self promote: subscribe to our channel, etc.
    
    TRANSCRIPT:
    {transcript}
    """
    
    # Generate the summary
    response = await model.generate_content_async(prompt)
    
    return response.text
