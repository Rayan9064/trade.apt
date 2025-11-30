"""
Aptos Blockchain Utilities
==========================
Handles Aptos-specific operations:
- Wallet verification
- Balance checking
- Testnet faucet funding
- Transaction building

For Testnet/Devnet:
- Faucet URL: https://faucet.testnet.aptoslabs.com
- Explorer: https://explorer.aptoslabs.com/?network=testnet
"""

import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class AptosNetwork(Enum):
    """Aptos network configurations."""
    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"


# Network configurations
NETWORK_CONFIG = {
    AptosNetwork.MAINNET: {
        "name": "Mainnet",
        "node_url": "https://fullnode.mainnet.aptoslabs.com/v1",
        "faucet_url": None,  # No faucet on mainnet
        "explorer_url": "https://explorer.aptoslabs.com",
        "chain_id": 1,
    },
    AptosNetwork.TESTNET: {
        "name": "Testnet",
        "node_url": "https://fullnode.testnet.aptoslabs.com/v1",
        "faucet_url": "https://faucet.testnet.aptoslabs.com",
        "explorer_url": "https://explorer.aptoslabs.com/?network=testnet",
        "chain_id": 2,
    },
    AptosNetwork.DEVNET: {
        "name": "Devnet",
        "node_url": "https://fullnode.devnet.aptoslabs.com/v1",
        "faucet_url": "https://faucet.devnet.aptoslabs.com",
        "explorer_url": "https://explorer.aptoslabs.com/?network=devnet",
        "chain_id": 3,
    },
}


@dataclass
class WalletBalance:
    """Wallet balance information."""
    address: str
    apt_balance: float  # In APT (not octas)
    apt_balance_octas: int  # Raw octas (1 APT = 100_000_000 octas)
    usd_value: Optional[float] = None
    network: str = "testnet"


@dataclass
class AccountInfo:
    """Aptos account information."""
    address: str
    sequence_number: int
    authentication_key: str
    exists: bool = True


def get_network_config(network: AptosNetwork) -> Dict[str, Any]:
    """Get configuration for a network."""
    return NETWORK_CONFIG.get(network, NETWORK_CONFIG[AptosNetwork.TESTNET])


async def verify_wallet_address(address: str) -> bool:
    """
    Verify if an address is a valid Aptos address format.
    Aptos addresses are 64-character hex strings (66 with 0x prefix).
    """
    if not address:
        return False
    
    # Remove 0x prefix if present
    clean_address = address.lower()
    if clean_address.startswith("0x"):
        clean_address = clean_address[2:]
    
    # Must be 64 hex characters
    if len(clean_address) != 64:
        return False
    
    # Must be valid hex
    try:
        int(clean_address, 16)
        return True
    except ValueError:
        return False


async def get_account_info(
    address: str,
    network: AptosNetwork = AptosNetwork.TESTNET
) -> Optional[AccountInfo]:
    """Get account information from Aptos node."""
    config = get_network_config(network)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{config['node_url']}/accounts/{address}"
            response = await client.get(url)
            
            if response.status_code == 404:
                # Account doesn't exist yet (not funded)
                return AccountInfo(
                    address=address,
                    sequence_number=0,
                    authentication_key="",
                    exists=False
                )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            return AccountInfo(
                address=address,
                sequence_number=int(data.get("sequence_number", 0)),
                authentication_key=data.get("authentication_key", ""),
                exists=True
            )
            
    except Exception as e:
        print(f"Error getting account info: {e}")
        return None


async def get_wallet_balance(
    address: str,
    network: AptosNetwork = AptosNetwork.TESTNET,
    apt_price_usd: Optional[float] = None
) -> Optional[WalletBalance]:
    """
    Get APT balance for a wallet.
    
    Returns balance in both APT and octas (1 APT = 100,000,000 octas).
    """
    config = get_network_config(network)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # APT coin resource
            url = f"{config['node_url']}/accounts/{address}/resource/0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>"
            response = await client.get(url)
            
            if response.status_code == 404:
                # Account exists but has no APT
                return WalletBalance(
                    address=address,
                    apt_balance=0.0,
                    apt_balance_octas=0,
                    usd_value=0.0,
                    network=network.value
                )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            octas = int(data.get("data", {}).get("coin", {}).get("value", 0))
            apt = octas / 100_000_000  # Convert to APT
            
            usd_value = None
            if apt_price_usd:
                usd_value = apt * apt_price_usd
            
            return WalletBalance(
                address=address,
                apt_balance=apt,
                apt_balance_octas=octas,
                usd_value=usd_value,
                network=network.value
            )
            
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
        return None


