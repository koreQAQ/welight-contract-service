from typing import Optional, List

from algosdk import account
from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient
from algosdk.kmd import KMDClient

from .account import Account
from .util import waitForTransaction

ALGOD_ADDRESS = "http://localhost:4001"
ALGOD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def getAlgodClient() -> AlgodClient:
    return AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)


KMD_ADDRESS = "http://localhost:4002"
KMD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def getKmdClient() -> KMDClient:
    return KMDClient(KMD_TOKEN, KMD_ADDRESS)


KMD_WALLET_NAME = "unencrypted-default-wallet"
KMD_WALLET_PASSWORD = ""

kmdAccounts: Optional[List[Account]] = None


def getGenesisAccounts() -> List[Account]:
    global kmdAccounts

    if kmdAccounts is None:
        kmd = getKmdClient()

        wallets = kmd.list_wallets()
        walletID = None
        for wallet in wallets:
            if wallet["name"] == KMD_WALLET_NAME:
                walletID = wallet["id"]
                break

        if walletID is None:
            raise Exception("Wallet not found: {}".format(KMD_WALLET_NAME))

        walletHandle = kmd.init_wallet_handle(walletID, KMD_WALLET_PASSWORD)

        try:
            addresses = kmd.list_keys(walletHandle)
            privateKeys = [
                kmd.export_key(walletHandle, KMD_WALLET_PASSWORD, addr)
                for addr in addresses
            ]
            kmdAccounts = [Account(sk) for sk in privateKeys]
        finally:
            kmd.release_wallet_handle(walletHandle)

    return kmdAccounts


def getOfficialAccount() -> Account:
    return getTemporaryAccount(getAlgodClient())
    # return Account('JH7D5MUTEFGJ635KRZZ2H3Z3PBT3ZWFDNSEX4VQGZDK7JBD2KIYZUBAUQY')


FUNDING_AMOUNT = 100_000_000


def getTemporaryAccount(client: AlgodClient) -> Account:
    accountList = []
    if len(accountList) == 0:
        sks = [account.generate_account()[0] for i in range(16)]
        accountList = [Account(sk) for sk in sks]

        genesisAccounts = getGenesisAccounts()
        suggestedParams = client.suggested_params()

        txns: List[transaction.Transaction] = []
        for i, a in enumerate(accountList):
            fundingAccount = genesisAccounts[i % len(genesisAccounts)]
            txns.append(
                transaction.PaymentTxn(
                    sender=fundingAccount.getAddress(),
                    receiver=a.getAddress(),
                    amt=FUNDING_AMOUNT,
                    sp=suggestedParams,
                )
            )

        txns = transaction.assign_group_id(txns)
        signedTxns = [
            txn.sign(genesisAccounts[i % len(genesisAccounts)].getPrivateKey())
            for i, txn in enumerate(txns)
        ]

        client.send_transactions(signedTxns)

        waitForTransaction(client, signedTxns[0].get_txid())

    return accountList.pop()
