import httpx

from ghostricon import constants
from ghostricon.config import get_cg_config


class CyberghostAPI:
    oauth = None

    @classmethod
    async def craft_oauth(cls):
        if cls.oauth:
            return cls.oauth
        config = get_cg_config()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f'OAuth oauth_consumer_key="{config.get("device", "token")}",oauth_signature_method="PLAINTEXT",oauth_version="1.0",oauth_signature="{config.get("device", "secret")}%26"',
        }
        payload = {
            "x_auth_machine_id": config.get("device", "name"),
            "x_auth_mode": "client_auth",
            "x_auth_account": config.get("account", "username"),
            "x_auth_password": config.get("account", "password"),
        }
        client: httpx.AsyncClient
        async with httpx.AsyncClient(headers=headers) as client:
            res = await client.post(constants.CG_BASE_URL + "oauth/access_token",
                                    json=payload)
            res = res.json()
        cls.oauth = f'OAuth oauth_consumer_key="{config.get("device", "token")}",oauth_token="{res.get("oauth_token")}",oauth_signature_method="PLAINTEXT",oauth_version="1.0",oauth_signature="{config.get("device", "secret")}%26{res.get("oauth_token_secret")}"',
        return cls.oauth

    @classmethod
    async def get_servers(cls):
        config = get_cg_config()
        headers = {
            "Content-Type": "application/json",
            "Authorization": await cls.craft_oauth(),
        }
        client: httpx.AsyncClient
        async with httpx.AsyncClient(headers=headers) as client:
            ret = await client.get(constants.CG_BASE_URL + "servers")
            return ret.json()
