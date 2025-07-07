import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import requests
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import time
import asyncio
import websockets

app = typer.Typer()
console = Console()

# Correct PumpPortal API endpoints
PUMPPORTAL_API_BASE = "https://api.pumpportal.fun/v1"
PUMPPORTAL_TRENDING_API = f"{PUMPPORTAL_API_BASE}/tokens/trending"
PUMPPORTAL_NEW_API = f"{PUMPPORTAL_API_BASE}/tokens/new"
PUMPPORTAL_TOKEN_API = f"{PUMPPORTAL_API_BASE}/token"
PUMPPORTAL_TRADES_API = f"{PUMPPORTAL_API_BASE}/trades"

class PumpPortalScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get_new_tokens(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch new tokens from PumpPortal."""
        try:
            url = f"{PUMPPORTAL_NEW_API}?limit={limit}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get('tokens', [])
        except Exception as e:
            console.print(f"[red]Error fetching new tokens: {e}[/red]")
            return []
    
    def get_trending_tokens(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch trending tokens from PumpPortal."""
        try:
            url = f"{PUMPPORTAL_TRENDING_API}?limit={limit}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get('tokens', [])
        except Exception as e:
            console.print(f"[red]Error fetching trending tokens: {e}[/red]")
            return []
    
    def get_token_by_address(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """Get token details by mint address."""
        try:
            url = f"{PUMPPORTAL_TOKEN_API}/{mint_address}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json().get('token', {})
        except Exception as e:
            console.print(f"[red]Error fetching token {mint_address}: {e}[/red]")
            return None
    
    def search_tokens(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search tokens by name or symbol."""
        try:
            url = f"{PUMPPORTAL_TRENDING_API}?q={query}&limit={limit}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get('tokens', [])
        except Exception as e:
            console.print(f"[red]Error searching tokens: {e}[/red]")
            return []
    
    def get_token_trades(self, mint_address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trades for a token."""
        try:
            url = f"{PUMPPORTAL_TRADES_API}/{mint_address}?limit={limit}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get('trades', [])
        except Exception as e:
            console.print(f"[red]Error fetching trades for {mint_address}: {e}[/red]")
            return []

def format_number(num: float) -> str:
    """Format large numbers with appropriate suffixes."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K"
    else:
        return f"{num:.4f}"

def format_market_cap(market_cap: float) -> str:
    """Format market cap with color coding."""
    formatted = format_number(market_cap)
    if market_cap >= 1_000_000:
        return f"[green]{formatted}[/green]"
    elif market_cap >= 100_000:
        return f"[yellow]{formatted}[/yellow]"
    else:
        return f"[red]{formatted}[/red]"

def format_timestamp(timestamp: int) -> str:
    """Format Unix timestamp to readable date."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%m/%d %H:%M")
    except:
        return "N/A"

def display_token_table(tokens: List[Dict[str, Any]], title: str = "Tokens"):
    """Display tokens in a formatted table."""
    if not tokens:
        console.print("[yellow]No tokens found.[/yellow]")
        return
    
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True, min_width=15)
    table.add_column("Symbol", style="green", no_wrap=True, min_width=8)
    table.add_column("Market Cap", justify="right", min_width=12)
    table.add_column("Price (SOL)", justify="right", min_width=12)
    table.add_column("24h Volume", justify="right", min_width=12)
    table.add_column("Mint Address", style="dim", no_wrap=True, min_width=20)
    table.add_column("Created", style="dim", min_width=10)
    
    for token in tokens:
        name = token.get('name', 'N/A')[:15]
        symbol = token.get('symbol', 'N/A')[:8]
        market_cap = token.get('market_cap', 0)
        price = token.get('price', 0)
        volume_24h = token.get('volume_24h', 0)
        mint = token.get('mint', 'N/A')
        created_timestamp = token.get('created_timestamp', 0)
        
        table.add_row(
            name,
            symbol,
            format_market_cap(market_cap),
            f"{price:.8f}" if price > 0 else "0",
            format_number(volume_24h) if volume_24h > 0 else "0",
            mint[:20] + "..." if len(mint) > 20 else mint,
            format_timestamp(created_timestamp)
        )
    
    console.print(table)

def display_token_details(token: Dict[str, Any]):
    """Display detailed information about a single token."""
    name = token.get('name', 'N/A')
    symbol = token.get('symbol', 'N/A')
    description = token.get('description', 'No description available')
    mint = token.get('mint', 'N/A')
    creator = token.get('creator', 'N/A')
    market_cap = token.get('market_cap', 0)
    price = token.get('price', 0)
    volume_24h = token.get('volume_24h', 0)
    supply = token.get('supply', 0)
    website = token.get('website', 'N/A')
    twitter = token.get('twitter', 'N/A')
    telegram = token.get('telegram', 'N/A')
    created_timestamp = token.get('created_timestamp', 0)
    
    # Create token info panel
    info_text = f"""
[bold cyan]Name:[/bold cyan] {name}
[bold cyan]Symbol:[/bold cyan] {symbol}
[bold cyan]Description:[/bold cyan] {description[:200]}...

[bold green]Financial Data:[/bold green]
├─ Market Cap: {format_market_cap(market_cap)}
├─ Price: {price:.8f} SOL
├─ 24h Volume: {format_number(volume_24h)}
└─ Supply: {format_number(supply)}

[bold yellow]Contract Info:[/bold yellow]
├─ Mint Address: {mint}
├─ Creator: {creator}
└─ Created: {format_timestamp(created_timestamp)}

[bold magenta]Social Links:[/bold magenta]
├─ Website: {website}
├─ Twitter: {twitter}
└─ Telegram: {telegram}
"""
    
    panel = Panel(info_text, title=f"Token Details: {symbol}", border_style="blue")
    console.print(panel)

@app.command()
def scan(limit: int = 20, trending: bool = False):
    """Scan for new or trending tokens on Pump.fun."""
    if trending:
        console.print(f"[bold blue]:mag: Scanning for {limit} trending tokens on Pump.fun...[/bold blue]")
    else:
        console.print(f"[bold blue]:mag: Scanning for {limit} newest tokens on Pump.fun...[/bold blue]")
    
    scanner = PumpPortalScanner()
    tokens = scanner.get_trending_tokens(limit) if trending else scanner.get_new_tokens(limit)
    
    if tokens:
        display_token_table(tokens, f"{'Trending' if trending else 'Latest'} {len(tokens)} Tokens")
        console.print(f"\n[green]Successfully fetched {len(tokens)} tokens![/green]")
    else:
        console.print("[red]No tokens found or API error.[/red]")

@app.command()
def token(mint_address: str):
    """Get detailed information about a specific token by mint address."""
    console.print(f"[bold blue]:mag: Fetching token details for: {mint_address}[/bold blue]")
    
    scanner = PumpPortalScanner()
    token_data = scanner.get_token_by_address(mint_address)
    
    if token_data:
        display_token_details(token_data)
    else:
        console.print(f"[red]Token not found or API error for address: {mint_address}[/red]")

@app.command()
def search(query: str, limit: int = 10):
    """Search for tokens by name or symbol."""
    console.print(f"[bold blue]:mag: Searching for tokens matching: '{query}'[/bold blue]")
    
    scanner = PumpPortalScanner()
    tokens = scanner.search_tokens(query, limit)
    
    if tokens:
        display_token_table(tokens, f"Search Results for '{query}'")
    else:
        console.print(f"[red]No tokens found matching '{query}'[/red]")

@app.command()
def trades(mint_address: str, limit: int = 20):
    """Get recent trades for a specific token."""
    console.print(f"[bold blue]:chart_with_upwards_trend: Fetching {limit} recent trades for: {mint_address}[/bold blue]")
    
    scanner = PumpPortalScanner()
    trades_data = scanner.get_token_trades(mint_address, limit)
    
    if trades_data:
        table = Table(title=f"Recent Trades for {mint_address[:20]}...", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Amount (SOL)", justify="right")
        table.add_column("Tokens", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Trader", style="dim", no_wrap=True)
        table.add_column("Time", style="dim")
        
        for trade in trades_data:
            trade_type = "🟢 BUY" if trade.get('is_buy', False) else "🔴 SELL"
            sol_amount = trade.get('sol_amount', 0)
            token_amount = trade.get('token_amount', 0)
            price = trade.get('price', 0)
            trader = trade.get('trader', 'N/A')
            timestamp = trade.get('timestamp', 0)
            
            table.add_row(
                trade_type,
                f"{sol_amount:.4f}",
                format_number(token_amount),
                f"{price:.8f}",
                trader[:20] + "..." if len(trader) > 20 else trader,
                format_timestamp(timestamp)
            )
        
        console.print(table)
    else:
        console.print(f"[red]No trades found for {mint_address}[/red]")

@app.command()
def monitor(interval: int = 30):
    """Monitor for new tokens continuously."""
    console.print(f"[bold blue]:satellite: Monitoring for new tokens every {interval} seconds...[/bold blue]")
    console.print("[dim]Press Ctrl+C to stop monitoring[/dim]")
    
    scanner = PumpPortalScanner()
    seen_tokens = set()
    
    try:
        while True:
            tokens = scanner.get_new_tokens(10)
            new_tokens = []
            
            for token in tokens:
                mint = token.get('mint', '')
                if mint and mint not in seen_tokens:
                    seen_tokens.add(mint)
                    new_tokens.append(token)
            
            if new_tokens:
                console.print(f"\n[green]🚨 {len(new_tokens)} NEW TOKEN(S) DETECTED![green]")
                display_token_table(new_tokens, "New Tokens Detected")
            else:
                console.print(f"[dim]{datetime.now().strftime('%H:%M:%S')} - No new tokens detected[/dim]")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user.[/yellow]")

# Legacy commands for compatibility
@app.command()
def meme():
    """Generates a meme."""
    console.print("[yellow]Meme generation feature not yet implemented.[/yellow]")

@app.command()
def bundle():
    """Bundles transactions."""
    console.print("[yellow]Transaction bundling feature not yet implemented.[/yellow]")

@app.command()
def grimcast():
    """Posts to Twitter/X."""
    console.print("[yellow]Twitter/X posting feature not yet implemented.[/yellow]")

@app.command()
def livefeed():
    """Subscribe to real-time Pump.fun events via WebSocket."""
    async def subscribe():
        uri = "wss://pumpportal.fun/api/data"
        while True:
            try:
                console.print("[bold blue]Connecting to PumpPortal WebSocket...[/bold blue]")
                async with websockets.connect(uri) as websocket:
                    # Subscribing to token creation events
                    await websocket.send(json.dumps({"method": "subscribeNewToken"}))
                    # Subscribing to migration events
                    await websocket.send(json.dumps({"method": "subscribeMigration"}))
                    # Example: subscribe to trades by account (customize as needed)
                    await websocket.send(json.dumps({
                        "method": "subscribeAccountTrade",
                        "keys": ["AArPXm8JatJiuyEffuC1un2Sc835SULa4uQqDcaGpAjV"]
                    }))
                    # Example: subscribe to trades on tokens (customize as needed)
                    await websocket.send(json.dumps({
                        "method": "subscribeTokenTrade",
                        "keys": ["91WNez8D22NwBssQbkzjy4s2ipFrzpmn5hfvWVe2aY5p"]
                    }))
                    console.print("[green]Subscribed to real-time events![/green]")
                    async for message in websocket:
                        try:
                            event = json.loads(message)
                            pretty_print_event(event)
                        except Exception as e:
                            console.print(f"[red]Error parsing event: {e}[/red]")
            except Exception as e:
                console.print(f"[red]WebSocket error: {e}. Reconnecting in 5 seconds...[/red]")
                await asyncio.sleep(5)
    
    def pretty_print_event(event: dict):
        event_type = event.get('method', 'unknown')
        data = event.get('data', event)
        ts = datetime.now().strftime('%H:%M:%S')
        if event_type == 'newToken':
            name = data.get('name', 'N/A')
            symbol = data.get('symbol', 'N/A')
            mint = data.get('mint', 'N/A')
            console.print(Panel(f"[bold green]NEW TOKEN[/bold green] [cyan]{name}[/cyan] ([magenta]{symbol}[/magenta])\nMint: {mint}", title=f"{ts} New Token"))
        elif event_type == 'migration':
            console.print(Panel(f"[yellow]Migration event:[/yellow] {data}", title=f"{ts} Migration"))
        elif event_type == 'accountTrade':
            trader = data.get('trader', 'N/A')
            sol = data.get('sol_amount', 0)
            token = data.get('token_amount', 0)
            console.print(Panel(f"[blue]Account Trade[/blue] Trader: {trader} | SOL: {sol} | Token: {token}", title=f"{ts} Account Trade"))
        elif event_type == 'tokenTrade':
            mint = data.get('mint', 'N/A')
            sol = data.get('sol_amount', 0)
            token = data.get('token_amount', 0)
            console.print(Panel(f"[magenta]Token Trade[/magenta] Mint: {mint} | SOL: {sol} | Token: {token}", title=f"{ts} Token Trade"))
        else:
            console.print(Panel(f"[dim]{json.dumps(event, indent=2)}[/dim]", title=f"{ts} Event"))

    asyncio.run(subscribe())

if __name__ == "__main__":
    console.print("[bold cyan]🚀 Pump.fun Token Scanner with PumpPortal API[/bold cyan]")
    console.print("[dim]Available commands: scan, token, search, trades, monitor, livefeed[/dim]\n")
    app() 