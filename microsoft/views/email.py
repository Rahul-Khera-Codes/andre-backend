from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError,
    InvalidToken,
    TokenError
)

from ..models import (
    EmailMessages
)
from ..serializers import (
    EmailMessageSerializer
)
from ..utils.auth import (
    get_tokens_for_user,
    verify_access_token
)

def snake_to_camel(q: str):
    ql = q.split("_")
    nql = []
    for s in ql:
        nql.append(s[0].upper() + s[1:])
        
    return " ".join(nql)

class GetUserMail(APIView):
    def get(self, request):
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
            
            mail_filter = request.query_params.get('filter')
            mail_filter = snake_to_camel(mail_filter)
            if mail_filter == "All" or mail_filter == 'all':
                mail_filter = None
            
            
            
            if mail_filter:
                emails = EmailMessages.objects.filter(Q(microsoft=account) & Q(folder_name=mail_filter))
            else:
                emails = EmailMessages.objects.filter(microsoft=account)
            email_serializer = EmailMessageSerializer(emails, many=True)
            
        except ExpiredTokenError as e:
            return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except InvalidToken as e:
            return Response({"error": "Invalid Token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except TokenError as e:
            return Response({"error": "Token Error"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            print("error:", e)
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
        # messages = response.json().get("value", [])
        # print("messages:", messages)
        return Response(email_serializer.data, status=status.HTTP_200_OK)
    
    
class GetMailFolder(APIView):
    def get(self, request):
        
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
            
            folder_name = EmailMessages.objects.values_list("folder_name", flat=True).distinct()
            
        except ExpiredTokenError as e:
            return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except InvalidToken as e:
            return Response({"error": "Invalid Token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except TokenError as e:
            return Response({"error": "Token Error"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            print("error:", e)
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
        # messages = response.json().get("value", [])
        # print("messages:", messages)
        return Response(folder_name, status=status.HTTP_200_OK)