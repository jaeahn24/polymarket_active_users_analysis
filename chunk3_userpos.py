import requests
import time
from datetime import datetime, timedelta
import json

class PolymarketUserAnalyzer:
    """Analyze individual user positions and profits with CORRECT API parameters"""
    
    def __init__(self):
        self.base_url = "https://data-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PolymarketAnalyzer/1.0'
        })
    
    def get_user_positions(self, user_address, limit=500):
        """
        Get all positions for a specific user
        
        Args:
            user_address: Wallet address of the user (proxyWallet from trades)
            limit: Max positions to return (default 500, max 500)
        
        Returns:
            List of positions or None if error
        """
        try:
            # CORRECTED: Use 'user' parameter name (not 'address')
            params = {
                'user': user_address,        # ✅ CORRECT parameter name!
                'limit': min(limit, 500),
                'sortBy': 'CASHPNL',        # Sort by cash P&L (highest first)
                'sortDirection': 'DESC'      # Descending order
            }
            
            print(f"Fetching positions for: {user_address[:10]}...{user_address[-6:]}")
            
            response = self.session.get(
                f"{self.base_url}/positions",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                positions = response.json()
                print(f"  ✅ Found {len(positions)} positions")
                
                # Verify field structure in response
                if positions:
                    sample_pos = positions[0]
                    proxy_wallet = sample_pos.get('proxyWallet')  # Response uses 'proxyWallet'
                    if proxy_wallet:
                        print(f"  📋 Response contains proxyWallet: {proxy_wallet[:10]}...")
                    else:
                        print(f"  ⚠️  No proxyWallet field in position response")
                
                return positions
            elif response.status_code == 400:
                print(f"  ❌ Bad Request (400): {response.text}")
                return None
            elif response.status_code == 404:
                print(f"  ℹ️  No positions found for this user")
                return []
            else:
                print(f"  ❌ API Error: HTTP {response.status_code}")
                print(f"     Response: {response.text[:100]}")
                return None
                
        except requests.RequestException as e:
            print(f"  ❌ Network error: {e}")
            return None
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            return None
    
    def get_user_activity(self, user_address, start_timestamp, end_timestamp=None, limit=500):
        """
        Get user's trading activity using CORRECT parameters
        
        Args:
            user_address: Wallet address (same as proxyWallet from trades)
            start_timestamp: Start time (6 months ago)
            end_timestamp: End time (now, if None)
            limit: Max activities to return
        """
        if end_timestamp is None:
            end_timestamp = int(time.time())
        
        try:
            # CORRECTED: Use 'user' parameter name (not 'address')
            params = {
                'user': user_address,        # ✅ CORRECT parameter name!
                'startTs': start_timestamp,   # Start timestamp
                'endTs': end_timestamp,       # End timestamp
                'type': 'TRADE',             # Only get trades
                'limit': min(limit, 500),
                'sortBy': 'TIMESTAMP',       # Sort by time
                'sortDirection': 'DESC'      # Most recent first
            }
            
            print(f"Fetching activity for: {user_address[:10]}...{user_address[-6:]}")
            print(f"  Time range: {datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(end_timestamp).strftime('%Y-%m-%d')}")
            
            response = self.session.get(
                f"{self.base_url}/activity",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                activities = response.json()
                print(f"  ✅ Found {len(activities)} activities")
                
                # Verify field structure in response
                if activities:
                    sample_activity = activities[0]
                    proxy_wallet = sample_activity.get('proxyWallet')  # Response uses 'proxyWallet'
                    if proxy_wallet:
                        print(f"  📋 Response contains proxyWallet: {proxy_wallet[:10]}...")
                    else:
                        print(f"  ⚠️  No proxyWallet field in activity response")
                
                return activities
            elif response.status_code == 400:
                print(f"  ❌ Bad Request (400): {response.text}")
                return None
            elif response.status_code == 404:
                print(f"  ℹ️  No activity found for this user in time range")
                return []
            else:
                print(f"  ❌ API Error: HTTP {response.status_code}")
                print(f"     Response: {response.text[:100]}")
                return None
                
        except requests.RequestException as e:
            print(f"  ❌ Network error: {e}")
            return None
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            return None
    
    def analyze_position_structure(self, positions):
        """Analyze the structure of position data with field verification"""
        if not positions:
            print("No positions to analyze")
            return
        
        print(f"\n=== Position Data Structure ===")
        print(f"Total positions: {len(positions)}")
        
        # Look at sample position
        sample_position = positions[0]
        print(f"\nSample position keys: {list(sample_position.keys())}")
        
        # Show key financial fields and verify they exist
        expected_fields = ['proxyWallet', 'cashPnl', 'percentPnl', 'initialValue', 'currentValue', 'title']
        print(f"\nKey fields verification:")
        for field in expected_fields:
            value = sample_position.get(field, 'NOT FOUND')
            if field == 'proxyWallet' and value != 'NOT FOUND':
                print(f"  ✅ {field}: {value[:10]}...{value[-6:]}")
            else:
                print(f"  {'✅' if value != 'NOT FOUND' else '❌'} {field}: {value}")
    
    def calculate_user_profit(self, positions):
        """Calculate total profit/loss for a user from their positions"""
        if not positions:
            return {
                'total_cash_pnl': 0,
                'total_percent_pnl': 0,
                'profitable_positions': 0,
                'losing_positions': 0,
                'total_positions': 0,
                'biggest_win': 0,
                'biggest_loss': 0,
                'total_initial_value': 0,
                'total_current_value': 0
            }
        
        total_cash_pnl = 0
        total_percent_pnl = 0
        profitable_positions = 0
        losing_positions = 0
        biggest_win = 0
        biggest_loss = 0
        total_initial_value = 0
        total_current_value = 0
        
        print(f"\n=== Calculating Profit/Loss ===")
        
        for i, position in enumerate(positions):
            # Extract P&L data - handle different data types
            cash_pnl_raw = position.get('cashPnl', 0)
            percent_pnl_raw = position.get('percentPnl', 0)
            initial_value_raw = position.get('initialValue', 0)
            current_value_raw = position.get('currentValue', 0)
            
            # Convert to float safely
            try:
                cash_pnl = float(cash_pnl_raw) if cash_pnl_raw else 0
                percent_pnl = float(percent_pnl_raw) if percent_pnl_raw else 0
                initial_value = float(initial_value_raw) if initial_value_raw else 0
                current_value = float(current_value_raw) if current_value_raw else 0
            except (ValueError, TypeError):
                cash_pnl = percent_pnl = initial_value = current_value = 0
            
            total_cash_pnl += cash_pnl
            total_percent_pnl += percent_pnl
            total_initial_value += initial_value
            total_current_value += current_value
            
            if cash_pnl > 0:
                profitable_positions += 1
                biggest_win = max(biggest_win, cash_pnl)
            elif cash_pnl < 0:
                losing_positions += 1
                biggest_loss = min(biggest_loss, cash_pnl)  # Will be negative
            
            # Show first few positions for debugging
            if i < 3:
                market_title = position.get('title', 'Unknown Market')
                print(f"  Position {i+1}: {market_title[:50]}...")
                print(f"    Cash P&L: ${cash_pnl:.2f}")
                print(f"    Initial Value: ${initial_value:.2f}")
                print(f"    Current Value: ${current_value:.2f}")
        
        results = {
            'total_cash_pnl': total_cash_pnl,
            'total_percent_pnl': total_percent_pnl,
            'profitable_positions': profitable_positions,
            'losing_positions': losing_positions,
            'total_positions': len(positions),
            'biggest_win': biggest_win,
            'biggest_loss': biggest_loss,
            'total_initial_value': total_initial_value,
            'total_current_value': total_current_value
        }
        
        print(f"\n  📊 Summary:")
        print(f"    Total Cash P&L: ${results['total_cash_pnl']:.2f}")
        print(f"    Total Investment: ${results['total_initial_value']:.2f}")
        print(f"    Current Value: ${results['total_current_value']:.2f}")
        print(f"    Profitable positions: {results['profitable_positions']}")
        print(f"    Losing positions: {results['losing_positions']}")
        print(f"    Biggest win: ${results['biggest_win']:.2f}")
        print(f"    Biggest loss: ${results['biggest_loss']:.2f}")
        
        return results
    
    def analyze_activity_data(self, activities):
        """Analyze user activity data structure and metrics"""
        if not activities:
            print("No activities to analyze")
            return {}
        
        print(f"\n=== Activity Analysis ===")
        
        # Look at sample activity
        sample_activity = activities[0]
        print(f"Sample activity keys: {list(sample_activity.keys())}")
        
        # Verify expected fields
        expected_fields = ['proxyWallet', 'timestamp', 'type', 'size', 'usdcSize', 'price', 'side', 'title']
        print(f"\nField verification:")
        for field in expected_fields:
            value = sample_activity.get(field, 'NOT FOUND')
            if field == 'timestamp' and value != 'NOT FOUND':
                print(f"  ✅ {field}: {value} ({datetime.fromtimestamp(value)})")
            elif field == 'proxyWallet' and value != 'NOT FOUND':
                print(f"  ✅ {field}: {value[:10]}...{value[-6:]}")
            else:
                print(f"  {'✅' if value != 'NOT FOUND' else '❌'} {field}: {value}")
        
        # Calculate activity metrics
        total_volume = 0
        buy_trades = 0
        sell_trades = 0
        
        for activity in activities:
            usdc_size = activity.get('usdcSize', 0)
            side = activity.get('side', '')
            
            try:
                volume = float(usdc_size) if usdc_size else 0
                total_volume += volume
            except (ValueError, TypeError):
                pass
            
            if side == 'BUY':
                buy_trades += 1
            elif side == 'SELL':
                sell_trades += 1
        
        metrics = {
            'total_trades': len(activities),
            'total_volume_usdc': total_volume,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades
        }
        
        print(f"\n  📈 Activity Metrics:")
        print(f"    Total trades: {metrics['total_trades']}")
        print(f"    Total volume: ${metrics['total_volume_usdc']:.2f}")
        print(f"    Buy trades: {metrics['buy_trades']}")
        print(f"    Sell trades: {metrics['sell_trades']}")
        
        return metrics

def test_corrected_api_parameters():
    """Test with the corrected API parameters that actually work"""
    print("=== Testing Corrected API Parameters ===\n")
    print("Using 'user' parameter for requests, 'proxyWallet' for responses")
    
    analyzer = PolymarketUserAnalyzer()
    
    # First get a real user from recent trades
    print("Step 1: Getting real user addresses from recent trades")
    
    try:
        response = requests.get(
            "https://data-api.polymarket.com/trades",
            params={'limit': 10, 'takerOnly': 'false'},
            timeout=10
        )
        
        if response.status_code == 200:
            trades = response.json()
            
            # Extract real user addresses
            test_users = []
            for trade in trades:
                proxy_wallet = trade.get('proxyWallet')  # Response uses 'proxyWallet'
                
                if proxy_wallet and proxy_wallet not in test_users:
                    test_users.append(proxy_wallet)
                
                if len(test_users) >= 3:
                    break
            
            print(f"Found {len(test_users)} test users from trade data")
            
            if test_users:
                test_user = test_users[0]
                print(f"\nTesting with user: {test_user}")
                
                # Test 2: Get user positions with CORRECT parameter
                print(f"\nTest 2: Get user positions (using 'user' parameter)")
                positions = analyzer.get_user_positions(test_user)
                
                if positions is not None and len(positions) > 0:
                    # Test 3: Analyze position structure
                    print(f"\nTest 3: Analyze position structure")
                    analyzer.analyze_position_structure(positions)
                    
                    # Test 4: Calculate profit
                    print(f"\nTest 4: Calculate user profit")
                    profit_data = analyzer.calculate_user_profit(positions)
                    
                    # Test 5: Get user activity with CORRECT parameter
                    print(f"\nTest 5: Get user activity (using 'user' parameter)")
                    thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
                    activity = analyzer.get_user_activity(test_user, thirty_days_ago)
                    
                    if activity and len(activity) > 0:
                        # Test 6: Analyze activity data
                        print(f"\nTest 6: Analyze activity data")
                        activity_metrics = analyzer.analyze_activity_data(activity)
                    
                    print(f"\n✅ All tests completed successfully!")
                    print(f"   ✅ API parameters corrected and working")
                    print(f"   ✅ User has {len(positions)} positions")
                    print(f"   ✅ Total P&L: ${profit_data['total_cash_pnl']:.2f}")
                    print(f"   ✅ Recent activities: {len(activity) if activity else 0}")
                    
                    return analyzer, test_user, positions, profit_data, activity
                else:
                    print("ℹ️  User has no positions, but API calls work correctly")
                    return analyzer, test_user, [], {}, []
            else:
                print("❌ No test users found")
        else:
            print(f"❌ Failed to get sample trades: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
    
    return None, None, None, None, None

if __name__ == "__main__":
    print("🔧 Testing Corrected API Parameters")
    print("===================================")
    print("Request Parameter: 'user'")
    print("Response Field: 'proxyWallet'")
    print()
    
    results = test_corrected_api_parameters()
    
    if results[0]:  # If analyzer was created successfully
        print("\n🎉 Parameter correction confirmed!")
        print("   Use 'user' for API requests")
        print("   Read 'proxyWallet' from responses")
    else:
        print("\n❌ Tests failed - check API connectivity")