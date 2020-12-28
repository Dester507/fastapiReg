from hashlib import pbkdf2_hmac
from os import urandom


def hash_password(password):
    salt = urandom(32)
    key = pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 50000)
    return [key, salt]


def check_password_hash(new_password, salt):
    key = pbkdf2_hmac('sha256', new_password.encode('utf-8'), salt, 50000)
    return key
