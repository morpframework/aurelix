from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from . import state
from . import schema
from .settings import Settings
import fastapi
import typing
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from . import exc
import httpx

def get_oidc_configuration(request: fastapi.Request):
    app = request.app
    oidc_settings = state.APP_STATE[app].get('oidc_settings', None)
    return oidc_settings

OIDCConfiguration = typing.Annotated[schema.OIDCConfiguration, fastapi.Depends(get_oidc_configuration)]

async def get_token(request: fastapi.Request):
    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise fastapi.HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
        )
    return param

class OAuth2Mixin(object):

    async def __call__(self, request: fastapi.Request) -> str:
        return await get_token(request)
    
class PasswordBearerScheme(OAuth2Mixin, OAuth2PasswordBearer):
    pass

env_settings = Settings()

Token = typing.Annotated[str, fastapi.Depends(get_token)]

if env_settings.OIDC_DISCOVERY_ENDPOINT:
    with httpx.Client() as client:
        resp = client.get(env_settings.OIDC_DISCOVERY_ENDPOINT)
        if resp.status_code != 200:
            raise exc.AurelixException("Unable to query OIDC discovery endpoint")
        _oidc_settings = schema.OIDCConfiguration.model_validate(resp.json())

    if env_settings.OIDC_SCHEME == 'password':
        Token = typing.Annotated[str, 
            fastapi.Depends(
                PasswordBearerScheme(
                    tokenUrl=_oidc_settings.token_endpoint, 
                    scopes=dict((k,k) for k in _oidc_settings.scopes_supported)
                )
            )
        ]
    
async def get_userinfo(token: Token, oidc_settings: OIDCConfiguration) -> schema.OIDCUserInfo:
    if token is None:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(oidc_settings.userinfo_endpoint, headers={'Authorization': 'Bearer %s' % token})
        if resp.status_code != 200:
            if resp.status_code == 401:
                raise exc.Unauthorized("Invalid token")
            raise exc.GatewayError('Unable to query OIDC userinfo endpoint (Error %s)' % (resp.status_code))
        userinfo = resp.json()
        if ('email' not in userinfo):
            raise exc.GatewayError("OIDC userinfo endpoint did not provide 'email' property")
        
        # groups and roles are not especified in oidc standard, so different provider uses different practice
        if 'groups' not in userinfo:
            if 'roles' in userinfo:
                userinfo['groups'] = userinfo['roles']
        return schema.OIDCUserInfo.model_validate(userinfo)

UserInfo = typing.Annotated[schema.OIDCUserInfo, fastapi.Depends(get_userinfo)]

async def get_userinfo_from_request(request: fastapi.Request) -> schema.OIDCUserInfo:
    oidc_settings = get_oidc_configuration(request)
    token = await get_token(request)
    userinfo = await get_userinfo(token, oidc_settings)
    return userinfo
