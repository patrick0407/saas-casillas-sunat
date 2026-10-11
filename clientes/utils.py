import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings

def _obtener_fernet():
    # Usa la SECRET_KEY de Django para derivar una clave de encriptación segura
    clave_base = settings.SECRET_KEY.encode()
    salt = b'sunat_sol_salt_segura_2026' # Salt fijo para derivación
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(clave_base))
    return Fernet(key)

def encriptar_texto(texto_plano: str) -> str:
    """Encripta un texto (ej. Clave SOL)"""
    if not texto_plano:
        return ""
    f = _obtener_fernet()
    return f.encrypt(texto_plano.encode()).decode()

def desencriptar_texto(texto_encriptado: str) -> str:
    """Desencripta la clave para enviarla al bot de Selenium"""
    if not texto_encriptado:
        return ""
    f = _obtener_fernet()
    return f.decrypt(texto_encriptado.encode()).decode()