import asyncio

import aiohttp
from asgiref.sync import sync_to_async
from . import get_refresh_token
from ..exceptions import MSInvalidTokenError
from ..models import MicrosoftConnectedAccounts

async def get_onedrive_content(
    access_token: str,
    /, *,
    folder_id: str | None = None,
    retries = 3,
    account: MicrosoftConnectedAccounts | None = None
):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    if folder_id:
        # url = "https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"
        url = "https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children".format(folder_id=folder_id)
    else:
        url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
        
    async with aiohttp.ClientSession() as session:
        attempts = 0
        async with session.get(url=url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return await response.json()
                # asyncio.sleep(0.3)
                # rt_status, rt_resposne = get_refresh_token(account.refresh_token)
                # if rt_status == 200:
                    
                    
    