import regex

RE_ETHEREUM_ADDRESS = regex.compile("^0x[a-fA-F0-9]{40}$")

def validate_address(address):
    if type(address) == bytes:
        if len(address) < 20:
            return False
        address = "0x" + address.hex()
    elif type(address) != str:
        return False
    return RE_ETHEREUM_ADDRESS.match(address) is not None
