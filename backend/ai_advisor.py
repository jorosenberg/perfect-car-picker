import json
import boto3

def get_car_pitch(car_row, priority):
    """
    Uses AWS Bedrock to generate a sales pitch.
    """
    # Construct a prompt based on the car data
    prompt = f"""
    Act as a car sales expert. Write a persuasive 2-3 sentence pitch for a {car_row.get('year')} {car_row.get('make')} {car_row.get('model')}.
    The buyer's top priority is: {priority}.
    Key specs: {car_row.get('city_mpg')} MPG, {car_row.get('acceleration')}s 0-60, {car_row.get('cargo_space')} cu ft cargo.
    Explain why this car fits their priority.
    """
    
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    try:
        response = client.converse(
        modelId='amazon.nova-micro-v1:0', 
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        inferenceConfig={
            "maxTokens": 60,
            "temperature": 0.7
            }
        )
    
        return response['output']['message']['content'][0]['text'].strip()
        
    except Exception as e:
        print(f"Bedrock Error: {e}")
        return f"This {car_row.get('model')} is an excellent choice for {priority}. (AI Pitch unavailable)."