from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError,
    InvalidToken,
    TokenError
)
from rest_framework_simplejwt.tokens import RefreshToken


class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token
            return Response({'access_token': new_access_token}, status=status.HTTP_201_CREATED)            
            
        except ExpiredTokenError as e:
            return Response({"error": "Token expired, please login again"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except InvalidToken as e:
            return Response({"error": "Invalid expired, please login again"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except TokenError as e:
            return Response({"error": "Token error, please login again"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            return Response({"error": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

