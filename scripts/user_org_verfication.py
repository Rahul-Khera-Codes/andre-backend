import json
import os

from dotenv import load_dotenv
import requests
from jose import jwt

load_dotenv(override=True)

TENANT_ID = os.getenv("TENANT_ID")
ID_TOKEN = os.getenv("ID_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me"
OPENID_CONFIG_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"
# print("TENANT_ID", TENANT_ID)
# print("ID_TOKEN", ID_TOKEN)
# print("ACCESS_TOKEN", ACCESS_TOKEN)
# print("CLIENT_ID", CLIENT_ID)
# print("GRAPH_API_URL", GRAPH_API_URL)
# print("OPENID_CONFIG_URL", OPENID_CONFIG_URL)

def get_user_tenant_info(id_token):
    # Decode JWT without verification (for inspection only)
    claims = jwt.get_unverified_claims(id_token)
    
    tenant_id = claims.get("tid")
    object_id = claims.get("oid")
    email = claims.get("preferred_username")

    return {
        "tenant_id": tenant_id,
        "object_id": object_id,
        "email": email
    }


def get_user_graph_info(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    resp = requests.get(GRAPH_API_URL, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # Key fields
    return {
        "id": data.get("id"),
        "userPrincipalName": data.get("userPrincipalName"),
        "userType": data.get("userType"),  # "Member" or "Guest"
        "displayName": data.get("displayName")
    }


def check_user_association(id_token, access_token):
    token_info = get_user_tenant_info(id_token)
    graph_info = get_user_graph_info(access_token)

    if token_info["tenant_id"] == TENANT_ID:
        if graph_info["userType"] == "Member":
            return "Internal Member"
        elif graph_info["userType"] == "Guest":
            return "Guest User (invited)"
    else:
        return "External (different tenant)"


# def verify_microsoft_token(id_token):
#     # Fetch OpenID config
    
#     openid_config = requests.get(OPENID_CONFIG_URL).json()
#     print("\nopenid_config", openid_config, "\n")

#     # Get JWKS URI
#     jwks_uri = openid_config["jwks_uri"]
#     jwks = requests.get(jwks_uri).json()
    
#     print("\jwks", jwks, "\n")

#     # Verify token
#     claims = jwt.decode(
#         id_token,
#         jwks,
#         algorithms=["RS256"],
#         audience=CLIENT_ID,
#         issuer=f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
#     )

#     return claims



def verify_microsoft_token(id_token):
    # Decode without verifying first
    headers = jwt.get_unverified_header(ID_TOKEN)
    claims = jwt.get_unverified_claims(ID_TOKEN)
    print("Header:", headers)
    print("Claims:", claims)
    
    
    issuer = claims["iss"]  # example: https://login.microsoftonline.com/2222-bbbb/v2.0
    openid_config_url = f"{issuer}/.well-known/openid-configuration"

    openid_config = requests.get(openid_config_url).json()
    jwks_uri = openid_config["jwks_uri"]
    jwks = requests.get(jwks_uri).json()

    # Find correct key
    kid = headers["kid"]
    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if not key:
        raise ValueError("No matching key in JWKS")

    # Verify token
    claims = jwt.decode(
        id_token,
        key,
        algorithms=["RS256"],
        audience=CLIENT_ID,
        issuer=issuer
    )

    return claims


def check_user(id_token, access_token):
    claims = verify_microsoft_token(id_token)

    tenant_id = claims["tid"]

    if tenant_id == TENANT_ID:
        return "Internal Member"
    else:
        # fallback check with Graph API
        info = get_user_graph_info(access_token)
        if info["userType"] == "Guest":
            return "Guest User (invited)"
        else:
            return "External (different tenant)"


if __name__ == "__main__":
    print(check_user(ID_TOKEN, ACCESS_TOKEN))