async def fund_from_faucet(
    address: str,
    amount_apt: float = 1.0,
    network: AptosNetwork = AptosNetwork.TESTNET
) -> Dict[str, Any]:
    """
    Request tokens from the testnet/devnet faucet.
    
    This only works on testnet and devnet, NOT mainnet.
    Default amount is 1 APT.
    
    Returns:
        Success/failure status and transaction hashes if successful.
    """
    config = get_network_config(network)
    
    if not config.get("faucet_url"):
        return {
            "success": False,
            "error": "Faucet not available on mainnet. Please acquire APT through an exchange."
        }
    
    try:
        # Convert APT to octas
        amount_octas = int(amount_apt * 100_000_000)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # The Aptos faucet API has changed - try different endpoints
            faucet_endpoints = [
                f"{config['faucet_url']}/mint",
                f"{config['faucet_url']}/fund",
            ]
            
            for endpoint in faucet_endpoints:
                try:
                    params = {
                        "address": address,
                        "amount": amount_octas
                    }
                    
                    response = await client.post(endpoint, params=params)
                    
                    if response.status_code == 200:
                        tx_hashes = response.json()
                        
                        return {
                            "success": True,
                            "amount_apt": amount_apt,
                            "tx_hashes": tx_hashes if isinstance(tx_hashes, list) else [tx_hashes],
                            "message": f"Successfully funded {amount_apt} APT to {address[:10]}...{address[-6:]}",
                            "explorer_url": f"{config['explorer_url']}/txn/{tx_hashes[0] if isinstance(tx_hashes, list) and tx_hashes else ''}"
                        }
                except Exception:
                    continue
            
            # If all endpoints failed, provide helpful guidance
            return {
                "success": False,
                "error": "Faucet API unavailable. Please use the web faucet instead.",
                "faucet_url": "https://aptoslabs.com/testnet-faucet",
                "instructions": [
                    "1. Visit https://aptoslabs.com/testnet-faucet",
                    "2. Enter your wallet address",
                    "3. Complete the captcha",
                    "4. Click 'Request Tokens'",
                    f"Your address: {address}"
                ]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Faucet request error: {str(e)}",
            "faucet_url": "https://aptoslabs.com/testnet-faucet"
        }


async def get_account_transactions(
    address: str,
    network: AptosNetwork = AptosNetwork.TESTNET,
    limit: int = 25
) -> List[Dict[str, Any]]:
    """Get recent transactions for an account."""
    config = get_network_config(network)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{config['node_url']}/accounts/{address}/transactions"
            params = {"limit": limit}
            
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                return []
            
            transactions = response.json()
            
            # Simplify transaction data
            simplified = []
            for tx in transactions:
                simplified.append({
                    "hash": tx.get("hash"),
                    "type": tx.get("type"),
                    "success": tx.get("success", False),
                    "timestamp": tx.get("timestamp"),
                    "gas_used": tx.get("gas_used"),
                    "version": tx.get("version"),
                })
            
            return simplified
            
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return []


def get_explorer_url(
    tx_hash: Optional[str] = None,
    address: Optional[str] = None,
    network: AptosNetwork = AptosNetwork.TESTNET
) -> str:
    """Get explorer URL for a transaction or address."""
    config = get_network_config(network)
    base_url = config["explorer_url"]
    
    if tx_hash:
        return f"{base_url}/txn/{tx_hash}"
    elif address:
        return f"{base_url}/account/{address}"
    else:
        return base_url


# =============================================================================
# Helpful Information for Beginners
# =============================================================================

APTOS_GETTING_STARTED = """
## Getting Started with Aptos (For Beginners)

### What is Aptos?
Aptos is a Layer 1 blockchain designed for safety and scalability. 
It uses the Move programming language and can handle thousands of transactions per second.

### Networks:
1. **Mainnet** - Real money, real transactions (be careful!)
2. **Testnet** - Free test tokens, perfect for development
3. **Devnet** - Even more experimental, resets frequently

### Getting Free Testnet APT:
1. **Web Faucet**: https://aptoslabs.com/testnet-faucet
2. **This App**: Use the "Get Test APT" button in wallet settings
3. **CLI**: `aptos account fund-with-faucet --account YOUR_ADDRESS`

### Wallets (Choose One):
- **Petra** (Recommended): https://petra.app - Official Aptos wallet
- **Pontem**: https://pontem.network - Full-featured wallet
- **Martian**: https://martianwallet.xyz - Mobile-friendly
- **Fewcha**: https://fewcha.app - Simple interface

### Setting Up Your Wallet:
1. Install a wallet browser extension
2. Create a new account (save your recovery phrase!)
3. Switch to "Testnet" network in wallet settings
4. Get free test APT from the faucet
5. Start trading!

### Important Concepts:
- **APT**: Native token of Aptos (like ETH for Ethereum)
- **Octas**: Smallest unit (1 APT = 100,000,000 octas)
- **Gas**: Fee for transactions (paid in APT)
- **Transaction**: Any action on the blockchain
"""


def get_onboarding_info() -> Dict[str, Any]:
    """Get onboarding information for new users."""
    return {
        "guide": APTOS_GETTING_STARTED,
        "wallets": [
            {
                "name": "Petra",
                "url": "https://petra.app",
                "recommended": True,
                "description": "Official Aptos wallet, best for beginners"
            },
            {
                "name": "Pontem",
                "url": "https://pontem.network",
                "recommended": False,
                "description": "Full-featured wallet with DeFi integration"
            },
            {
                "name": "Martian",
                "url": "https://martianwallet.xyz",
                "recommended": False,
                "description": "Mobile-friendly with NFT support"
            }
        ],
        "faucets": {
            "testnet": "https://aptoslabs.com/testnet-faucet",
            "devnet": "https://aptoslabs.com/devnet-faucet"
        },
        "explorer": {
            "mainnet": "https://explorer.aptoslabs.com",
            "testnet": "https://explorer.aptoslabs.com/?network=testnet"
        }
    }
