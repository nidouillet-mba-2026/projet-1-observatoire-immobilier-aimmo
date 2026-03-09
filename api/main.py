from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI(title='AImmo API')

# CORS configuration for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
ollama_model = os.getenv('OLLAMA_MODEL', 'llama3')

@app.get('/')
async def root():
    """Root endpoint"""
    return {'message': 'AImmo API - Real Estate Analysis Engine', 'version': '1.0'}

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {'status': 'ok', 'api': 'running'}

@app.post('/chat')
async def chat(message: dict):
    """Chat endpoint connected to Ollama for conversational assistance"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{ollama_host}/api/generate',
                json={
                    'model': ollama_model,
                    'prompt': message.get('text', ''),
                    'stream': False
                },
                timeout=30.0
            )
        return response.json()
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

@app.post('/report')
async def generate_report(data: dict):
    """Endpoint for generating PDF reports"""
    try:
        # Placeholder for PDF generation logic
        return {
            'status': 'success',
            'message': 'Report generation initiated',
            'report_id': data.get('property_id', 'N/A')
        }
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

@app.get('/models')
async def available_models():
    """Get available Ollama models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{ollama_host}/api/tags')
        return response.json()
    except Exception as e:
        return {'error': str(e), 'status': 'error'}
