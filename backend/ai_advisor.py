import os
import requests

# Google Gemini (free tier) replaces AWS Bedrock Nova - same behavior:
# short reasoning-capable model generates the sales pitch.
# Set GEMINI_API_KEY in the environment (aistudio.google.com/apikey, no card needed).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def get_car_pitch(car_row, priority):
    """
    Uses Google Gemini (free tier) to generate a sales pitch.
    (1:1 port of the AWS Bedrock Nova version - same prompt, same fallback.)
    """

    prompt = f"""
    Act as a car sales expert. Write a persuasive 2-3 sentence pitch for a {car_row.get('year')} {car_row.get('make')} {car_row.get('model')}.
    The buyer's top priority is: {priority}.
    Key specs: {car_row.get('city_mpg')} MPG, {car_row.get('acceleration')}s 0-60, {car_row.get('cargo_space')} cu ft cargo.
    Review Insights: {car_row.get('review_summary')}
    Notable Features: {car_row.get('features')}

    Explain why this car fits their priority. Be sure to highlight the 'Pros' from the review insights and explicitly list out some of the best vehicle features.
    """

    try:
        api_key = os.environ["GEMINI_API_KEY"]

        response = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": 1000,
                    "temperature": 0.7,
                    # mirrors Nova's "low" reasoning effort
                    "thinkingConfig": {"thinkingBudget": 128},
                },
            },
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()

        final_text = ""
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if part.get("thought"):
                    print("Gemini is reasoning... (Logging hidden from user)")
                    continue
                if "text" in part:
                    final_text += part["text"] + " "

        if final_text.strip():
            return final_text.strip()

        return "Pitch generated but format unrecognized."

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"This {car_row.get('model')} is a fantastic choice for {priority}."
