import zmq
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# In a real scenario, keys would be managed securely (e.g., distributed via a secure channel)
# For demonstration, a fixed key is used.
SHADOWNET_KEY = b'\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29' # 16-byte key

def encrypt_message(message: str, key: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
    return bytes(cipher.iv) + ct_bytes

def decrypt_message(ciphertext: bytes, key: bytes) -> str:
    iv = ciphertext[:AES.block_size]
    ct = ciphertext[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode()

def start_shadow_agent(port: int):
    context = zmq.Context()
    socket = context.socket(zmq.REP)  # Reply socket
    socket.bind(f"tcp://*:{port}")
    print(f"ShadowNet Agent listening on port {port}...")

    while True:
        encrypted_message = socket.recv()
        message = decrypt_message(encrypted_message, SHADOWNET_KEY)
        print(f"Received request: {message}")
        encrypted_ack = encrypt_message(f"ACK: {message}", SHADOWNET_KEY)
        socket.send(encrypted_ack)

if __name__ == "__main__":
    start_shadow_agent(5555) # Default port