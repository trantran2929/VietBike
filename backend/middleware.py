import requests
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
import logging
from django.http import HttpResponseBadRequest, FileResponse

logger = logging.getLogger(__name__)

class AutoRefreshTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')

        if access_token and refresh_token:
            try:
                JWTAuthentication().get_validated_token(access_token)
            except InvalidToken:
                try:
                    response = requests.post(
                        f'{settings.BACKEND_API_URL}/auth/token/refresh/',
                        data={'refresh': refresh_token}
                    )
                    if response.status_code == 200:
                        new_tokens = response.json()
                        request.session['access_token'] = new_tokens['access']
                        if 'refresh' in new_tokens:
                            request.session['refresh_token'] = new_tokens['refresh']
                    else:
                        request.session.flush()
                except requests.RequestException:
                    request.session.flush()

        response = self.get_response(request)
        return response

class LogFailedLogin:
    def __call__(self, request):
        response = self.get_response(request)
        if request.path == '/api/auth/token/' and response.status_code == 401:
            logger.warning(f"Failed login for {request.POST.get('email')}")
        return response
    

class LogRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Decode request.body sang string UTF-8
        try:
            request_body = request.body.decode('utf-8')
        except UnicodeDecodeError:
            request_body = "<Non-UTF-8 body>"
        logger.debug(f"Request: {request.method} {request.path} Body: {request_body}")
        
        try:
            response = self.get_response(request)
            # Xử lý response chỉ khi không phải FileResponse
            if isinstance(response, FileResponse):
                logger.debug(f"Response: {response.status_code} <FileResponse: {request.path}>")
            else:
                try:
                    response_content = response.content.decode('utf-8')[:100]
                except UnicodeDecodeError:
                    response_content = "<Non-UTF-8 content>"
                logger.debug(f"Response: {response.status_code} {response_content}")
            return response
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            return HttpResponseBadRequest("Invalid request")