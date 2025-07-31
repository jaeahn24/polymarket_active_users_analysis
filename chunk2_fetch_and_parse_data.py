import requests
import time
from datetime import datetime, timedelta
import json
from collections import defaultdict

class PolymarketRateLimitedScanner:
    """Trade scanner with proper rate limiting and 429 error handling"""
    
    def __init__(self):
        self.base_url = "https://data-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PolymarketAnalyzer/1.0'
        })
        
        # Rate limiting settings
        self.base_delay = 0.5  # Start with 500ms between requests
        self.current_delay = self.base_delay
        self.max_delay = 10.0  # Max 10 seconds
        self.backoff_multiplier = 2.0
        self.success_delay_reduction = 0.9  # Reduce delay by 10% on success
        
        # Calculate 6 months ago timestamp
        self.six_months_ago = int((datetime.now() - timedelta(days=180)).timestamp())
        print(f"Scanning for users active since: {datetime.fromtimestamp(self.six_months_ago)}")
        print(f"Starting with {self.base_delay}s delay between requests")
    
    def make_request_with_backoff(self, url, params, max_retries=5):
        """
        Make API request with exponential backoff for rate limiting
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    # Success - gradually reduce delay
                    self.current_delay = max(
                        self.base_delay, 
                        self.current_delay * self.success_delay_reduction
                    )
                    return response
                
                elif response.status_code == 429:
                    # Rate limited - increase delay
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = int(retry_after)
                        print(f"   🕐 Rate limited. Retry-After: {wait_time}s")
                    else:
                        wait_time = self.current_delay * self.backoff_multiplier
                        self.current_delay = min(self.max_delay, wait_time)
                        print(f"   🕐 Rate limited. Backing off to {self.current_delay:.1f}s delay")
                    
                    if attempt < max_retries - 1:
                        print(f"   ⏳ Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   ❌ Max retries reached for rate limiting")
                        return None
                
                else:
                    print(f"   ❌ API Error: HTTP {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"   🔄 Retrying in {self.current_delay:.1f}s...")
                        time.sleep(self.current_delay)
                        continue
                    else:
                        return None
                        
            except Exception as e:
                print(f"   ❌ Request error: {e}")
                if attempt < max_retries - 1:
                    print(f"   🔄 Retrying in {self.current_delay:.1f}s...")
                    time.sleep(self.current_delay)
                    continue
                else:
                    return None
        
        return None
    
    def scan_all_recent_trades_with_rate_limiting(self):
        """
        Scan ALL trades with proper rate limiting
        """
        print(f"\n=== Rate-Limited Trade Scanning ===")
        print(f"Will handle rate limits gracefully with exponential backoff")
        
        # Storage
        active_users = set()
        user_trade_counts = defaultdict(int)
        user_names = {}
        
        # Progress tracking
        offset = 0
        limit = 500
        total_api_calls = 0
        successful_calls = 0
        failed_calls = 0
        total_trades_processed = 0
        recent_trades_found = 0
        consecutive_old_trades = 0
        rate_limit_hits = 0
        
        start_time = time.time()
        
        while True:
            total_api_calls += 1
            
            # Progress updates every 10 successful calls
            if successful_calls % 10 == 0 and successful_calls > 0:
                elapsed = time.time() - start_time
                rate = successful_calls / elapsed if elapsed > 0 else 0
                
                print(f"\n📊 Progress Update:")
                print(f"   Time elapsed: {elapsed/60:.1f} minutes")
                print(f"   Successful API calls: {successful_calls:,}")
                print(f"   Failed calls: {failed_calls}")
                print(f"   Rate limit hits: {rate_limit_hits}")
                print(f"   Current delay: {self.current_delay:.2f}s")
                print(f"   Success rate: {rate:.1f} calls/sec")
                print(f"   Trades processed: {total_trades_processed:,}")
                print(f"   Unique users: {len(active_users):,}")
            
            # Make the API request
            response = self.make_request_with_backoff(
                f"{self.base_url}/trades",
                {
                    'limit': limit,
                    'offset': offset,
                    'takerOnly': 'false'
                }
            )
            
            if response is None:
                failed_calls += 1
                print(f"❌ Failed to get response after retries")
                
                # If we get too many failures, stop
                if failed_calls >= 5:
                    print(f"❌ Too many failures ({failed_calls}). Stopping scan.")
                    break
                    
                # Skip this batch and continue
                offset += limit
                continue
            
            # Track rate limiting
            if response.status_code == 429:
                rate_limit_hits += 1
            
            successful_calls += 1
            
            try:
                trades = response.json()
                
                if not trades:
                    print(f"📭 No more trades available")
                    break
                
                # Process trades
                batch_recent = 0
                batch_old = 0
                
                for trade in trades:
                    total_trades_processed += 1
                    trade_timestamp = trade.get('timestamp', 0)
                    
                    if trade_timestamp >= self.six_months_ago:
                        batch_recent += 1
                        recent_trades_found += 1
                        consecutive_old_trades = 0
                        
                        proxy_wallet = trade.get('proxyWallet')
                        if proxy_wallet:
                            active_users.add(proxy_wallet)
                            user_trade_counts[proxy_wallet] += 1
                            
                            if proxy_wallet not in user_names:
                                name = trade.get('name', '') or trade.get('pseudonym', '') or 'Anonymous'
                                user_names[proxy_wallet] = name
                    else:
                        batch_old += 1
                        consecutive_old_trades += 1
                
                # Stop if too many old trades
                if consecutive_old_trades >= 2500:
                    print(f"🛑 Stopping: Found {consecutive_old_trades} consecutive old trades")
                    break
                
                # Move to next batch
                offset += limit
                
                # Rate limiting delay (always wait between requests)
                time.sleep(self.current_delay)
                
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
                failed_calls += 1
                continue
            except Exception as e:
                print(f"❌ Error processing response: {e}")
                failed_calls += 1
                continue
        
        # Final results
        total_time = time.time() - start_time
        
        print(f"\n" + "="*50)
        print(f"RATE-LIMITED SCAN COMPLETE")
        print(f"="*50)
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Successful API calls: {successful_calls:,}")
        print(f"Failed calls: {failed_calls}")
        print(f"Rate limit hits: {rate_limit_hits}")
        print(f"Average delay used: {self.current_delay:.2f}s")
        print(f"Trades processed: {total_trades_processed:,}")
        print(f"Recent trades: {recent_trades_found:,}")
        print(f"✅ UNIQUE ACTIVE USERS: {len(active_users):,}")
        print(f"="*50)
        
        return active_users, user_trade_counts, user_names

def test_rate_limited_scanning():
    """Test the rate-limited scanning approach"""
    print("=== Testing Rate-Limited Trade Scanning ===")
    print("This version handles HTTP 429 errors gracefully")
    
    scanner = PolymarketRateLimitedScanner()
    
    print(f"\nRate limiting strategy:")
    print(f"• Start with {scanner.base_delay}s delay between requests")
    print(f"• Exponential backoff on 429 errors")
    print(f"• Gradual reduction on successful requests")
    print(f"• Max delay: {scanner.max_delay}s")
    
    print("\nThis will take longer but avoid rate limiting issues.")
    print("Expected time: 30-60 minutes")
    
    confirm = input("\nProceed with rate-limited scan? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return None, None, None
    
    # Run rate-limited scan
    users, counts, names = scanner.scan_all_recent_trades_with_rate_limiting()
    
    if users:
        print(f"\n🏆 TOP 10 MOST ACTIVE USERS:")
        sorted_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        for i, (address, count) in enumerate(sorted_users[:10], 1):
            name = names.get(address, 'Anonymous')
            print(f"   {i:2d}. {address[:10]}...{address[-6:]} ({name}) - {count} trades")
    
    return users, counts, names

# Quick test function for finding optimal delay
def test_rate_limits():
    """Quick test to find optimal rate limiting"""
    print("=== Testing Rate Limits ===")
    
    delays = [0.2, 0.5, 1.0, 2.0]  # Test different delays
    
    for delay in delays:
        print(f"\nTesting {delay}s delay...")
        
        session = requests.Session()
        session.headers.update({'User-Agent': 'PolymarketAnalyzer/1.0'})
        
        success_count = 0
        rate_limit_count = 0
        
        for i in range(10):  # Test 10 requests
            try:
                response = session.get(
                    "https://data-api.polymarket.com/trades",
                    params={'limit': 10, 'offset': i * 10},
                    timeout=10
                )
                
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limit_count += 1
                    print(f"   Rate limited on request {i+1}")
                
                time.sleep(delay)
                
            except Exception as e:
                print(f"   Error on request {i+1}: {e}")
        
        print(f"   Results: {success_count}/10 successful, {rate_limit_count} rate limited")
        
        if rate_limit_count == 0:
            print(f"   ✅ {delay}s delay works!")
            break
        else:
            print(f"   ❌ {delay}s delay still hits rate limits")

if __name__ == "__main__":
    print("Choose option:")
    print("1. Test rate limits to find optimal delay")
    print("2. Run full rate-limited scan")
    
    choice = input("Enter choice (1-2): ")
    
    if choice == "1":
        test_rate_limits()
    elif choice == "2":
        active_users, trade_counts, user_names = test_rate_limited_scanning()
    else:
        print("Invalid choice")