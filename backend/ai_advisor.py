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


def _extract_text(data):
    text = ""
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if part.get("thought"):
                continue
            if "text" in part:
                text += part["text"] + " "
    return text.strip()


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
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        contents = [{"role": "user", "parts": [{"text": prompt}]}]

        # Two configs, tried in order:
        #  1. Thinking disabled -> fast (a few seconds), whole budget goes to the
        #     answer. This is the common, snappy path.
        #  2. If the model rejects thinkingBudget=0 (some newer models do) or
        #     returns no visible text, allow thinking with generous headroom.
        configs = [
            {"maxOutputTokens": 1024, "temperature": 0.7,
             "thinkingConfig": {"thinkingBudget": 0}},
            {"maxOutputTokens": 4096, "temperature": 0.7},
        ]

        for cfg in configs:
            resp = requests.post(
                GEMINI_URL,
                headers=headers,
                json={"contents": contents, "generationConfig": cfg},
                timeout=45,
            )
            if resp.status_code == 200:
                text = _extract_text(resp.json())
                if text:
                    return text
                # 200 but empty (budget spent thinking) -> try the next config.
                continue
            # Non-200: surface the reason. Only a 400 (e.g. thinkingConfig not
            # supported) is worth retrying with the second config.
            print(f"Gemini API Error {resp.status_code}: {resp.text[:300]}")
            if resp.status_code != 400:
                break

        return _fallback(car_row)

    except Exception as e:
        # Log the real reason (bad key, quota, timeout) but never leak the prompt
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
