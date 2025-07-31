import requests
import time
from datetime import datetime, timedelta
import json
from collections import defaultdict

class PolymarketAPI:
    """API wrapper for Polymarket endpoints with correct field names"""
    
    def __init__(self):
        self.base_url = "https://data-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PolymarketAnalyzer/1.0'
        })
    
    def test_connection(self):
        """Test if we can connect to the API"""
        try:
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
                    
                    # Check for user address field
                    proxy_wallet = sample_trade.get('proxyWallet')
                    if proxy_wallet:
                        print(f"   Found user address field: proxyWallet = {proxy_wallet[:10]}...")
                
                return True
            else:
                print(f"❌ API Connection failed! Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def fetch_trades_page(self, limit=100, offset=0, taker_only=True, user=None):
        """
        Fetch a single page of trades from the API
        
        Args:
            limit: Number of trades to fetch (max 500)
            offset: Starting index for pagination  
            taker_only: If True, only return taker orders (default True per API)
            user: Optional user address to filter trades
        
        Returns:
            List of trades or None if error
        """
        try:
            # Build parameters according to API docs
            params = {
                'limit': min(limit, 500),  # API max is 500
                'offset': offset,
                'takerOnly': str(taker_only).lower()  # API expects string boolean
            }
            
            # Add user filter if provided
            if user:
                params['user'] = user
            
            print(f"Fetching trades: limit={limit}, offset={offset}, takerOnly={taker_only}")
            if user:
                print(f"  Filtering for user: {user[:10]}...{user[-6:]}")
            
            response = self.session.get(
                f"{self.base_url}/trades",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                trades = response.json()
                print(f"✅ Successfully fetched {len(trades)} trades")
                return trades
            else:
                print(f"❌ API Error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

def analyze_trade_structure(trades):
    """Analyze the structure of trade data"""
    if not trades:
        print("No trades to analyze")
        return
    
    print(f"\n=== Analyzing Trade Data Structure ===")
    print(f"Total trades received: {len(trades)}")
    
    # Look at the first trade
    sample_trade = trades[0]
    print(f"\nSample trade keys: {list(sample_trade.keys())}")
    
    # Print key fields from sample trade - using CORRECT field names
    print(f"\nKey trade data:")
    important_fields = ['timestamp', 'proxyWallet', 'price', 'size', 'side', 'conditionId', 'title']
    for field in important_fields:
        value = sample_trade.get(field, 'NOT FOUND')
        print(f"  {field}: {value}")
    
    # Check timestamp format and convert to readable date
    if 'timestamp' in sample_trade:
        ts = sample_trade['timestamp']
        print(f"  timestamp as date: {datetime.fromtimestamp(ts)}")
    
    # Show what fields are available for user identification
    user_fields = ['proxyWallet', 'name', 'pseudonym']
    print(f"\nUser identification fields:")
    for field in user_fields:
        value = sample_trade.get(field, 'NOT FOUND')
        print(f"  {field}: {value}")

def extract_user_addresses(trades):
    """Extract unique user addresses from trades using correct field name"""
    user_addresses = set()
    trade_counts = defaultdict(int)
    user_names = {}  # Store user names for reference
    
    print(f"\n=== Extracting User Addresses ===")
    
    for trade in trades:
        # Extract addresses using CORRECT field name
        proxy_wallet = trade.get('proxyWallet')  # This is the correct field!
        user_name = trade.get('name', '')
        pseudonym = trade.get('pseudonym', '')
        
        if proxy_wallet:
            user_addresses.add(proxy_wallet)
            trade_counts[proxy_wallet] += 1
            
            # Store user display info
            if proxy_wallet not in user_names:
                display_name = user_name or pseudonym or 'Anonymous'
                user_names[proxy_wallet] = display_name
    
    print(f"Found {len(user_addresses)} unique user addresses")
    
    # Show top active users
    top_users = sorted(trade_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"\nTop 5 most active users in this sample:")
    for i, (address, count) in enumerate(top_users, 1):
        display_name = user_names.get(address, 'Unknown')
        print(f"  {i}. {address[:10]}...{address[-6:]} ({display_name}) - {count} trades")
    
    return user_addresses, trade_counts, user_names

def filter_trades_by_time(trades, cutoff_timestamp):
    """Filter trades to only include those after cutoff timestamp"""
    if not trades:
        return []
    
    recent_trades = []
    old_trades = 0
    
    for trade in trades:
        trade_timestamp = trade.get('timestamp', 0)
        
        if trade_timestamp >= cutoff_timestamp:
            recent_trades.append(trade)
        else:
            old_trades += 1
    
    print(f"\nTime filtering results:")
    print(f"  Recent trades (last 6 months): {len(recent_trades)}")
    print(f"  Older trades: {old_trades}")
    
    if recent_trades:
        oldest_recent = min(trade.get('timestamp', 0) for trade in recent_trades)
        newest_recent = max(trade.get('timestamp', 0) for trade in recent_trades)
        print(f"  Date range of recent trades:")
        print(f"    From: {datetime.fromtimestamp(oldest_recent)}")
        print(f"    To: {datetime.fromtimestamp(newest_recent)}")
    
    return recent_trades

def analyze_trade_volume(trades):
    """Analyze trading volume from the trades"""
    if not trades:
        return
    
    print(f"\n=== Trade Volume Analysis ===")
    
    total_volume = 0
    buy_volume = 0
    sell_volume = 0
    buy_count = 0
    sell_count = 0
    
    for trade in trades:
        size = trade.get('size', 0)
        price = trade.get('price', 0)
        side = trade.get('side', '')
        
        try:
            trade_value = float(size) * float(price)
            total_volume += trade_value
            
            if side == 'BUY':
                buy_volume += trade_value
                buy_count += 1
            elif side == 'SELL':
                sell_volume += trade_value
                sell_count += 1
                
        except (ValueError, TypeError):
            continue
    
    print(f"Total volume: ${total_volume:.2f}")
    print(f"Buy volume: ${buy_volume:.2f} ({buy_count} trades)")
    print(f"Sell volume: ${sell_volume:.2f} ({sell_count} trades)")

def test_fixed_chunk2():
    """Test the fixed API calls with correct field names"""
    print("=== Testing Chunk 2 (Fixed): Correct Field Names ===\n")
    
    # Setup
    api = PolymarketAPI()
    six_months_ago = int((datetime.now() - timedelta(days=180)).timestamp())
    print(f"Looking for trades since: {datetime.fromtimestamp(six_months_ago)}")
    
    # Test 1: Basic connection
    print("\nTest 1: API Connection")
    if not api.test_connection():
        print("❌ Cannot proceed without API connection")
        return
    
    # Test 2: Fetch trades with correct parameters
    print("\nTest 2: Fetch trades with corrected parameters")
    trades = api.fetch_trades_page(limit=20, offset=0, taker_only=False)  # Get both maker and taker
    
    if not trades:
        print("❌ Failed to fetch trades")
        return
    
    # Test 3: Analyze structure with correct field names
    print("\nTest 3: Analyze trade structure")
    analyze_trade_structure(trades)
    
    # Test 4: Extract user addresses using CORRECT field name
    print("\nTest 4: Extract user addresses (using proxyWallet)")
    user_addresses, trade_counts, user_names = extract_user_addresses(trades)
    
    # Test 5: Filter by time
    print("\nTest 5: Filter trades by time (6 months)")
    recent_trades = filter_trades_by_time(trades, six_months_ago)
    
    # Test 6: Analyze volume
    print("\nTest 6: Analyze trade volume")
    analyze_trade_volume(trades)
    
    # Test 7: Test user-specific trade fetching
    if user_addresses:
        test_user = list(user_addresses)[0]
        test_user_name = user_names.get(test_user, 'Unknown')
        print(f"\nTest 7: Fetch trades for specific user")
        print(f"Testing with: {test_user[:10]}... ({test_user_name})")
        user_trades = api.fetch_trades_page(limit=10, user=test_user)
        if user_trades:
            print(f"  ✅ Found {len(user_trades)} trades for this user")
        else:
            print(f"  ℹ️  No trades found for this user")
    
    print(f"\n✅ Chunk 2 (Fixed) completed successfully!")
    print(f"   API parameters and field names verified")
    print(f"   Fetched {len(trades)} trades")
    print(f"   Found {len(user_addresses)} unique users")
    print(f"   {len(recent_trades)} trades from last 6 months")
    
    return api, trades, user_addresses, trade_counts, recent_trades

if __name__ == "__main__":
    results = test_fixed_chunk2()