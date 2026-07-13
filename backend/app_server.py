"""
HTTP shim - replaces AWS API Gateway + Lambda runtime with FastAPI.
The original lambda_handler is called unchanged; this file only converts
HTTP <-> Lambda event format, exactly like API Gateway's AWS_PROXY integration.

Run:  uvicorn app_server:app --host 0.0.0.0 --port 7860
"""
import json

from fastapi import FastAPI, Request, Response
from lambda_function import lambda_handler

app = FastAPI(title="perfect-car-picker backend")


@app.get("/")
def health():
    return {"status": "ok", "service": "perfect-car-picker backend"}


@app.post("/calculate")
async def calculate(request: Request):
    # Same shape API Gateway (payload v2, AWS_PROXY) handed to the Lambda.
    event = {"body": (await request.body()).decode("utf-8") or "{}"}
    result = lambda_handler(event, None)

    return Response(
        content=result.get("body", "{}"),
        status_code=result.get("statusCode", 200),
        media_type="application/json",
        headers={
            k: v
            for k, v in result.get("headers", {}).items()
            if k.lower() != "content-type"
        },
    )
