ZIP_CHUNK_SIZE = 64 * 1024  # 64K
ZIP_MEMBER_FILENAME = 'mayan_file'


# literals.py — Constantes pour le backend de stockage chiffre

# Taille de la cle AES en bytes (AES-256 = 32 bytes)
ENCRYPTION_KEY_SIZE = 32

# Iterations PBKDF2-HMAC-SHA256
# OWASP 2024 recommande 600 000 pour SHA-256
# Valeur precedente (pyCrypto) : souvent 10 000 -- mise a jour requise
ENCRYPTION_KEY_DERIVATION_ITERATIONS = 600_000

# Taille des chunks lors de la lecture en streaming (non utilise pour GCM
# qui chiffre le fichier entier, mais conserve pour compatibilite)
ENCRYPTION_FILE_CHUNK_SIZE = 16 * 1024  # 16 KB
