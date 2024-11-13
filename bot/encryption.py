import os
from cryptography.fernet import Fernet

KEY = os.getenv('KEY')


def encrypt(password: str) -> str:
    cipher_suite = Fernet(KEY)
    encrypted_password = cipher_suite.encrypt(password.encode())
    return encrypted_password.decode()


def decrypt(encrypted_password: str) -> str:
    cipher_suite = Fernet(KEY)
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode()).decode()
    return decrypted_password
