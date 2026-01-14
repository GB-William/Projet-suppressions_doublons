import sys
import hashlib


def lire_premiers_octets(filepath, n=5):
    """
    Lit les n premiers octets d'un fichier.
    
    Args:
        filepath: Chemin vers le fichier
        n: Nombre d'octets à lire
    
    Returns:
        Les n premiers octets sous forme de bytes, ou None en cas d'erreur.
    """
    try:
        with open(filepath, 'rb') as f:
            return f.read(n)
    except (IOError, OSError) as e:
        print(f"Erreur lors de la lecture des premiers octets de {filepath}: {e}", file=sys.stderr)
        return None


def calculer_hash_fichier(filepath, chunk_size=8192):
    """
    Calcule le hash MD5 d'un fichier.
    
    Args:
        filepath: Chemin vers le fichier
        chunk_size: Taille des blocs à lire (par défaut 8KB)
    
    Returns:
        Hash MD5 du fichier en hexadécimal ou None en cas d'erreur.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, OSError) as e:
        print(f"Erreur lors de la lecture de {filepath}: {e}", file=sys.stderr)
        return None


def formater_taille(taille_octets):
    """
    Formate une taille en octets en format lisible.
    
    Args:
        taille_octets: Taille en octets
    
    Returns:
        Chaîne formatée (ex: "1.5 MB")
    """
    for unite in ['B', 'KB', 'MB', 'GB', 'TB']:
        if taille_octets < 1024.0:
            return f"{taille_octets:.2f} {unite}"
        taille_octets /= 1024.0
    return f"{taille_octets:.2f} PB"

