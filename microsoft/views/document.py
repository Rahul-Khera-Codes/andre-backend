from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class SummarizeEmailView(APIView):
    def post(self, request):
        try:
            jwt_auth_header = request.headers.get("Authorization")
            if jwt_auth_header and jwt_auth_header.startswith("Bearer "):
                jwt_access_token = jwt_auth_header.split(" ")[1]
            else:
                jwt_access_token = None
            if not jwt_access_token:
                return Response({"error": "Not Token"}, status=status.HTTP_401_UNAUTHORIZED)
            
            account = verify_access_token(jwt_access_token)
            if not account:
                return Response({"error": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)
            
            message_id = request.data.get("message_id")
            email_message = EmailMessages(microsoft=account, message_id=message_id)
            # 
            
            
                
        except ExpiredTokenError as e:
            return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except InvalidToken as e:
            return Response({"error": "Invalid Token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except TokenError as e:
            return Response({"error": "Token Error"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            return Response({"error": "Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        