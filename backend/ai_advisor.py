import boto3

def get_car_pitch(car_row, priority):
    """
    Uses AWS Bedrock to generate a sales pitch.
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
                "maxTokens": 1000, 
                "temperature": 0.7
            },
            additionalModelRequestFields={
                "reasoningConfig": {
                    "type": "enabled", 
                    "maxReasoningEffort": "low" 
                }
            }
        )
        
        final_text = ""
        
        for block in response["output"]["message"]["content"]:
            if "reasoningContent" in block:
                print("Nova is reasoning... (Logging hidden from user)")
            if "text" in block:
                final_text += block["text"] + " "
                
        if final_text.strip():
            return final_text.strip()
            
        return "Pitch generated but format unrecognized."
        
    except Exception as e:
        print(f"Bedrock API Error: {e}")
        return f"This {car_row.get('model')} is a fantastic choice for {priority}."