from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from . import state
from . import schema
from .settings import Settings
import fastapi
import typing
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from . import exc
import jwt
import httpx
import traceback
import yaml

def get_oidc_configuration(request: fastapi.Request):
    app = request.app
    oidc_settings = state.APP_STATE[app].get('oidc_settings', None)
    return oidc_settings

OIDCConfiguration = typing.Annotated[schema.OIDCConfiguration, fastapi.Depends(get_oidc_configuration)]

async def _get_token(request: fastapi.Request, oidc_settings: OIDCConfiguration) -> schema.OIDCAccessToken:
    if not oidc_settings:
        return None

    decoded = getattr(request.state, 'decoded_token', None)
    if decoded:
        return decoded
    
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise exc.Unauthorized("Not authenticated")

    jwk_client = state.APP_STATE[request.app]['oidc_jwk_client']
    try: 
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        # FIXME: should we really ignore audience claim
        decoded = jwt.decode(token, key=signing_key.key, algorithms=oidc_settings.id_token_signing_alg_values_supported, options={'verify_aud': False})
        
    except jwt.InvalidTokenError as e:
        raise exc.Unauthorized("Not authenticated")
    except jwt.InvalidKeyError as e:
        traceback.print_exc()
        raise exc.Unauthorized("Not authenticated")

    token = schema.OIDCAccessToken.model_validate(decoded)
    if not token.sub:
        raise exc.Unauthorized("No sub provided in token")
    if not token.email and token.email_verified:
        raise exc.Unauthorized("No valid email address")
    request.state.decoded_token = token
    return token

class OAuth2Mixin(object):

    async def __call__(self, request: fastapi.Request, oidc_settings: OIDCConfiguration) -> schema.OIDCAccessToken:
        return await _get_token(request, oidc_settings)
    
class PasswordBearerScheme(OAuth2Mixin, OAuth2PasswordBearer):
    pass

env_settings = Settings()

Token = typing.Annotated[str, fastapi.Depends(_get_token)]

if env_settings.CONFIG:
    with open(env_settings.CONFIG) as f:
        _config = yaml.safe_load(f)

    _oidc_discovery_endpoint = _config.get('oidc_discovery_endpoint', None)
    if _oidc_discovery_endpoint:
        with httpx.Client() as client:
            resp = client.get(_oidc_discovery_endpoint)
            if resp.status_code != 200:
                raise exc.AurelixException("Unable to query OIDC discovery endpoint")
            _oidc_settings = schema.OIDCConfiguration.model_validate(resp.json())
    
        _oidc_scheme = _config.get('oidc_scheme', 'password')
    
        if _oidc_scheme == 'password':
            Token = typing.Annotated[str, 
                fastapi.Depends(
                    PasswordBearerScheme(
                        tokenUrl=_oidc_settings.token_endpoint, 
                        scopes=dict((k,k) for k in _oidc_settings.scopes_supported)
                    )
                )
            ]
        else:
            raise exc.AurelixException("Unsupported OIDC scheme %s" % _oidc_scheme)
    
async def get_token(request: fastapi.Request) -> schema.OIDCAccessToken:
    oidc_settings = get_oidc_configuration(request)
    token = await _get_token(request, oidc_settings)
    return token

async def get_permission_identities(request: fastapi.Request) -> list[str]:
    token = await get_token(request)
    if token is None:
        return []
    res = []
    res.append('sub:%s' % token.sub)
    if token.email and token.email_verified:
        res.append('email:%s' % token.email)
    if token.roles:
        for g in token.roles:
            res.append('role:%s' % g)
    return res
