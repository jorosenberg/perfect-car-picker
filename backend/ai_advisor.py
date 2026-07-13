import os
import requests

# Google Gemini (free tier) replaces AWS Bedrock Nova - same behavior:
# generates a short, persuasive sales pitch for a vehicle.
# Set GEMINI_API_KEY in the environment (aistudio.google.com/apikey, no card needed).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def get_car_pitch(car_row, priority):
    """
    Uses Google Gemini (free tier) to generate a sales pitch.
    (1:1 port of the AWS Bedrock Nova version - same prompt, graceful fallback.)
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
                    continue
                if "text" in part:
                    final_text += part["text"] + " "

        if final_text.strip():
            return final_text.strip()

        return _fallback(car_row)

    except Exception as e:
        # Log the real reason (bad key, quota, etc.) but never leak the prompt
        # or the (long) priority instruction back to the UI.
        print(f"Gemini API Error: {e}")
        return _fallback(car_row)


def _fallback(car_row):
    # Clean, generic pitch used when the AI call is unavailable. Deliberately
    # does NOT echo the caller's priority string, which can be a long
    # instruction and would otherwise look like a leaked prompt in the UI.
    year = car_row.get("year", "")
    make = car_row.get("make", "this")
    model = car_row.get("model", "vehicle")
    features = car_row.get("features")
    base = f"The {year} {make} {model} is a strong, well-rounded match for your needs."
    if features:
        first = str(features).split(",")[0].strip()
        if first:
            base += f" Notable feature: {first}."
    return base
