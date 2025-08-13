#!/usr/bin/env python3
# encoding: utf-8

from SEEDBlockchain import Wallet

# Set your Ethereum node URL
eth_node_url = 'http://10.154.0.71:8545'

# Create wallet and connect
wallet = Wallet(mnemonic="great amazing fun seed lab protect network system security prevent attack future")
wallet.connectToBlockchain(eth_node_url)

# Get current block number
block_number = wallet._web3.eth.block_number
print(f"Current block number: {block_number}")
