import json
import boto3

def get_car_pitch(car_row, priority):
    """
    Uses AWS Bedrock to generate a sales pitch.
    """

    prompt = f"""
    Act as a car sales expert. Write a persuasive 2-3 sentence pitch for a {car_row.get('year')} {car_row.get('make')} {car_row.get('model')}.
    The buyer's top priority is: {priority}.
    Key specs: {car_row.get('city_mpg')} MPG, {car_row.get('acceleration')}s 0-60, {car_row.get('cargo_space')} cu ft cargo.
    Explain why this car fits their priority.
    """
    
    client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    response = client.converse(
        modelId='global.amazon.nova-2-lite-v1:0', 
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        inferenceConfig={
            "maxTokens": 300,
            "temperature": 0.7
        },
        additionalModelRequestFields={
            "reasoningConfig": {
                "type": "enabled", 
                "maxReasoningEffort": "low" 
            }
        }
    )
    
    for block in response["output"]["message"]["content"]:
        if "reasoningContent" in block:
            reasoning_text = block["reasoningContent"]["reasoningText"]["text"]
            print(f"Nova's thinking process: {reasoning_text}")
        elif "text" in block:
            return block["text"].strip()
            
    return "Pitch generated but format unrecognized."