import aiohttp
import asyncio
import weakref
from http.client import responses
from ethereum.utils import decode_hex, encode_hex

class HTTPError(Exception):
    def __init__(self, status, message=None):
        self.status = status
        self.message = message or responses.get(status, "Unknown")
        super().__init__(status, message)

    def __str__(self):
        return "HTTP %d: %s" % (self.status, self.message)

class DolaClient:

    @classmethod
    def _async_clients(cls):
        attr_name = '_async_client_dict_' + cls.__name__
        if not hasattr(cls, attr_name):
            setattr(cls, attr_name, weakref.WeakKeyDictionary())
        return getattr(cls, attr_name)

    def __new__(cls, *args, force_instance=False, **kwargs):
        loop = asyncio.get_event_loop()
        if force_instance:
            instance_cache = None
        else:
            instance_cache = cls._async_clients()
        if instance_cache is not None and loop in instance_cache:
            return instance_cache[loop]
        instance = super().__new__(cls)
        # Make sure the instance knows which cache to remove itself from.
        instance._loop = loop
        instance._instance_cache = instance_cache
        if instance_cache is not None:
            instance_cache[instance._loop] = instance
        instance.initialise(*args, **kwargs)
        return instance

    def initialise(self, base_url, wallet, *, max_clients=100, connect_timeout=None, verify_ssl=True):
        self.wallet = wallet
        self.base_url = base_url
        connector = aiohttp.TCPConnector(
            limit=max_clients)
        self._verify_ssl = verify_ssl
        self._session = aiohttp.ClientSession(connector=connector, conn_timeout=connect_timeout)

    async def fetch(self, url, *, method="GET", params=None, headers=None, body=None, request_timeout=None):
        if not (url.startswith('http://') or url.startswith('https://')):
            url = self.base_url + url
        fn = getattr(self._session, method.lower())
        kwargs = {}
        if isinstance(body, (dict, list)) and (headers is None or 'Content-Type' not in headers):
            kwargs['json'] = body
        else:
            kwargs['data'] = body
        if request_timeout:
            kwargs['timeout'] = request_timeout
        if params is not None:
            kwargs['params'] = params
        try:
            resp = await fn(url, headers=headers, ssl=self._verify_ssl, **kwargs)
            if resp.status < 200 or resp.status >= 300:
                print(await resp.json())
                raise HTTPError(resp.status, message=resp.reason)
            return resp
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            error = e
        # outside of the except block to avoid rethrow error message
        raise HTTPError(599, message=str(error))

    async def close(self):
        await self._session.close()
        if self._instance_cache is not None:
            del self._instance_cache[self._loop]

    async def get_user(self, address):
        try:
            resp = await self.fetch('/v1/user/{}'.format(address),
                                    method="GET", headers={'Authorization': self.wallet.auth})
            return await resp.json()
        except HTTPError:
            return None

    async def create_user(self, name):
        resp = await self.fetch('/v1/user', method="POST", headers={'Authorization': self.wallet.auth},
                                body={'name': name})
        return await resp.json()

    async def send_message(self, address, message):
        resp = await self.fetch('/v1/message', method="POST", headers={'Authorization': self.wallet.auth},
                                body={'to': address, 'message': message})
        return await resp.json()

    async def get_balance(self, address):
        resp = await self.fetch('/v1/balance/{}'.format(address), method="GET")
        return await resp.json()

    async def get_events(self, from_event=0):
        resp = await self.fetch('/v1/events', method="GET", params={'from': from_event}, headers={'Authorization': self.wallet.auth})
        return await resp.json()

    async def send_payment(self, address, value, message=None):
        resp = await self.fetch('/v1/payment', method="POST", headers={'Authorization': self.wallet.auth},
                                body={'to': address, 'value': value})
        data = await resp.json()
        signature = "0x" + encode_hex(self.wallet.sign(decode_hex(data['hash'])))
        data['signature'] = signature
        if message:
            data['message'] = message
        print(data)
        resp = await self.fetch('/v1/payment', method="POST", headers={'Authorization': self.wallet.auth},
                                body=data)
        return await resp.json()

    async def update_payment_message(self, payment_id, message):
        resp = await self.fetch(f'/v1/payment/{payment_id}', method="PUT", headers={'Authorization': self.wallet.auth},
                                body={'message': message})
        return await resp.json()

    async def approve(self):
        resp = await self.fetch('/v1/approval', method="GET", headers={'Authorization': self.wallet.auth})
        data = await resp.json()
        print(data)
        signature = "0x" + encode_hex(self.wallet.sign(decode_hex(data['tx'])))
        print(signature)
        data['signature'] = signature

        resp = await self.fetch('/v1/approval', method="POST",
                                headers={'Authorization': self.wallet.auth},
                                body=data)
        return await resp.json()

    async def ephemeral_key(self):
        resp = await self.fetch('/v1/stripe/ephemeral_keys', method="POST", headers={'Authorization': self.wallet.auth})
        data = await resp.json()
        return data

    async def purchase_info(self):
        resp = await self.fetch('/v1/purchase/info', method="GET", headers={'Authorization': self.wallet.auth})
        data = await resp.text()
        return data
