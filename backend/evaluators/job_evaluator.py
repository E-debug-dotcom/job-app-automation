import os
import json
import openai
from pathlib import Path

# Load OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def evaluate_job(job_title, job_description, company, location, user_cv=None):
    """
    Evaluate a job using AI based on title, description, etc.
    Returns a score (0-5) and notes.
    """
    if not openai.api_key:
        return {"score": 0, "notes": "OpenAI API key not set. Set OPENAI_API_KEY environment variable."}

    # Load user CV if available
    cv_text = ""
    if user_cv:
        cv_path = ROOT_DIR / "data" / user_cv
        if cv_path.exists():
            with open(cv_path, 'r') as f:
                cv_text = f.read()

    prompt = f"""
    Evaluate the following job opportunity on a scale of 1-5 (5 being best fit) based on typical software engineering criteria.
    Consider role fit, company reputation, location, and skills match.

    Job Title: {job_title}
    Company: {company}
    Location: {location}
    Description: {job_description[:1000]}  # Truncate for token limit

    User CV Summary: {cv_text[:500] if cv_text else "No CV provided"}

    Provide a JSON response with "score" (float) and "notes" (string).
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        result = json.loads(response.choices[0].message.content.strip())
        return result
    except Exception as e:
        return {"score": 0, "notes": f"Error evaluating job: {str(e)}"}

if __name__ == "__main__":
    # Example usage
    result = evaluate_job("Software Engineer", "Build AI systems...", "Anthropic", "Remote")
    print(result)