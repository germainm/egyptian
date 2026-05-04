"""
encryptedstorage.py — Stockage chiffre AES-256-GCM pour Mayan EDMS

Format de fichier (binaire) :
    [4 bytes]  Magic : b'MENC'
    [1 byte]   Version : 0x01
    [1 byte]   Longueur du sel (en bytes, max 255)
    [N bytes]  Sel PBKDF2 aleatoire, unique par fichier (N = valeur byte precedent)
    [12 bytes] Nonce AES-GCM aleatoire, unique par fichier
    [M bytes]  Ciphertext AES-GCM + tag d'authentification (16 bytes tag integre)

Securite :
    - AES-256-GCM : chiffrement authentifie (AEAD) -- integrite et confidentialite
    - Sel unique par fichier : PBKDF2 pleinement efficace, pas d'attaque par table
    - Nonce unique par fichier : pas de reutilisation nonce/cle
    - 600 000 iterations PBKDF2-SHA256 (recommandation OWASP 2024)
    - Pas de sel fixe, pas de padding oracle, pas de CBC

Dependance : cryptography (PyCA) -- pip install cryptography
"""

import io
import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

from django.core.files.base import ContentFile

from ..classes import PassthroughStorage

from .literals import (
    ENCRYPTION_KEY_DERIVATION_ITERATIONS,
    ENCRYPTION_KEY_SIZE,
    ENCRYPTION_FILE_CHUNK_SIZE,
)

# ── Constantes du format de fichier ──────────────────────────────────────────

MAGIC = b'MENC'
VERSION = 0x01
SALT_SIZE = 32    # bytes -- sel PBKDF2 par fichier
NONCE_SIZE = 12   # bytes -- nonce AES-GCM (96 bits, recommande NIST)
HEADER_FIXED_SIZE = len(MAGIC) + 1 + 1  # magic + version + salt_len


class EncryptedFileError(Exception):
    """Erreur lors du dechiffrement ou de la validation du format."""
    pass


# ── Derivation de cle ─────────────────────────────────────────────────────────

def _derive_key(password, salt):
    """
    Deriver une cle AES-256 depuis le mot de passe et le sel.
    PBKDF2-HMAC-SHA256, 600 000 iterations (OWASP 2024).

    Args:
        password (bytes): mot de passe
        salt (bytes): sel aleatoire unique par fichier

    Returns:
        bytes: cle de 32 bytes (AES-256)
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=ENCRYPTION_KEY_SIZE,
        salt=salt,
        iterations=ENCRYPTION_KEY_DERIVATION_ITERATIONS,
    )
    return kdf.derive(key_material=password)


# ── Chiffrement (ecriture) ────────────────────────────────────────────────────

def _encrypt_content(password, plaintext):
    """
    Chiffrer des donnees avec AES-256-GCM.

    Un sel et un nonce aleatoires sont generes pour chaque appel.
    Le tag GCM (16 bytes) est integre a la fin du ciphertext par cryptography.

    Args:
        password (bytes): mot de passe
        plaintext (bytes): donnees claires

    Returns:
        bytes: contenu complet du fichier chiffre (header + ciphertext + tag)
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(password=password, salt=salt)

    aesgcm = AESGCM(key=key)
    # encrypt() retourne ciphertext || tag (tag de 16 bytes en fin)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)

    header = (
        MAGIC
        + struct.pack('B', VERSION)
        + struct.pack('B', SALT_SIZE)
        + salt
        + nonce
    )
    return header + ciphertext_with_tag


# ── Dechiffrement (lecture) ───────────────────────────────────────────────────

