#!/usr/bin/env python3
# encoding: utf-8

import unittest
import time
from SEEDBlockchain import Wallet
from web3 import Web3
from typing import List, Tuple

class MnemonicTransactionTest(unittest.TestCase):
    """Test case for transactions between accounts derived from mnemonic"""

    def setUp(self):
        """Setup connection to local Ethereum node and prepare accounts"""
        # Connect to Ethereum node using the Wallet class
        self.wallet = Wallet(mnemonic="great amazing fun seed lab protect network system security prevent attack future")
        self.wallet.connectToBlockchain('http://10.154.0.71:8545')
        
        # Create two accounts from the mnemonic
        self.wallet.createAccount("Account1")
        self.wallet.createAccount("Account2")
        
        # Set Account1 as default
        self.wallet.setDefaultAccount("Account1")
        
        # Print account addresses
        print(f"Account 1: {self.wallet.getAccountAddressByName('Account1')}")
        print(f"Account 2: {self.wallet.getAccountAddressByName('Account2')}")
        
        # Get Web3 instance for direct calls if needed
        self.w3 = self.wallet._web3
        
        # Ensure Account1 has enough ETH for tests
        self._ensure_account_funded("Account1")

    def _ensure_account_funded(self, account_name):
        """Make sure the account has enough ETH for testing"""
        balance = self.wallet.getBalanceByName(account_name)
        if balance < 0.01:  # If less than 0.01 ETH
            try:
                # Try to fund from coinbase
                coinbase = self.w3.eth.coinbase
                tx_hash = self.w3.eth.send_transaction({
                    'from': coinbase,
                    'to': self.wallet.getAccountAddressByName(account_name),
                    'value': Web3.toWei(0.1, 'ether')
                })
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                self.assertTrue(receipt['status'], "Funding transaction failed")
                print(f"Funded {account_name} with 0.1 ETH")
                time.sleep(1)  # Wait for transaction to be fully processed
            except Exception as e:
                print(f"Warning: Could not fund account automatically: {e}")
                print(f"Please ensure {account_name} has at least 0.01 ETH before running the test")
    
    def test_bidirectional_transfers(self):
        """Test transfers from account1 to account2 and then back"""
        # Get initial balances
        initial_balance1 = self.wallet.getBalanceByName("Account1")
        initial_balance2 = self.wallet.getBalanceByName("Account2")
        
        print(f"Initial balance Account1: {initial_balance1} ETH")
        print(f"Initial balance Account2: {initial_balance2} ETH")
        
        # Send ETH from Account1 to Account2
        transfer_amount = 0.01
        tx_hash1 = self.wallet.sendTransaction(
            recipient=self.wallet.getAccountAddressByName("Account2"),
            amount=transfer_amount,
            sender_name="Account1",
            wait=True,
            verbose=True
        )
        
        # Get transaction receipt to verify success
        receipt1 = self.wallet.getTransactionReceipt(tx_hash1)
        self.assertTrue(receipt1['status'], "First transaction failed")
        
        # Get balances after first transaction
        mid_balance1 = self.wallet.getBalanceByName("Account1")
        mid_balance2 = self.wallet.getBalanceByName("Account2")
        
        print(f"Mid balance Account1: {mid_balance1} ETH")
        print(f"Mid balance Account2: {mid_balance2} ETH")
        
        # Verify Account2 received the ETH
        expected_increase = transfer_amount
        actual_increase = mid_balance2 - initial_balance2
        self.assertAlmostEqual(actual_increase, expected_increase, delta=0.0001,
                             msg=f"Expected increase of {transfer_amount} ETH but got {actual_increase} ETH")
        
        # Send back from Account2 to Account1
        return_amount = 0.005  # Send back half the amount
        tx_hash2 = self.wallet.sendTransaction(
            recipient=self.wallet.getAccountAddressByName("Account1"),
            amount=return_amount,
            sender_name="Account2",
            wait=True,
            verbose=True
        )
        
        # Get transaction receipt to verify success
        receipt2 = self.wallet.getTransactionReceipt(tx_hash2)
        self.assertTrue(receipt2['status'], "Second transaction failed")
        
        # Get final balances
        final_balance1 = self.wallet.getBalanceByName("Account1")
        final_balance2 = self.wallet.getBalanceByName("Account2")
        
        print(f"Final balance Account1: {final_balance1} ETH")
        print(f"Final balance Account2: {final_balance2} ETH")
        
        # Verify Account1 received the ETH back
        expected_increase = return_amount
        actual_increase = final_balance1 - mid_balance1
        self.assertAlmostEqual(actual_increase, expected_increase, delta=0.0001,
                             msg=f"Expected Account1 to receive {return_amount} ETH but got {actual_increase} ETH")
        
        print("Test completed successfully!")

if __name__ == '__main__':
    unittest.main()