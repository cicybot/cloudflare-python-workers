from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
import base64

def pad(text):
    """Pad text to be a multiple of 16 bytes (AES block size)."""
    return text + (16 - len(text) % 16) * chr(16 - len(text) % 16)

def unpad(padded_text):
    """Remove padding after decryption."""
    return padded_text[:-ord(padded_text[-1])]
    
def aes_encrypt(password, plaintext):
    # Generate AES key from the password (PBKDF2 will hash the password to 16 bytes)
    key = PBKDF2(password, b"salt", dkLen=16)

    # Create AES cipher in ECB mode
    cipher = AES.new(key, AES.MODE_ECB)

    # Pad the plaintext to make it multiple of 16 bytes
    padded_text = pad(plaintext)

    # Encrypt the plaintext
    ciphertext = cipher.encrypt(padded_text.encode())

    # Return the base64-encoded ciphertext for readability
    return base64.b64encode(ciphertext).decode()


def aes_decrypt(password, ciphertext_base64):
    # Generate AES key from the password (PBKDF2 will hash the password to 16 bytes)
    key = PBKDF2(password, b"salt", dkLen=16)

    # Decode the base64 ciphertext
    ciphertext = base64.b64decode(ciphertext_base64)

    # Create AES cipher in ECB mode
    cipher = AES.new(key, AES.MODE_ECB)

    # Decrypt the ciphertext
    decrypted_padded_text = cipher.decrypt(ciphertext).decode()

    # Unpad the decrypted text
    return unpad(decrypted_padded_text)