def _decrypt_content(password, encrypted_data):
    """
    Dechiffrer des donnees avec AES-256-GCM.

    Valide le magic header, la version, puis authentifie et dechiffre.

    Args:
        password (bytes): mot de passe
        encrypted_data (bytes): contenu brut du fichier chiffre

    Returns:
        bytes: donnees claires

    Raises:
        EncryptedFileError: si le format est invalide, les donnees corrompues,
                            ou le mot de passe incorrect.
    """
    if len(encrypted_data) < HEADER_FIXED_SIZE:
        raise EncryptedFileError(
            'Fichier trop court pour contenir un header valide.'
        )

    # Valider le magic header
    if encrypted_data[:len(MAGIC)] != MAGIC:
        raise EncryptedFileError(
            'Magic header manquant -- ce fichier n\'est pas au format MENC v1.'
        )

    offset = len(MAGIC)

    # Version
    version = struct.unpack('B', encrypted_data[offset:offset + 1])[0]
    offset += 1
    if version != VERSION:
        raise EncryptedFileError(
            'Version de format non supportee : {} (attendu {})'.format(
                version, VERSION
            )
        )

    # Longueur du sel
    salt_len = struct.unpack('B', encrypted_data[offset:offset + 1])[0]
    offset += 1

    # Verifier qu'il reste assez de donnees : sel + nonce + tag minimum
    min_remaining = salt_len + NONCE_SIZE + 16
    if len(encrypted_data) - offset < min_remaining:
        raise EncryptedFileError('Fichier tronque -- donnees insuffisantes.')

    # Sel
    salt = encrypted_data[offset:offset + salt_len]
    offset += salt_len

    # Nonce
    nonce = encrypted_data[offset:offset + NONCE_SIZE]
    offset += NONCE_SIZE

    # Ciphertext + tag GCM
    ciphertext_with_tag = encrypted_data[offset:]

    # Deriver la cle et dechiffrer + authentifier
    key = _derive_key(password=password, salt=salt)
    aesgcm = AESGCM(key=key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
    except InvalidTag:
        raise EncryptedFileError(
            'Echec de l\'authentification GCM -- '
            'mot de passe incorrect ou donnees corrompues/modifiees.'
        )

    return plaintext


# ── BufferedEncryptedFile ─────────────────────────────────────────────────────

class BufferedEncryptedFile(io.RawIOBase):
    """
    Fichier dechiffre presentant une interface file-like standard.

    Le dechiffrement est effectue en une seule passe a l'ouverture car
    AES-GCM doit valider le tag d'authentification sur l'integralite des
    donnees avant d'en retourner une seule octet.

    En ecriture, les donnees sont bufferisees en memoire et chiffrees
    atomiquement a la fermeture (close/context manager).
    """

    def __init__(self, file_object, password, mode='rb'):
        super().__init__()
        self.mode = mode
        self._password = password
        self._file_object = file_object
        self._write_mode = 'w' in mode or ('+' in mode and 'r' not in mode)

        if not self._write_mode:
            # Lecture : dechiffrer et authentifier tout le contenu
            encrypted_data = file_object.read()
            plaintext = _decrypt_content(
                password=password,
                encrypted_data=encrypted_data,
            )
            self._buffer = io.BytesIO(plaintext)
        else:
            # Ecriture : buffer memoire, chiffrement a la fermeture
            self._write_buffer = io.BytesIO()
            self._buffer = self._write_buffer

    # ── Interface de lecture ──────────────────────────────────────────────────

    def read(self, size=-1):
        if self._write_mode:
            raise io.UnsupportedOperation('read sur un fichier en ecriture')
        return self._buffer.read(size)

    def read1(self, size=-1):
        return self.read(size)

    def readinto(self, b):
        data = self.read(len(b))
        n = len(data)
        b[:n] = data
        return n

    def readline(self, size=-1):
        return self._buffer.readline(size)

    def seek(self, pos, whence=0):
        return self._buffer.seek(pos, whence)

    def tell(self):
        return self._buffer.tell()

    def readable(self):
        return not self._write_mode

    def writable(self):
        return self._write_mode

    def seekable(self):
        return True

    # ── Interface d'ecriture ──────────────────────────────────────────────────

    def write(self, data):
        if not self._write_mode:
            raise io.UnsupportedOperation('write sur un fichier en lecture')
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self._write_buffer.write(data)

    # ── Fermeture : chiffrement effectif ──────────────────────────────────────

    def close(self):
        if not self.closed and self._write_mode:
            plaintext = self._write_buffer.getvalue()
            encrypted = _encrypt_content(
                password=self._password,
                plaintext=plaintext,
            )
            self._file_object.seek(0)
            self._file_object.write(encrypted)
            self._file_object.truncate()
            if hasattr(self._file_object, 'flush'):
                self._file_object.flush()

        if hasattr(self._file_object, 'close'):
            self._file_object.close()

        super().close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# ── EncryptedPassthroughStorage ───────────────────────────────────────────────

class EncryptedPassthroughStorage(PassthroughStorage):
    """
    Storage Django qui chiffre/dechiffre les fichiers avec AES-256-GCM.

    Chaque fichier est chiffre avec un sel et un nonce aleatoires uniques,
    garantissant qu'aucun deux fichiers ne partagent les memes parametres
    cryptographiques meme s'ils ont le meme contenu.

    Configuration dans settings.py / config.yml :
        STORAGE_BACKEND: mayan.apps.storage.backends.encryptedstorage.EncryptedPassthroughStorage
        STORAGE_BACKEND_ARGUMENTS:
            password: "votre-mot-de-passe-fort"

    Le mot de passe peut etre une chaine ou des bytes.
    Il est recommande d'utiliser un mot de passe d'au moins 32 caracteres
    aleatoires, stocke dans les variables d'environnement et non dans le code.
    """

    def __init__(self, *args, **kwargs):
        password = kwargs.pop('password')
        super().__init__(*args, **kwargs)

        # Normaliser en bytes une seule fois
        if isinstance(password, str):
            password = password.encode('utf-8')
        self._password = password

    # ── Ouverture ─────────────────────────────────────────────────────────────

    def open(self, name, mode='rb', _direct=False):
        """
        Ouvrir un fichier.

        _direct=True bypasse le dechiffrement (acces brut au fichier chiffre).
        """
        next_kwargs = {'name': name}

        if _direct:
            next_kwargs['mode'] = mode
            if issubclass(self.next_storage_class, PassthroughStorage):
                next_kwargs['_direct'] = _direct
            return self._call_backend_method(
                method_name='open', kwargs=next_kwargs
            )

        # Le fichier sous-jacent est toujours ouvert en binaire
        next_kwargs['mode'] = 'rb+'
        storage_file = self._call_backend_method(
            method_name='open', kwargs=next_kwargs
        )

        return BufferedEncryptedFile(
            file_object=storage_file,
            password=self._password,
            mode=mode,
        )

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def save(self, name, content, max_length=None, _direct=False):
        """
        Sauvegarder un fichier en le chiffrant.

        _direct=True bypasse le chiffrement (sauvegarde brute).
        """
        next_kwargs = {'max_length': max_length, 'name': name}

        if _direct:
            next_kwargs['content'] = content
            if issubclass(self.next_storage_class, PassthroughStorage):
                next_kwargs['_direct'] = _direct
            return self._call_backend_method(
                method_name='save', kwargs=next_kwargs
            )

        # Lire tout le contenu plaintext
        if hasattr(content, 'read'):
            plaintext = content.read()
        else:
            plaintext = bytes(content)

        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')

        # Chiffrer avec sel et nonce aleatoires
        encrypted = _encrypt_content(
            password=self._password,
            plaintext=plaintext,
        )

        return self._call_backend_method(
            method_name='save',
            kwargs={
                'content': ContentFile(content=encrypted),
                'name': name,
            }
        )
