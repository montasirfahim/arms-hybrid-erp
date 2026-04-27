import os
import json
import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from accounts.decorators import login_required

# Initialize Logger
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def ai_chat_view(request):
    """
    Django view that proxies the request to the FastAPI AI microservice.
    """
    try:
        # 1. Get the payload from the frontend
        data = json.loads(request.body)
        
        # 2. Define the AI Service URL (Local vs Render)
        ai_service_url = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
        
        # Ensure the URL has a protocol
        if not ai_service_url.startswith("http"):
            # On Render, if we only get the host, we add http and the internal port 10000
            ai_service_url = f"http://{ai_service_url}:10000"
        
        logger.info(f"Proxying request to AI Service: {ai_service_url}/chat")

        # 3. Forward the request to FastAPI
        response = requests.post(
            f"{ai_service_url}/chat",
            json=data,
            timeout=30
        )
        
        # 4. Return the FastAPI response back to the frontend
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            logger.error(f"AI Service Error: {response.status_code} - {response.text}")
            return JsonResponse({
                "role": "assistant",
                "content": "I'm having trouble connecting to my brain (AI Service). Please try again later."
            }, status=response.status_code)

    except requests.exceptions.RequestException as re:
        logger.error(f"Connection to AI Service failed: {str(re)}")
        return JsonResponse({
            "role": "assistant",
            "content": "Connection to the AI microservice failed. Is the service running?"
        }, status=503)
    except Exception as e:
        logger.error(f"AI Proxy View Error: {str(e)}", exc_info=True)
        return JsonResponse({"error": "An internal error occurred in the proxy view."}, status=500)
