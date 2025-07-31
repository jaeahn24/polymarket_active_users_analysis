import requests
import time
from datetime import datetime, timedelta
import json

class PolymarketAPI:
    """Basic API wrapper for Polymarket endpoints"""
    
    def __init__(self):
        self.base_url = "https://data-api.polymarket.com"
        self.session = requests.Session()
        # Add user agent to be respectful
        self.session.headers.update({
            'User-Agent': 'PolymarketAnalyzer/1.0'
        })
    
    def test_connection(self):
        """Test if we can connect to the API"""
        try:
            # Try to fetch just 1 trade to test connection
            response = self.session.get(
                f"{self.base_url}/trades",
                params={'limit': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Connection successful!")
                print(f"   Status: {response.status_code}")
                print(f"   Response contains {len(data)} trades")
                
                if data:
                    sample_trade = data[0]
                    print(f"   Sample trade keys: {list(sample_trade.keys())}")
                    print(f"   Sample timestamp: {sample_trade.get('timestamp', 'N/A')}")
                
                return True
            else:
                print(f"❌ API Connection failed!")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

def calculate_timestamp_6_months_ago():
    """Calculate timestamp for 6 months ago"""
    six_months_ago = datetime.now() - timedelta(days=180)
    timestamp = int(six_months_ago.timestamp())
    
    print(f"Current time: {datetime.now()}")
    print(f"6 months ago: {six_months_ago}")
    print(f"Timestamp: {timestamp}")
    
    return timestamp

def test_chunk1():
    """Test all functionality in chunk 1"""
    print("=== Testing Chunk 1: Basic API Setup ===\n")
    
    # Test 1: Calculate timestamp
    print("Test 1: Calculate 6 months ago timestamp")
    timestamp = calculate_timestamp_6_months_ago()
    print()
    
    # Test 2: API connection
    print("Test 2: Test API connection")
    api = PolymarketAPI()
    connection_success = api.test_connection()
    print()
    
    if connection_success:
        print("✅ Chunk 1 completed successfully!")
        return api, timestamp
    else:
        print("❌ Chunk 1 failed - check your internet connection")
        return None, None

if __name__ == "__main__":
    api, timestamp = test_chunk1()