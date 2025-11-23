import requests
from django.http import JsonResponse
from django.conf import settings


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bỏ qua trang admin
        if request.path.startswith('/admin'):
            return self.get_response(request)

        # Lấy token từ Header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({"error": "Unauthorized - missing token"}, status=401)

        token = auth_header.replace("Bearer ", "")

        # Gửi token sang Auth Service (TH2) để xác thực
        try:
            response = requests.post(
                settings.AUTH_VERIFY_URL,
                json={"token": token},
                timeout=5
            )

            if response.status_code != 200:
                return JsonResponse({"error": "Unauthorized - invalid token"}, status=401)

        except requests.exceptions.RequestException:
            return JsonResponse({"error": "Auth Service unavailable"}, status=503)

        return self.get_response(request)

