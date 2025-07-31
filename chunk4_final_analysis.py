import requests
import time
from datetime import datetime, timedelta
import json
from collections import defaultdict

class PolymarketCompleteAnalyzer:
    """Complete analyzer with corrected field names throughout"""
    
    def __init__(self):
        self.base_url = "https://data-api.polymarket.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PolymarketAnalyzer/1.0'
        })
        
        # Calculate 6 months ago
        self.six_months_ago = int((datetime.now() - timedelta(days=180)).timestamp())
        print(f"Analyzing users active since: {datetime.fromtimestamp(self.six_months_ago)}")
        
        # Storage for results
        self.active_users = set()
        self.user_trade_counts = defaultdict(int)
        self.user_names = {}  # Store display names
        self.profitable_users = []
    
    def scan_for_active_users(self, max_trades_to_scan=5000):
        """
        Scan recent trades to find users active in last 6 months
        Uses CORRECT field name: proxyWallet
        
        Args:
            max_trades_to_scan: Maximum number of trades to scan
        """
        print(f"\n=== Scanning for Active Users ===")
        print(f"Will scan up to {max_trades_to_scan} recent trades")
        
        offset = 0
        limit = 500  # Max per request
        trades_scanned = 0
        
        while trades_scanned < max_trades_to_scan:
            print(f"\nFetching trades {offset} to {offset + limit}...")
            
            try:
                response = self.session.get(
                    f"{self.base_url}/trades",
                    params={
                        'limit': limit,
                        'offset': offset,
                        'takerOnly': 'false'  # Get all trades
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ API Error: HTTP {response.status_code}")
                    break
                
                trades = response.json()
                
                if not trades:
                    print("No more trades found")
                    break
                
                # Process this batch using CORRECT field name
                recent_trades_in_batch = 0
                
                for trade in trades:
                    trade_timestamp = trade.get('timestamp', 0)
                    
                    # Stop if trades are too old
                    if trade_timestamp < self.six_months_ago:
                        print(f"Reached trades older than 6 months. Stopping scan.")
                        return len(self.active_users)
                    
                    # Extract user address using CORRECT field name
                    proxy_wallet = trade.get('proxyWallet')  # ✅ Correct field!
                    user_name = trade.get('name', '')
                    pseudonym = trade.get('pseudonym', '')
                    
                    if proxy_wallet:
                        self.active_users.add(proxy_wallet)
                        self.user_trade_counts[proxy_wallet] += 1
                        
                        # Store display name for reference
                        if proxy_wallet not in self.user_names:
                            display_name = user_name or pseudonym or 'Anonymous'
                            self.user_names[proxy_wallet] = display_name
                    
                    recent_trades_in_batch += 1
                    trades_scanned += 1
                
                print(f"  Processed {recent_trades_in_batch} recent trades")
                print(f"  Total unique users found: {len(self.active_users)}")
                print(f"  Total trades scanned: {trades_scanned}")
                
                # Move to next batch
                offset += limit
                
                # Small delay to be respectful
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error scanning trades: {e}")
                break
        
        print(f"\n✅ Scan complete. Found {len(self.active_users)} active users")
        return len(self.active_users)
    
    def analyze_user_profit(self, user_address):
        """Analyze profit for a single user using correct API parameters"""
        try:
            # Get user positions using correct parameter name
            response = self.session.get(
                f"{self.base_url}/positions",
                params={
                    'user': user_address,       # ✅ CORRECTED: Use 'user' not 'address'
                    'sortBy': 'CASHPNL',       # ✅ Correct enum value
                    'sortDirection': 'DESC',   # ✅ Correct parameter name
                    'limit': 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                positions = response.json()
                
                # Calculate total profit using correct field names
                total_profit = 0
                for position in positions:
                    cash_pnl = position.get('cashPnl', 0)  # ✅ Correct field name
                    if isinstance(cash_pnl, (str, int, float)):
                        try:
                            total_profit += float(cash_pnl) if cash_pnl else 0
                        except (ValueError, TypeError):
                            pass
                
                return total_profit
            else:
                return 0
                
        except Exception as e:
            print(f"  Error analyzing {user_address[:10]}...: {e}")
            return 0
    
    def find_profitable_users(self, profit_threshold=3000, max_users_to_check=None):
        """
        Find users with profit above threshold
        
        Args:
            profit_threshold: Minimum profit in USD
            max_users_to_check: Limit how many users to check (for testing)
        """
        print(f"\n=== Finding Users with Profit > ${profit_threshold} ===")
        
        # Sort users by trade count (most active first)
        sorted_users = sorted(
            self.user_trade_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        users_to_check = sorted_users
        if max_users_to_check:
            users_to_check = sorted_users[:max_users_to_check]
            print(f"Limiting analysis to top {max_users_to_check} most active users")
        
        print(f"Checking {len(users_to_check)} users...")
        
        self.profitable_users = []
        
        for i, (user_address, trade_count) in enumerate(users_to_check):
            if (i + 1) % 10 == 0:
                print(f"  Checked {i + 1}/{len(users_to_check)} users...")
            
            profit = self.analyze_user_profit(user_address)
            
            if profit > profit_threshold:
                user_data = {
                    'address': user_address,
                    'profit': profit,
                    'trade_count': trade_count,
                    'display_name': self.user_names.get(user_address, 'Anonymous')
                }
                self.profitable_users.append(user_data)
                
                display_name = user_data['display_name']
                print(f"  💰 Found: {user_address[:10]}... ({display_name}) - ${profit:.2f} profit, {trade_count} trades")
            
            # Small delay
            time.sleep(0.05)
        
        return len(self.profitable_users)
    
    def generate_detailed_report(self):
        """Generate comprehensive analysis report"""
        print(f"\n" + "="*60)
        print(f"           POLYMARKET PROFITABLE USERS ANALYSIS")
        print(f"="*60)
        print(f"Analysis Period: Last 6 months (since {datetime.fromtimestamp(self.six_months_ago).strftime('%Y-%m-%d')})")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{"="*60}")
        
        # Summary statistics
        total_active = len(self.active_users)
        total_profitable = len(self.profitable_users)
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   • Total active users (6 months): {total_active:,}")
        print(f"   • Users with profit > $3,000: {total_profitable:,}")
        print(f"   • Percentage profitable: {(total_profitable/total_active*100):.2f}%" if total_active > 0 else "   • Percentage profitable: 0%")
        
        if self.profitable_users:
            total_profits = sum(user['profit'] for user in self.profitable_users)
            avg_profit = total_profits / len(self.profitable_users)
            max_profit = max(user['profit'] for user in self.profitable_users)
            min_profit = min(user['profit'] for user in self.profitable_users)
            
            print(f"   • Total profits (top users): ${total_profits:,.2f}")
            print(f"   • Average profit (top users): ${avg_profit:,.2f}")
            print(f"   • Highest individual profit: ${max_profit:,.2f}")
            print(f"   • Lowest qualifying profit: ${min_profit:,.2f}")
        
        # Top performers
        if self.profitable_users:
            print(f"\n🏆 TOP 10 MOST PROFITABLE USERS:")
            sorted_profitable = sorted(self.profitable_users, key=lambda x: x['profit'], reverse=True)
            
            for i, user in enumerate(sorted_profitable[:10]):
                rank = i + 1
                address = user['address']
                profit = user['profit']
                trades = user['trade_count']
                name = user['display_name']
                
                print(f"   {rank:2d}. {address[:10]}...{address[-6:]} ({name})")
                print(f"       Profit: ${profit:,.2f} | Trades: {trades} | Avg per trade: ${profit/trades:.2f}")
        
        # Activity analysis
        if self.user_trade_counts:
            print(f"\n📈 TRADING ACTIVITY ANALYSIS:")
            trade_counts = list(self.user_trade_counts.values())
            avg_trades = sum(trade_counts) / len(trade_counts)
            max_trades = max(trade_counts)
            
            print(f"   • Average trades per user: {avg_trades:.1f}")
            print(f"   • Most active user trades: {max_trades}")
            
            # Trade count distribution
            high_activity = sum(1 for count in trade_counts if count >= 10)
            medium_activity = sum(1 for count in trade_counts if 3 <= count < 10)
            low_activity = sum(1 for count in trade_counts if count < 3)
            
            print(f"   • High activity users (10+ trades): {high_activity}")
            print(f"   • Medium activity users (3-9 trades): {medium_activity}")
            print(f"   • Low activity users (1-2 trades): {low_activity}")
        
        print(f"\n" + "="*60)
        print(f"Analysis completed successfully!")
        print(f"Data source: Polymarket Data API")
        print(f"{"="*60}")
        
        return {
            'total_active_users': total_active,
            'profitable_users_count': total_profitable,
            'profitable_users_details': self.profitable_users,
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_period_start': datetime.fromtimestamp(self.six_months_ago).isoformat()
        }
    
    def run_complete_analysis(self, max_trades_scan=5000, max_users_check=None, profit_threshold=3000):
        """
        Run the complete analysis pipeline
        
        Args:
            max_trades_scan: Max trades to scan for active users
            max_users_check: Max users to check for profitability (None = all)
            profit_threshold: Minimum profit threshold in USD
        """
        print("=== POLYMARKET PROFITABLE USERS ANALYSIS ===")
        print(f"Target: Users with profit > ${profit_threshold} in last 6 months\n")
        
        # Step 1: Scan for active users
        print("STEP 1: Scanning for active users...")
        active_count = self.scan_for_active_users(max_trades_scan)
        
        if active_count == 0:
            print("❌ No active users found. Cannot proceed.")
            return None
        
        # Step 2: Analyze profits
        print(f"\nSTEP 2: Analyzing profits for {active_count} users...")
        profitable_count = self.find_profitable_users(profit_threshold, max_users_check)
        
        # Step 3: Generate report
        print(f"\nSTEP 3: Generating final report...")
        results = self.generate_detailed_report()
        
        return results

def test_final_analysis():
    """Test the complete analysis with a small sample"""
    print("=== Testing Complete Analysis (Sample Run) ===\n")
    
    analyzer = PolymarketCompleteAnalyzer()
    
    # Run with small limits for testing
    results = analyzer.run_complete_analysis(
        max_trades_scan=1000,    # Scan 1000 recent trades
        max_users_check=20,      # Check top 20 most active users
        profit_threshold=1000    # Lower threshold for testing ($1000)
    )
    
    if results:
        print(f"\n✅ Test completed successfully!")
        print(f"   Found {results['total_active_users']} active users")
        print(f"   Found {results['profitable_users_count']} profitable users")
        
        # Save results
        filename = f"polymarket_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"   Results saved to: {filename}")
        
        return results
    else:
        print("❌ Test failed")
        return None

def run_full_analysis():
    """Run the full analysis for production use"""
    print("=== FULL PRODUCTION ANALYSIS ===\n")
    print("This will scan many trades and check all users for profitability.")
    print("This may take several minutes to complete.")
    
    confirmation = input("\nProceed with full analysis? (y/N): ")
    if confirmation.lower() != 'y':
        print("Analysis cancelled.")
        return None
    
    analyzer = PolymarketCompleteAnalyzer()
    
    # Full production run
    results = analyzer.run_complete_analysis(
        max_trades_scan=10000,   # Scan 10,000 recent trades
        max_users_check=None,    # Check ALL active users
        profit_threshold=3000    # $3,000 profit threshold
    )
    
    if results:
        # Save comprehensive results
        filename = f"polymarket_full_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Full results saved to: {filename}")
        
        # Also save a summary CSV for easy viewing
        if results['profitable_users_details']:
            import csv
            csv_filename = f"profitable_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ['rank', 'address', 'display_name', 'profit', 'trade_count', 'profit_per_trade']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                sorted_users = sorted(results['profitable_users_details'], 
                                    key=lambda x: x['profit'], reverse=True)
                
                for i, user in enumerate(sorted_users, 1):
                    writer.writerow({
                        'rank': i,
                        'address': user['address'],
                        'display_name': user['display_name'],
                        'profit': f"${user['profit']:.2f}",
                        'trade_count': user['trade_count'],
                        'profit_per_trade': f"${user['profit']/user['trade_count']:.2f}"
                    })
            
            print(f"📊 Summary CSV saved to: {csv_filename}")
        
        return results
    else:
        print("❌ Full analysis failed")
        return None

if __name__ == "__main__":
    print("Polymarket Profitable Users Analyzer")
    print("=====================================")
    print()
    print("Choose analysis type:")
    print("1. Test run (small sample, quick)")
    print("2. Full analysis (comprehensive, slower)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        test_final_analysis()
    elif choice == "2":
        run_full_analysis()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice. Running test analysis...")
        test_final_analysis()