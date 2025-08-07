import json
from django.http import JsonResponse
from django.core.exceptions import ValidationError as DjangoValidationError


class APIResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip processing for redirect responses (300–399)
        if 300 <= response.status_code < 400:
            return response

        # Handle permission errors (403)
        if response.status_code == 403:
            try:
                content = json.loads(response.content) if response.content else {}
                detail = content.get('detail', response.reason_phrase)
            except json.JSONDecodeError:
                detail = response.reason_phrase
            return JsonResponse({
                "response_status": "error",
                "response_description": f"Forbidden: {detail}",
                "response_data": {"detail": detail}
            }, status=403)

        # Handle validation errors (400)
        if response.status_code == 400:
            try:
                content = json.loads(response.content) if response.content else {}
                detail = content.get('detail', content)
            except json.JSONDecodeError:
                detail = response.reason_phrase
            return JsonResponse({
                "response_status": "error",
                "response_description": "Validation error occurred.",
                "response_data": detail
            }, status=400)

        # Check if the response is already a JsonResponse
        if isinstance(response, JsonResponse):
            content = json.loads(response.content)
            # Add standard fields if not already present
            if "response_status" not in content:
                standardized_response = {
                    "response_status": "success" if response.status_code <= 399 else "error",
                    "response_description": content.get("message", "Request processed"),
                    "response_data": content.get("data", content)
                }
                return JsonResponse(standardized_response, status=response.status_code)

        # Handle other error responses
        if response.status_code > 399:
            return JsonResponse({
                "response_status": "error",
                "response_description": response.reason_phrase,
                "response_data": {}
            }, status=response.status_code)

        return response
