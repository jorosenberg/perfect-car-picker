---
title: Perfect Car Picker Backend
emoji: 🚗
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# perfect-car-picker backend (Hugging Face Space)

FastAPI shim around the original AWS Lambda handler (`lambda_function.lambda_handler`).
`POST /calculate` accepts the exact same JSON payloads as the old API Gateway route.

Environment variables to set in the Space (Settings → Variables and secrets):

| Var | Value |
|---|---|
| `DB_HOST` | Neon host (`ep-....neon.tech`) |
| `DB_PORT` | `5432` |
| `DB_NAME` | `cardb` |
| `DB_USER` | Neon role |
| `DB_PASS` | Neon password (secret) |
| `DB_SSLMODE` | `require` |
| `GEMINI_API_KEY` | Google AI Studio key (secret) |
