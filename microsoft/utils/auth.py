import base64
from datetime import datetime, timedelta, timezone
import json
import uuid

from rest_framework_simplejwt.tokens import (
    AccessToken,
    RefreshToken
)

from ..models import (
    MicrosoftConnectedAccounts,
    UserToken
)

async def get_vector_store_name(account: MicrosoftConnectedAccounts) -> str:
    return f"{account.given_name}-{account.surname}-{str(uuid.uuid4())[:8]}"


def get_callback_session_id(mid: str):
    future5 = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    future5_data = {
        'expire_at': future5,
        'mid': mid
    }
    future5_json = json.dumps(future5_data)
    future5_bytes = future5_json.encode('utf-8')
    future5_base64 = base64.b64encode(future5_bytes)
    return future5_base64.decode('utf-8')


def get_tokens_for_user(user: MicrosoftConnectedAccounts) -> dict[str, str]:
    """
    This function return the data user token for access the website.
    :param user: MicrosoftConnectedAccount instance
    """
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
    """
    Decode and verify token. Return the `MicrosoftConnectAccounts` object.
    
    :param token_str: access token of user.
    """
    
    if not UserToken.objects.filter(access_token=token_str).exists():
        return None
    
    access_token = AccessToken(token_str)
    microsoft_id = access_token['microsoft_id']  # default claim
    user = MicrosoftConnectedAccounts.objects.get(microsoft_id=microsoft_id)
    return user
    
    