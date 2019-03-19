from mnemonic import Mnemonic
import os
import hmac
import hashlib
import math
import time
from coincurve import PrivateKey
from ethereum.utils import privtoaddr, decode_hex, encode_hex, ecsign, zpad, bytearray_to_bytestr, int_to_32bytearray, sha3 as keccak256
from base64 import b64encode

def derive(seed, path):
    # TODO: fix me
    path_elements = path.split('/')
    digest = hmac.new(b'Bitcoin seed', msg=seed, digestmod=hashlib.sha512).digest()
    private_key = PrivateKey(digest[:32])
    chaincode = digest[32:]

    for path_element in path_elements:
        if path_element == 'm':
            continue
        hm = hmac.new(chaincode, digestmod=hashlib.sha512)
        hardened = path_element.endswith("'") or path_element.endswith("h")
        if hardened:
            n = int(path_element[:-1])
            hm.update(b'\x00')
            hm.update(private_key.secret)
            hm.update((n + (1 << 31)).to_bytes(4, 'big'))
        else:
            n = int(path_element)
            hm.update(private_key.public_key.format(compressed=True))
            hm.update(n.to_bytes(4, 'big'))
        digest = hm.digest()
        priv = PrivateKey(digest[:32])
        priv = priv.add(private_key.secret)
        private_key = priv
        chaincode = digest[32:]
    return private_key.secret

class Wallet:
    def __init__(self, twelve_words=None, key=None):
        if twelve_words is None and key is None:
            twelve_words = Mnemonic('english').generate()
        if twelve_words is not None:
            self.twelve_words = twelve_words
            self.seed = Mnemonic.to_seed(self.twelve_words)

            # derive paths
            key = derive(self.seed, "m/44'/60'/0'/0/0")
            self.key = key
        elif key is not None:
            if isinstance(key, str):
                key = decode_hex(key)
            self.key = key

    @staticmethod
    def load():
        if not os.path.exists(".twelvewords"):
            return None
        with open(".twelvewords") as f:
            return Wallet(f.read())

    def save(self):
        with open(".twelvewords", 'w') as f:
            f.write(self.twelve_words)

    def sign(self, rawhash):
        v, r, s = ecsign(rawhash, self.key)
        signature = \
            zpad(bytearray_to_bytestr(int_to_32bytearray(r)), 32) + \
            zpad(bytearray_to_bytestr(int_to_32bytearray(s)), 32) + \
            bytearray_to_bytestr([v - 27])

        return signature

    @property
    def address(self):
        return '0x' + encode_hex(privtoaddr(self.key))

    @property
    def auth(self):
        code = str(math.floor(time.time() / 30))
        signature = self.sign(keccak256(code))
        combined = privtoaddr(self.key) + signature
        return 'Basic ' + b64encode(combined).decode()
