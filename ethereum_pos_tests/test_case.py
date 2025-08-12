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
        # First check if the host is reachable
        eth_host = '10.154.0.71'
        eth_port = 8545
        
        # Check if host is reachable using ping
        import subprocess
        import socket
        
        print(f"Checking if {eth_host} is reachable...")
        try:
            # Try to ping the host (1 packet, 1 second timeout)
            ping_result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', eth_host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if ping_result.returncode != 0:
                self.fail(f"Host {eth_host} is not reachable. Check network connectivity.")
                
            # Check if the port is open
            print(f"Checking if port {eth_port} is open on {eth_host}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex((eth_host, eth_port))
            s.close()
            
            if result != 0:
                self.fail(f"Port {eth_port} is not open on {eth_host}. Check if Ethereum node is running.")
                
            print(f"Host {eth_host}:{eth_port} is reachable and port is open.")
            
        except Exception as e:
            self.fail(f"Connection check failed: {str(e)}")
        
        # Connect to Ethereum node using the Wallet class
        try:
            print("Creating wallet with mnemonic...")
            self.wallet = Wallet(mnemonic="great amazing fun seed lab protect network system security prevent attack future")
            
            print(f"Connecting to Ethereum node at http://{eth_host}:{eth_port}...")
            self.wallet.connectToBlockchain(f'http://{eth_host}:{eth_port}')
            
            # Additional check for RPC connection
            if not self.wallet._web3.isConnected():
                self.fail(f"Web3 reports not connected to Ethereum node at http://{eth_host}:{eth_port}")
                
            print("Successfully connected to Ethereum node.")
                
            # Create two accounts from the mnemonic
            print("Creating accounts from mnemonic...")
            self.wallet.createAccount("Account1")
            self.wallet.createAccount("Account2")
            
            # Set Account1 as default
            self.wallet.setDefaultAccount("Account1")
        except AssertionError as ae:
            self.fail(f"Blockchain connection failed: {str(ae)}")
        except Exception as e:
            self.fail(f"Setup failed: {str(e)}")
        
        # Print account addresses
        print(f"Account 1: {self.wallet.getAccountAddressByName('Account1')}")
        print(f"Account 2: {self.wallet.getAccountAddressByName('Account2')}")
        
        # Get Web3 instance for direct calls if needed
        self.w3 = self.wallet._web3
        
        # Ensure Account1 has enough ETH for tests
        self._ensure_account_funded("Account1")

    def _ensure_account_funded(self, account_name):
        """Make sure the account has enough ETH for testing"""
        try:
            balance = self.wallet.getBalanceByName(account_name)
            print(f"Current balance of {account_name}: {balance} ETH")
            
            if balance < 0.01:  # If less than 0.01 ETH
                print(f"Account {account_name} needs funding (balance: {balance} ETH)")
                
                # Try to get coinbase account
                try:
                    coinbase = self.w3.eth.coinbase
                    print(f"Using coinbase account {coinbase} to fund test account")
                    
                    # Get coinbase balance
                    coinbase_balance = self.w3.eth.get_balance(coinbase)
                    print(f"Coinbase balance: {Web3.fromWei(coinbase_balance, 'ether')} ETH")
                    
                    if coinbase_balance < Web3.toWei(0.1, 'ether'):
                        print(f"Warning: Coinbase account has low balance ({Web3.fromWei(coinbase_balance, 'ether')} ETH)")
                    
                    # Send transaction
                    tx_hash = self.w3.eth.send_transaction({
                        'from': coinbase,
                        'to': self.wallet.getAccountAddressByName(account_name),
                        'value': Web3.toWei(0.1, 'ether')
                    })
                    
                    print(f"Funding transaction sent: {tx_hash.hex()}")
                    print("Waiting for transaction receipt...")
                    
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                    
                    if receipt['status'] == 1:
                        print(f"Successfully funded {account_name} with 0.1 ETH")
                    else:
                        self.fail(f"Funding transaction failed: {receipt}")
                        
                    # Wait and check new balance
                    time.sleep(2)
                    new_balance = self.wallet.getBalanceByName(account_name)
                    print(f"New balance of {account_name}: {new_balance} ETH")
                    
                    if new_balance < 0.01:
                        self.fail(f"Account {account_name} still has insufficient funds after funding attempt")
                    
                except Exception as e:
                    print(f"Warning: Could not fund account automatically: {str(e)}")
                    self.fail(f"Test requires {account_name} to have at least 0.01 ETH. Please fund the account manually.")
        except Exception as e:
            self.fail(f"Error checking or funding account: {str(e)}")
    
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