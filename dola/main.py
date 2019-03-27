import sys
import names
from dola.client import DolaClient
from dola.wallet import Wallet
from dola.utils import validate_address

# BASE_URL = 'https://dola.one'
BASE_URL = 'https://dola.testwerk.org'

def help():
    print("")

async def main():
    if len(sys.argv) < 2:
        help()
        sys.exit(1)
    if sys.argv[1] == 'create':
        name = ' '.join(sys.argv[2:]).strip()
        if name == '':
            name = names.get_full_name()
        wallet = Wallet()
        wallet.save()
        client = DolaClient(BASE_URL, wallet)
        resp = await client.create_user(name)
        print(resp)
        await client.close()
    if sys.argv[1] == 'import':
        print("Enter 12 word phrase: ", end='')
        phrase = input()
        wallet = Wallet(twelve_words=phrase)
        wallet.save()
        client = DolaClient(BASE_URL, wallet)
        user = await client.get_user(wallet.address)
        if user is None:
            print("Creating user")
            print("Enter name: ", end='')
            name = input()
            if name == '':
                name = names.get_full_name()
            resp = await client.create_user(name)
            print(resp)
        else:
            print(user)
        await client.close()
    elif sys.argv[1] == 'balance':
        wallet = Wallet.load()
        if wallet is None:
            print("Error: no wallet found, use `create` first")
            help()
            sys.exit(1)
        if len(sys.argv) < 3:
            address = wallet.address
        else:
            address = sys.argv[2]
            if not validate_address(address):
                print("Error: invalid address")
                help()
                sys.exit(1)
        client = DolaClient(BASE_URL, wallet)
        resp = await client.get_balance(address)
        print(resp)
        await client.close()
    elif sys.argv[1] == 'events':
        wallet = Wallet.load()
        if wallet is None:
            print("Error: no wallet found, use `create` first")
            help()
            sys.exit(1)
        client = DolaClient(BASE_URL, wallet)
        if len(sys.argv) >= 3:
            from_event = int(sys.argv[2])
        else:
            from_event = 0
        resp = await client.get_events(from_event=from_event)
        for event in resp['events']:
            print(event)
        await client.close()
    elif sys.argv[1] == 'message':
        wallet = Wallet.load()
        if wallet is None:
            print("Error: no wallet found, use `create` first")
            help()
            sys.exit(1)
        if len(sys.argv) < 3:
            print("Error: missing address")
            help()
            sys.exit(1)
        address = sys.argv[2]
        if not validate_address(address):
            print("Error: invalid address")
            help()
            sys.exit(1)
        if len(sys.argv) < 4:
            print("Error: missing message")
            help()
            sys.exit(1)
        client = DolaClient(BASE_URL, wallet)
        resp = await client.send_message(address, ' '.join(sys.argv[3:]))
        print(resp)
        await client.close()
    elif sys.argv[1] == 'approve':
        wallet = Wallet.load()
        if wallet is None:
            print("Error: no wallet found, use `create` first")
            help()
            sys.exit(1)
        client = DolaClient(BASE_URL, wallet)
        resp = await client.approve()
        print(resp)
        await client.close()
    elif sys.argv[1] == 'pay':
        wallet = Wallet.load()
        if wallet is None:
            print("Error: no wallet found, use `create` first")
            help()
            sys.exit(1)
        if len(sys.argv) < 3:
            print("Error: missing address")
            help()
            sys.exit(1)
        address = sys.argv[2]
        if not validate_address(address):
            print("Error: invalid address")
            help()
            sys.exit(1)
        if len(sys.argv) < 4:
            print("Error: missing value")
            help()
            sys.exit(1)
        value = sys.argv[3]
        try:
            if value.startswith('0x'):
                pass # value = int(value, 16)
            else:
                pass # value = int(decimal.Decimal(value) * (10 ** 18))
        except ValueError:
            print("Error: invalid value '{}'".format(value))
        message = None
        if len(sys.argv) > 4:
            message = ' '.join(sys.argv[4:])
        client = DolaClient(BASE_URL, wallet)
        resp = await client.send_payment(address, value, message)
        print(resp)
        await client.close()
    elif sys.argv[1] == 'ephemeral_key':
        wallet = Wallet.load()
        if wallet is None:
            print("Error: no wallet found, use `create` first")
            help()
            sys.exit(1)
        client = DolaClient(BASE_URL, wallet)
        resp = await client.ephemeral_key()
        print(resp)
        await client.close()
    elif sys.argv[1] == 'purchase_info':
        wallet = Wallet.load()
        if wallet is None:
            print("Error: no wallet found, use `create` first")
            help()
            sys.exit(1)
        client = DolaClient(BASE_URL, wallet)
        resp = await client.purchase_info()
        print(resp)
        await client.close()
