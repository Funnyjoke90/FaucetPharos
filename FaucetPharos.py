import requests
import time
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3

# Faucet API & RPC
FAUCET_API = "https://faucet.pharos.sh/claim"  # သင်သိတဲ့ faucet URL
RPC_URL = "https://rpc.pharos.sh"              # RPC URL

web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Load main wallet
with open("wallet.txt", "r") as f:
    MAIN_WALLET = f.read().strip()

def create_wallet():
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
    seed = Bip39SeedGenerator(mnemonic).Generate()
    bip44 = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
    addr_obj = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
    return {
        "address": addr_obj.PublicKey().ToAddress(),
        "private_key": addr_obj.PrivateKey().Raw().ToHex(),
    }

def claim_faucet(address):
    try:
        res = requests.post(FAUCET_API, json={"address": address})
        print(f"[CLAIM] {address} => {res.status_code} {res.text}")
    except Exception as e:
        print(f"[ERROR] Claiming {address} => {e}")

def transfer_funds(wallet):
    try:
        from_addr = wallet["address"]
        priv_key = wallet["private_key"]
        nonce = web3.eth.get_transaction_count(from_addr)
        balance = web3.eth.get_balance(from_addr)
        gas_price = web3.eth.gas_price
        gas = 21000

        if balance < gas_price * gas:
            print(f"[SKIP] {from_addr} has low balance")
            return

        tx = {
            "nonce": nonce,
            "to": MAIN_WALLET,
            "value": balance - gas_price * gas,
            "gas": gas,
            "gasPrice": gas_price,
        }

        signed_tx = web3.eth.account.sign_transaction(tx, priv_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"[SEND] {from_addr} => {MAIN_WALLET} | tx: {tx_hash.hex()}")

    except Exception as e:
        print(f"[ERROR] Transfer from {wallet['address']} => {e}")

def main():
    try:
        loops = int(input("ဘယ်နှကြိမ်လုပ်မလဲ?: "))
    except ValueError:
        print("ကျေးဇူးပြုပြီး ဂဏန်းဖြင့်ထည့်ပါ")
        return

    for i in range(loops):
        print(f"\n=== Loop {i+1} / {loops} ===")
        wallets = [create_wallet() for _ in range(10)]
        for w in wallets:
            claim_faucet(w['address'])
            time.sleep(5)  # Faucet cooldown
            transfer_funds(w)
        print("Loop အပြီး... 30 seconds နားကြတယ်...\n")
        time.sleep(30)

if __name__ == "__main__":
    main()
