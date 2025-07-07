import typer
from rich.console import Console
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature
import base58
import zmq
from utils.crypto import encrypt_message, decrypt_message, generate_key
import asyncio
import websockets
import json
import subprocess

app = typer.Typer(add_completion=False, rich_markup_mode="rich")
console = Console()

# Banner boot
def print_banner():
    try:
        subprocess.run([
            "npx", "cfonts", "GRIMNODE",
            "--gradient", "grey,white",
            "--font", "block",
            "--align", "center",
            "--space", "true",
            "--transition", "true"
        ], check=True)
    except Exception:
        console.print("[bold white]GRIMNODE[/bold white]")

# RPC + constants
SOLANA_RPC_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-api.projectserum.com",
    "https://rpc.ankr.com/solana"
]
PUMP_FUN_PROGRAM_ADDRESS = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
CREATE_DISCRIMINATOR = "181ec828051c0777"
SHADOWNET_AGENT_ADDRESS = "tcp://localhost:5555"
SHADOWNET_KEY = b'\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29'

# Welcome handler
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    print_banner()
    if ctx.invoked_subcommand is None:
        console.print("[bold magenta]Welcome to GRIMNODE. Autonomy in Chaos.[/bold magenta]")
        console.print("[white]> Available commands: [cyan]scan[/cyan], [cyan]bundle[/cyan], [cyan]send-job[/cyan], [cyan]grimcast[/cyan], [cyan]livefeed[/cyan][/white]")
        console.print("[dim]Use '--help' after a command to explore its options.[/dim]")
        raise typer.Exit()

@app.command()
def scan(limit: int = 5):
    """Scans for new tokens on Pump.fun."""
    console.print(f":mag: Scanning for new tokens on Pump.fun...")
    for endpoint in SOLANA_RPC_ENDPOINTS:
        try:
            console.print(f"--> Trying RPC endpoint: [cyan]{endpoint}[/cyan]")
            client = Client(endpoint)
            program_pubkey = Pubkey.from_string(PUMP_FUN_PROGRAM_ADDRESS)
            try:
                signatures = client.get_signatures_for_address(program_pubkey, limit=limit)
                console.print(f"--> Connected to Solana mainnet via {endpoint}")
                console.print(f"--> Monitoring Pump.fun program: [cyan]{PUMP_FUN_PROGRAM_ADDRESS}[/cyan]")
                console.print(f"--> Found {len(signatures.value)} recent transactions:")
                found_creates = 0
                for sig_info in signatures.value:
                    signature = sig_info.signature
                    console.print(f"    - Processing: [dim]{signature}[/dim]")
                    try:
                        tx_response = client.get_transaction(signature, max_supported_transaction_version=0)
                        if tx_response.value and tx_response.value.transaction and tx_response.value.transaction.transaction:
                            message = tx_response.value.transaction.transaction.message
                            for ix in message.instructions:
                                program_id = message.account_keys[ix.program_id_index]
                                if str(program_id) == PUMP_FUN_PROGRAM_ADDRESS:
                                    ix_data_hex = base58.b58decode(ix.data).hex()
                                    if ix_data_hex.startswith(CREATE_DISCRIMINATOR):
                                        found_creates += 1
                                        console.print(f"      [yellow]{signature}[/yellow]")
                                        console.print("        [bold green]Found 'create' instruction![/bold green]")
                                        console.print("          [cyan]Token data decoding not yet implemented.[/cyan]")
                        else:
                            console.print(f"      [dim]No transaction data for {signature}[/dim]")
                    except Exception as tx_error:
                        console.print(f"      [red]Error processing transaction {signature}: {tx_error}[/red]")
                        continue
                if found_creates == 0:
                    console.print("    [yellow]No 'create' instructions found in recent transactions.[/yellow]")
                else:
                    console.print(f"    [green]Found {found_creates} 'create' instructions![/green]")
                return
            except Exception as sig_error:
                console.print(f"[red]Error fetching signatures: {sig_error}[/red]")
                continue
        except Exception as e:
            console.print(f"[red]Error connecting to {endpoint}: {e}[/red]")
            continue
    console.print("[bold red]Failed to connect to any Solana RPC endpoint. Check your internet connection.[/bold red]")

@app.command()
def bundle(
    tokens: str = typer.Argument(..., help="Comma-separated list of token symbols (e.g. SOL,USDC,ETH)"),
    slippage: float = typer.Option(1.0, help="Slippage tolerance percentage (default: 1.0)"),
    simulate: bool = typer.Option(False, help="Simulate the bundle instead of executing")
):
    """Bundle token actions and estimate costs."""
    from bundle.executor import bundle_tokens, validate_bundle, estimate_bundle_cost, generate_bundle_summary
    token_list = [t.strip() for t in tokens.split(",") if t.strip()]
    bundle_data = bundle_tokens(token_list, slippage, simulate)
    validation = validate_bundle(bundle_data)
    summary = generate_bundle_summary(bundle_data)
    cost = estimate_bundle_cost(bundle_data)
    console.print(f"[bold green]Bundle Summary:[/bold green]\n{summary}")
    console.print(f"[bold blue]Cost Estimate:[/bold blue] {cost}")
    if not validation["valid"]:
        console.print(f"[red]Bundle validation failed: {validation['errors']}[/red]")
    elif validation["warnings"]:
        console.print(f"[yellow]Warnings: {validation['warnings']}[/yellow]")
    else:
        console.print("[green]Bundle is valid and ready![/green]")

@app.command()
def send_job(job_data: str):
    """Sends an encrypted job to the ShadowNet."""
    console.print(f":satellite: Sending encrypted job to ShadowNet...")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(SHADOWNET_AGENT_ADDRESS)
    try:
        encrypted_job = encrypt_message(job_data, SHADOWNET_KEY)
        socket.send(encrypted_job)
        console.print("--> Job sent. Waiting for acknowledgment...")
        encrypted_ack = socket.recv()
        ack_message = decrypt_message(encrypted_ack, SHADOWNET_KEY)
        console.print(f"--> Received acknowledgment: [green]{ack_message}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error sending job: {e}[/bold red]")
    finally:
        socket.close()
        context.term()

@app.command()
def grimcast(message: str = typer.Argument(..., help="The message to post to Twitter/X")):
    """Posts a message to Twitter/X using Tweepy."""
    import os
    import tweepy
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    if not all([api_key, api_secret, access_token, access_token_secret]):
        console.print("[red]Twitter API credentials not set in environment variables.[/red]")
        return
    try:
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        api = tweepy.API(auth)
        tweet = api.update_status(status=message)
        console.print(f"[green]Tweet posted![/green] [link=https://twitter.com/user/status/{tweet.id}]{tweet.text}[/link]")
    except Exception as e:
        console.print(f"[red]Error posting to Twitter/X: {e}[/red]")

@app.command()
def livefeed():
    """Subscribe to real-time Pump.fun events via WebSocket."""
    async def subscribe():
        uri = "wss://pumpportal.fun/api/data"
        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                event = json.loads(message)
                console.print(event)
    asyncio.run(subscribe())

if __name__ == "__main__":
    app()
