# Setup

```
virtualenv -p python3 env
env/bin/pip install -r requirements.txt
```

# Initial start

## Create a wallet

```
env/bin/python -m dola create
```

## Send a payment

NOTE: you need to have DAI in the created account.

```
env/bin/python -m dola pay <target-address>
```

## Approval

Aprroval is needed before or after the first payment is made. It is needed to allow Dola to transfer DAI on behalf of the user's account.

If your account has ETH, it will use some of that ETH to execute an approval.
If your account only has DAI, and has a pending payment, Dola will send you some ETH and execute the approval after that ETH comes into your account.

```
env/bin/python -m dola approve
```
