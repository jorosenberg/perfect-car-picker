import json
import boto3
import os
import requests

def get_car_pitch(car_row, priority):
    """
    Uses AWS Bedrock to generate a sales pitch.
    """
    # Construct a prompt based on the car data
    # prompt = f"""
    # Act as a car sales expert. Write a persuasive 2-3 sentence pitch for a {car_row.get('year')} {car_row.get('make')} {car_row.get('model')}.
    # The buyer's top priority is: {priority}.
    # Key specs: {car_row.get('city_mpg')} MPG, {car_row.get('acceleration')}s 0-60, {car_row.get('cargo_space')} cu ft cargo.
    # Explain why this car fits their priority.
    # """
    
    # try:
    #     # AWS Bedrock Client
    #     # Note: In Lambda, this uses the attached IAM Role automatically.
    #     client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
    #     body = json.dumps({
    #         "inputText": prompt,
    #         "textGenerationConfig": {
    #             "maxTokenCount": 150,
    #             "stopSequences": [],
    #             "temperature": 0.7,
    #             "topP": 1
    #         }
    #     })
        
    #     response = client.invoke_model(
    #         modelId='amazon.titan-text-express-v1',
    #         contentType='application/json',
    #         accept='application/json',
    #         body=body
    #     )
        
    #     response_body = json.loads(response.get('body').read())
    #     return response_body.get('results')[0].get('outputText').strip()
        
    # except Exception as e:
    #     print(f"Bedrock Error: {e}")
    #     return f"This {car_row.get('model')} is an excellent choice for {priority}. (AI Pitch unavailable)."


    ## HUGGING FACE implementation while bedrock doesn't work ##

    api_key = os.environ.get('HF_API_KEY')
    # Using Zephyr as it's often more available on the free inference API than base Mistral
    api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
    headers = {"Authorization": f"Bearer {api_key}"}

    # Prompt engineering for Zephyr/Mistral
    prompt = f"<|system|>\nYou are a car sales expert.<|user|>\nWrite a persuasive, enthusiastic single sentence selling the {car_row.get('year')} {car_row.get('make')} {car_row.get('model')} to a buyer who cares most about {priority}. Mention one specific stat from: {car_row.get('city_mpg')} mpg, {car_row.get('acceleration')}s 0-60, or {car_row.get('cargo_space')} cu-ft cargo.<|assistant|>\n"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 60, 
            "return_full_text": False,
            "temperature": 0.7
        }
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=8)
    response.raise_for_status()
    
    # Clean up response
    text = response.json()[0]['generated_text'].strip()
    if '"' in text and text.count('"') % 2 == 0:
        text = text.replace('"', '')
    return text