"""
pip install monero
"""

from monero.wallet import Wallet

from monero.backends.jsonrpc import JSONRPCWallet

w = Wallet(JSONRPCWallet(port=18082))

print(w.address())
print(w.balance())
