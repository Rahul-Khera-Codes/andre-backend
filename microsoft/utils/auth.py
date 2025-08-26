from rest_framework_simplejwt.tokens import (
    AccessToken,
    RefreshToken
)

from ..models import (
    MicrosoftConnectedAccounts,
    UserToken
)


def get_tokens_for_user(user: MicrosoftConnectedAccounts):
    refresh = RefreshToken.for_user(user)
    refresh['id'] = user.id
    refresh['microsoft_id'] = user.microsoft_id
    refresh['display_name'] = user.display_name

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        "id": user.id,
        "microsoft_id": user.microsoft_id,
        "display_name": user.display_name
    }
    

def verify_access_token(token_str):
    # Decode and verify token
    
    if not UserToken.objects.filter(access_token=token_str).exists():
        return None
    
    access_token = AccessToken(token_str)
    microsoft_id = access_token['microsoft_id']  # default claim
    user = MicrosoftConnectedAccounts.objects.get(microsoft_id=microsoft_id)
    return user
    
    