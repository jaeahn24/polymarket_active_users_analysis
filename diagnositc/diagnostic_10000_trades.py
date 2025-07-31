import requests
import time
from datetime import datetime, timedelta
from collections import defaultdict

class PolymarketDiagnostic:
    """Diagnostic version to understand why scanning stops"""
    
    def __init__(self):
        self.base_url = "https://data-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PolymarketAnalyzer/1.0'
        })
        
        # Calculate 6 months ago
        self.six_months_ago = int((datetime.now() - timedelta(days=180)).timestamp())
        print(f"6 months cutoff: {datetime.fromtimestamp(self.six_months_ago)}")
        
        # Tracking variables
        self.total_trades_fetched = 0
        self.recent_trades_count = 0
        self.old_trades_count = 0
        self.active_users = set()
        
    def scan_with_detailed_logging(self, max_trades_to_scan=50000):
        """
        Scan with detailed logging to understand what's happening
        """
        print(f"\n=== Diagnostic Scan ===")
        print(f"Max trades to scan: {max_trades_to_scan}")
        print(f"6 months cutoff: {datetime.fromtimestamp(self.six_months_ago)}")
        
        offset = 0
        limit = 500
        consecutive_old_batches = 0
        
        while self.total_trades_fetched < max_trades_to_scan:
            print(f"\n--- Batch {(offset//500)+1} ---")
            print(f"Fetching trades {offset} to {offset + limit}...")
            
            try:
                response = self.session.get(
                    f"{self.base_url}/trades",
                    params={
                        'limit': limit,
                        'offset': offset,
                        'takerOnly': 'false'
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ API Error: HTTP {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    break
                
                trades = response.json()
                
                if not trades:
                    print("❌ No more trades returned by API")
                    print(f"   This suggests we've reached the end of available data")
                    break
                
                print(f"✅ Received {len(trades)} trades")
                self.total_trades_fetched += len(trades)
                
                # Analyze this batch
                batch_recent = 0
                batch_old = 0
                oldest_in_batch = None
                newest_in_batch = None
                
                for trade in trades:
                    trade_timestamp = trade.get('timestamp', 0)
                    
                    if oldest_in_batch is None or trade_timestamp < oldest_in_batch:
                        oldest_in_batch = trade_timestamp
                    if newest_in_batch is None or trade_timestamp > newest_in_batch:
                        newest_in_batch = trade_timestamp
                    
                    if trade_timestamp >= self.six_months_ago:
                        batch_recent += 1
                        self.recent_trades_count += 1
                        
                        # Count unique users
                        proxy_wallet = trade.get('proxyWallet')
                        if proxy_wallet:
                            self.active_users.add(proxy_wallet)
                    else:
                        batch_old += 1
                        self.old_trades_count += 1
                
                # Log batch analysis
                print(f"   Recent trades in batch: {batch_recent}")
                print(f"   Old trades in batch: {batch_old}")
                print(f"   Batch date range:")
                print(f"     Newest: {datetime.fromtimestamp(newest_in_batch) if newest_in_batch else 'None'}")
                print(f"     Oldest: {datetime.fromtimestamp(oldest_in_batch) if oldest_in_batch else 'None'}")
                
                # Check if this batch is all old trades
                if batch_recent == 0:
                    consecutive_old_batches += 1
                    print(f"   ⚠️  All trades in this batch are older than 6 months")
                    print(f"   📊 Consecutive old batches: {consecutive_old_batches}")
                    
                    if consecutive_old_batches >= 3:
                        print(f"   🛑 Stopping: Found 3 consecutive batches with only old trades")
                        break
                else:
                    consecutive_old_batches = 0
                
                # Overall progress
                print(f"   📈 Total progress:")
                print(f"     Total trades fetched: {self.total_trades_fetched:,}")
                print(f"     Recent trades found: {self.recent_trades_count:,}")
                print(f"     Old trades found: {self.old_trades_count:,}")
                print(f"     Unique active users: {len(self.active_users):,}")
                
                # Check if we should stop due to time cutoff
                if batch_old > batch_recent and oldest_in_batch < self.six_months_ago:
                    print(f"   🕐 Most trades in this batch are old. Consider stopping soon.")
                
                # Move to next batch
                offset += limit
                
                # API rate limiting delay
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        # Final summary
        print(f"\n" + "="*50)
        print(f"DIAGNOSTIC SUMMARY")
        print(f"="*50)
        print(f"Total trades fetched: {self.total_trades_fetched:,}")
        print(f"Recent trades (6mo): {self.recent_trades_count:,}")
        print(f"Old trades: {self.old_trades_count:,}")
        print(f"Unique active users: {len(self.active_users):,}")
        print(f"API requests made: {(offset//500):,}")
        
        # Analyze why scanning stopped
        print(f"\nWHY SCANNING STOPPED:")
        if self.total_trades_fetched >= max_trades_to_scan:
            print(f"✅ Reached max_trades_to_scan limit ({max_trades_to_scan:,})")
        elif consecutive_old_batches >= 3:
            print(f"⏰ Found too many old trades (beyond 6 month cutoff)")
        elif not trades:
            print(f"📭 API returned no more trades (end of data)")
        else:
            print(f"❓ Unknown reason")
        
        return {
            'total_fetched': self.total_trades_fetched,
            'recent_trades': self.recent_trades_count,
            'active_users': len(self.active_users),
            'stop_reason': 'diagnostic_complete'
        }

    def quick_sample_analysis(self):
        """Quick analysis of first few batches to understand data distribution"""
        print(f"\n=== Quick Sample Analysis ===")
        
        for batch_num in range(1, 6):  # Check first 5 batches
            offset = (batch_num - 1) * 500
            
            try:
                response = self.session.get(
                    f"{self.base_url}/trades",
                    params={'limit': 500, 'offset': offset, 'takerOnly': 'false'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    trades = response.json()
                    if trades:
                        oldest = min(trade.get('timestamp', 0) for trade in trades)
                        newest = max(trade.get('timestamp', 0) for trade in trades)
                        
                        print(f"Batch {batch_num}: {len(trades)} trades")
                        print(f"  Range: {datetime.fromtimestamp(newest)} to {datetime.fromtimestamp(oldest)}")
                        print(f"  Days ago: {(time.time() - oldest)/(24*3600):.1f} days")
                    else:
                        print(f"Batch {batch_num}: No trades")
                        break
                else:
                    print(f"Batch {batch_num}: API Error {response.status_code}")
                    
            except Exception as e:
                print(f"Batch {batch_num}: Error - {e}")
            
            time.sleep(0.1)

def run_diagnostic():
    """Run diagnostic to understand trade scanning behavior"""
    print("🔍 POLYMARKET DIAGNOSTIC ANALYSIS")
    print("="*40)
    
    diagnostic = PolymarketDiagnostic()
    
    print("\n1. Quick sample analysis...")
    diagnostic.quick_sample_analysis()
    
    print("\n2. Detailed scanning analysis...")
    choice = input("Run detailed scan? This may take a while (y/N): ")
    
    if choice.lower() == 'y':
        max_limit = input("Max trades to scan (default 15000): ")
        try:
            max_limit = int(max_limit) if max_limit else 15000
        except ValueError:
            max_limit = 15000
        
        results = diagnostic.scan_with_detailed_logging(max_limit)
        
        print(f"\n💾 Diagnostic complete!")
        print(f"Found {results['active_users']} unique active users")
        print(f"Processed {results['recent_trades']} recent trades")
    else:
        print("Diagnostic cancelled.")

if __name__ == "__main__":
    run_diagnostic()