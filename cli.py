import typer
from rich.console import Console
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature
import base58
import zmq
from utils.crypto import encrypt_message, decrypt_message, generate_key

app = typer.Typer()
console = Console()

# Solana mainnet RPC endpoint
SOLANA_RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
PUMP_FUN_PROGRAM_ADDRESS = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
CREATE_DISCRIMINATOR = "181ec828051c0777"

# ShadowNet config
SHADOWNET_AGENT_ADDRESS = "tcp://localhost:5555"
SHADOWNET_KEY = b'\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29'  # 16-byte key

@app.command()
def scan(limit: int = 5):
    """Scans for new tokens on Pump.fun."""
    console.print(f":mag: Scanning for new tokens on Pump.fun...")
    try:
        client = Client(SOLANA_RPC_ENDPOINT)
        program_pubkey = Pubkey.from_string(PUMP_FUN_PROGRAM_ADDRESS)
        console.print(f"--> Connected to Solana mainnet.")
        console.print(f"--> Monitoring Pump.fun program: [cyan]{PUMP_FUN_PROGRAM_ADDRESS}[/cyan]")

        signatures = client.get_signatures_for_address(program_pubkey, limit=limit)
        console.print("--> Found recent transactions:")
        for sig_info in signatures.value:
            signature = sig_info.signature
            tx_response = client.get_transaction(signature, max_supported_transaction_version=0)
            if tx_response.value and tx_response.value.transaction and tx_response.value.transaction.transaction:
                message = tx_response.value.transaction.transaction.message
                for ix in message.instructions:
                    program_id = message.account_keys[ix.program_id_index]
                    if str(program_id) == PUMP_FUN_PROGRAM_ADDRESS:
                        ix_data_hex = base58.b58decode(ix.data).hex()
                        if ix_data_hex.startswith(CREATE_DISCRIMINATOR):
                            console.print(f"    - [yellow]{signature}[/yellow]")
                            console.print("      [bold green]Found 'create' instruction![/bold green]")
                            console.print("        [cyan]Token data decoding not yet implemented.[/cyan]")
            else:
                console.print(f"[dim]No transaction data for {signature}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

@app.command()
def meme():
    """Generates a meme."""
    console.print(":art: Generating meme...")

@app.command()
def bundle():
    """Bundles transactions."""
    console.print(":package: Bundling transactions...")

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
def grimcast():
    """Posts to Twitter/X."""
    console.print(":bird: Posting to Twitter/X...")

if __name__ == "__main__":
    app()
