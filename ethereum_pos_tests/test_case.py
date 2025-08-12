#!/usr/bin/env python3
# encoding: utf-8

import unittest
import time
import os
from web3 import Web3
from eth_account import Account
from typing import List, Tuple

# Enable deriving accounts from mnemonic
Account.enable_unaudited_hdwallet_features()

class MnemonicTransactionTest(unittest.TestCase):
    """Test case for transactions between accounts derived from mnemonic"""

    def setUp(self):
        """Setup connection to local Ethereum node and prepare accounts"""
        # Connect to Ethereum node at the specified IP and port
        self.w3 = Web3(Web3.HTTPProvider('http://10.154.0.71:8545'))
        
        if not self.w3.is_connected():
            self.fail("Could not connect to Ethereum node at 10.154.0.71:8545")
        
        # Custom mnemonic for testing
        self.mnemonic = "great amazing fun seed lab protect network system security prevent attack future"
        
        # Derive two accounts from the mnemonic
        self.account1, self.account2 = self._derive_accounts_from_mnemonic(self.mnemonic, 2)
        
        print(f"Account 1: {self.account1.address}")
        print(f"Account 2: {self.account2.address}")
        
        # Ensure account1 has enough ETH for tests
        self._ensure_account_funded(self.account1.address)

    def _derive_accounts_from_mnemonic(self, mnemonic: str, count: int) -> List[Account]:
        """Derive multiple accounts from a mnemonic phrase"""
        accounts = []
        for i in range(count):
            account = Account.from_mnemonic(
                mnemonic,
                account_path=f"m/44'/60'/0'/0/{i}"  # Standard Ethereum derivation path
            )
            accounts.append(account)
        return accounts
    
    def _ensure_account_funded(self, address: str):
        """Make sure the account has enough ETH for testing"""
        balance = self.w3.eth.get_balance(address)
        if balance < Web3.to_wei(0.01, 'ether'):
            # If running in a test environment, we can get ETH from a coinbase account
            coinbase = self.w3.eth.coinbase
            tx_hash = self.w3.eth.send_transaction({
                'from': coinbase,
                'to': address,
                'value': Web3.to_wei(0.1, 'ether')
            })
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.assertTrue(receipt.status, "Funding transaction failed")
            print(f"Funded account {address} with 0.1 ETH")
            time.sleep(1)  # Wait for transaction to be fully processed
    
    def _get_balance(self, address: str) -> int:
        """Get account balance in Wei"""
        return self.w3.eth.get_balance(address)
    
    def _send_transaction(self, from_account: Account, to_address: str, amount_eth: float) -> Tuple[str, dict]:
        """Send a transaction and return the hash and receipt"""
        # Get the current nonce for the sender account
        nonce = self.w3.eth.get_transaction_count(from_account.address)
        
        # Build the transaction
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': Web3.to_wei(amount_eth, 'ether'),
            'gas': 21000,  # Standard gas limit for a transfer
            'gasPrice': self.w3.eth.gas_price,
            'chainId': self.w3.eth.chain_id
        }
        
        # Sign the transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx, from_account.key)
        
        # Send the transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for the transaction to be mined
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_hash.hex(), receipt
    
    def test_bidirectional_transfers(self):
        """Test transfers from account1 to account2 and then back"""
        # Get initial balances
        initial_balance1 = self._get_balance(self.account1.address)
        initial_balance2 = self._get_balance(self.account2.address)
        
        print(f"Initial balance account1: {Web3.from_wei(initial_balance1, 'ether')} ETH")
        print(f"Initial balance account2: {Web3.from_wei(initial_balance2, 'ether')} ETH")
        
        # Send ETH from account1 to account2
        transfer_amount = 0.01
        tx_hash1, receipt1 = self._send_transaction(self.account1, self.account2.address, transfer_amount)
        
        # Verify transaction succeeded
        self.assertTrue(receipt1.status, "First transaction failed")
        print(f"Transaction 1 completed: {tx_hash1}")
        
        # Get balances after first transaction
        mid_balance1 = self._get_balance(self.account1.address)
        mid_balance2 = self._get_balance(self.account2.address)
        
        print(f"Mid balance account1: {Web3.from_wei(mid_balance1, 'ether')} ETH")
        print(f"Mid balance account2: {Web3.from_wei(mid_balance2, 'ether')} ETH")
        
        # Verify account2 received the ETH (with some tolerance for gas costs)
        expected_increase = Web3.to_wei(transfer_amount, 'ether')
        actual_increase = mid_balance2 - initial_balance2
        self.assertEqual(actual_increase, expected_increase, 
                         f"Expected increase of {transfer_amount} ETH but got {Web3.from_wei(actual_increase, 'ether')} ETH")
        
        # Verify account1 balance decreased by transfer amount plus gas
        expected_decrease = Web3.to_wei(transfer_amount, 'ether') + (receipt1.gasUsed * self.w3.eth.gas_price)
        actual_decrease = initial_balance1 - mid_balance1
        self.assertAlmostEqual(actual_decrease, expected_decrease, delta=1000,  # Allow small delta for calculation
                              msg=f"Expected decrease not matching actual decrease")
        
        # Send back from account2 to account1
        return_amount = 0.005  # Send back half the amount
        tx_hash2, receipt2 = self._send_transaction(self.account2, self.account1.address, return_amount)
        
        # Verify transaction succeeded
        self.assertTrue(receipt2.status, "Second transaction failed")
        print(f"Transaction 2 completed: {tx_hash2}")
        
        # Get final balances
        final_balance1 = self._get_balance(self.account1.address)
        final_balance2 = self._get_balance(self.account2.address)
        
        print(f"Final balance account1: {Web3.from_wei(final_balance1, 'ether')} ETH")
        print(f"Final balance account2: {Web3.from_wei(final_balance2, 'ether')} ETH")
        
        # Verify account1 received the ETH back
        expected_increase = Web3.to_wei(return_amount, 'ether')
        actual_increase = final_balance1 - mid_balance1
        self.assertEqual(actual_increase, expected_increase,
                        f"Expected account1 to receive {return_amount} ETH but got {Web3.from_wei(actual_increase, 'ether')} ETH")
        
        # Verify account2 balance decreased by return amount plus gas
        expected_decrease = Web3.to_wei(return_amount, 'ether') + (receipt2.gasUsed * self.w3.eth.gas_price)
        actual_decrease = mid_balance2 - final_balance2
        self.assertAlmostEqual(actual_decrease, expected_decrease, delta=1000,  # Allow small delta for calculation
                              msg=f"Expected decrease from account2 not matching actual decrease")
        
        print("Test completed successfully!")

if __name__ == '__main__':
    unittest.main()