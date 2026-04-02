from fastapi import FastAPI

app = FastAPI(title="ARMS AI Service", version="1.0.0")

@app.get("/")
async def root():
    return {"status": "Online", "service": "ARMS AI Analytics Service"}

@app.get("/health")
async def health_check():
    return {"message": "AI Service is healthy and ready for Groq integration"}