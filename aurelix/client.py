import requests
from . import schema
from time import time
import typing

class RemoteException(Exception):
    pass

class ClientException(Exception):
    pass



class APIClient(object):

    def __init__(self, base_url: str, client_id: str | None = None, client_secret: str | None = None):
        if base_url.endswith('/'):
            self.base_url = base_url[:-1]
        else:
            self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expiry = None
        self._scope = None
        self.config: schema.WellKnownConfiguration = self.get_config()

    def url(self, path):
        if '://' in path:
            return path
        if path.startswith('/'):
            return self.base_url + path
        return self.base_url + '/' + path
    
    def authenticate(self, username: str, password: str, scope: list[str] = None):
        return self._authenticate(
            username=username,
            password=password,
            grant_type='password',
            scope=scope
        )
    
    def refresh_token(self, refresh_token=None, scope: list[str] = None):
        refresh_token = refresh_token or self._token.refresh_token 
        return self._authenticate(
            refresh_token=refresh_token,
            grant_type='refresh_token',
            scope=scope
        )
    
    def _authenticate(self, username: str = None, password: str = None, refresh_token: str = None, 
                     grant_type: str='password', scope: list[str]=None):
        scope = scope or self._scope or ['openid','email', 'profile', 'offline_access']
        self._scope = scope
        if not self.client_id:
            return None
        token_endpoint = self.openid_configuration.token_endpoint
        payload = {
            'grant_type': grant_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret, 
            'scope': ' '.join(scope)
        }
        if username and password:
            payload.update({
                'username': username,
                'password': password
            })
        if refresh_token:
            payload['refresh_token'] = refresh_token
        resp = requests.post(token_endpoint, data=payload)
        if resp.status_code != 200:
            raise RemoteException("Unable to authenticate (Error %s : %s)" % (resp.status_code, resp.text))
        token = schema.OIDCTokenResponse.model_validate(resp.json())
        self._token = token
        self._token_expiry = time() + token.expires_in
        return token
    
    @property
    def token(self):
        if self._token is None:
            return None
        if time() < self._token_expiry:
            token = self.refresh_token()
            self._token = token
        return self._token
    
    def request(self, method, path, *args, **kwargs):
        url = self.url(path)
        if self._token:
            kwargs.setdefault('headers', {})
            kwargs['headers']['Authorization'] = self._token.token_type + ' ' + self._token.access_token
        resp: requests.Response = getattr(requests, method.lower())(url, *args, **kwargs)
        if resp.status_code != 200:
            try:
                data = resp.json()
            except requests.exceptions.JSONDecodeError:
                data = None
            if data:
                raise RemoteException('Error %s: %s' % (resp.status_code, data['detail']))
            raise RemoteException('Error %s' % resp.status_code)
        data = resp.json()
        return data
    
    def get(self, path, *args, **kwargs):
        return self.request(method='get', path=path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        return self.request(method='post', path=path, *args, **kwargs)

    def delete(self, path, *args, **kwargs):
        return self.request(method='delete', path=path, *args, **kwargs)

    def put(self, path, *args, **kwargs):
        return self.request(method='put', path=path, *args, **kwargs)
    
    def patch(self, path, *args, **kwargs):
        return self.request(method='patch', path=path, *args, **kwargs)
        
    def get_config(self) -> schema.WellKnownConfiguration:
        data = self.get('/.well-known/aurelix-configuration')
        return schema.WellKnownConfiguration.model_validate(data)
    
    @property
    def collections(self):
        return self.config.collections

    @property
    def openid_configuration(self):
        return self.config.openid_configuration
    
class Model(object):
    
    def __init__(self, api: APIClient, collection: 'Collection', data):
        self.api = api
        self.data = data
        self.collection = collection

    def url(self, path:str = None):
        if path:
            if path.startswith('/'):
                return self.data['links']['self'] + path
            return self.data['links']['self'] + '/' + path
        return self.data['links']['self']

    def __getitem__(self, key: str) -> typing.Any: 
        return self.data['attributes'][key]
    
    def update(self, data: dict):
        attrs = self.data['attributes']
        attrs.update(data)
        self.put(json=attrs)
        self.data = self.get()['data']
        return True

    def triggers(self):
        sm = self.collection.config.stateMachine
        current_state = self[sm.field]
        result = []
        if not sm:
            return []
        for trigger in sm.triggers:
            if type(trigger.source) == str:
                source = [trigger.source]
            else:
                source = trigger.source
            if current_state in source:
                result.append(trigger.name)
        return result
        
    def transition(self, trigger, data: dict = None):
        triggers = self.triggers()
        if trigger not in triggers:
            message = "Unable to trigger '%s' from state '%s'." % (trigger, self.state)
            if triggers:
                message += ' Valid triggers are: %s.' % ', '.join(['%s' % t for t in triggers])
            raise ClientException(message)
        payload = {
            'trigger': trigger
        }
        if data:
            payload['data'] = data
        self.post('/+transition', json=payload)
        self.data = self.get()['data']
        return True
    
    @property
    def state(self):
        sm = self.collection.config.stateMachine
        if sm:
            return self[sm.field]
        return None
    
    def __repr__(self) -> str:
        name = self['id']
        if 'name' in self.data['attributes']:
            name = self['name']
        return "<Model at '/%s/%s'>" % (self.collection.config.name, name)

    def get(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.get(path, *args, **kwargs)

    def post(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.post(path, *args, **kwargs)

    def delete(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.delete(path, *args, **kwargs)

    def put(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.put(path, *args, **kwargs)

    def patch(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.patch(path, *args, **kwargs)

class SearchResult(object):
    def __init__(self, api: APIClient, collection: 'Collection', result) -> None:
        self.api = api
        self.collection = collection
        self.result = result

    def __iter__(self) -> typing.Iterator[Model]:
        for d in self.result['data']:
            yield Model(self.api, self.collection, d)
        next = self.next()
        if next:
            for o in next:
                yield o

    def next(self) -> 'SearchResult':
        next_url = self.result['links'].get('next', None)
        if next_url:
            result = self.api.get(next_url)
            return SearchResult(self.api, self.collection, result)
        return None
    
    def previous(self) -> 'SearchResult':
        prev_url = self.result['links'].get('prev', None)
        if prev_url:
            result = self.api.get(prev_url)
            return SearchResult(self.api, self.collection, result)
        return None
    
    @property
    def total_pages(self) -> int:
        return self.result['meta']['total_pages']
    
    @property
    def total_records(self) -> int:
        return self.result['meta']['total_pages']

class Collection(object):

    def __init__(self, api: APIClient, config: schema.WellKnownCollection) -> None:
        self.api = api
        self.config = config

    def url(self, path: str | int =None):
        if path:
            path = str(path)
            if path.startswith('/'):
                return self.config.links['self'] + path
            return self.config.links['self'] + '/' + path
        return self.config.links['self']

    def __getitem__(self, key) -> Model: 
        return self.get_item(key)
    
    def __iter__(self) -> typing.Iterator[Model]:
        return self.search(page_size=100).__iter__()
    
    def get_item(self, name: str | int) -> Model:
        data = self.get(name)
        return Model(self.api, self, data['data'])
    
    def create(self, data: dict) -> Model:
        result = self.post(json=data)
        return Model(self.api, self, result['data'])
    
    def search(self, query:str=None, page: int =0, page_size: int=10):
        payload = {
            'page': page,
            'page_size':page_size
        }
        if query:
            payload['query'] = query
        result = self.get(params=payload)
        return SearchResult(self.api, self, result)
    
    def __repr__(self) -> str:
        return "<Collection at '/%s'>" % self.config.name

    def total(self):
        return self.search(page_size=0).total_records
    
    def get(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.get(path, *args, **kwargs)

    def post(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.post(path, *args, **kwargs)


    def delete(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.delete(path, *args, **kwargs)
    
    def delete_item(self):
        return self.delete(json={'delete': True})


    def put(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.put(path, *args, **kwargs)

    
    def patch(self, path='/', *args, **kwargs):
        path = self.url(path)
        return self.api.patch(path, *args, **kwargs)



class Client(object):

    def __init__(self, base_url: str, client_id: str|None = None, client_secret: str|None = None) -> None:
        self.api: APIClient = APIClient(base_url, client_id, client_secret)

    def authenticate(self, username: str, password: str):
        self.api.authenticate(username, password)

    def __getitem__(self, key) -> Collection:
        return self.get_collection(key)
    
    def get_collection(self, name) -> Collection:
        c = self.api.collections[name]
        return Collection(self.api, c)
    
    def collections(self) -> dict[str, Collection]:
        result = {}
        for k, c in self.api.collections.items():
            result[k] = Collection(self.api, c)
        return result

