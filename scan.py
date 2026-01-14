import sys
from collections import defaultdict
from pathlib import Path

from fichier_utils import lire_premiers_octets, calculer_hash_fichier


def parcourir_repertoires(repertoires):
    """
    Parcourt récursivement les répertoires et collecte tous les fichiers.
    
    Args:
        repertoires: Liste des chemins de répertoires à parcourir
    
    Returns:
        Dictionnaire {taille_en_octets: [liste des chemins de fichiers]}
    """
    fichiers_par_taille = defaultdict(list)
    fichiers_traites = 0
    
    for repertoire in repertoires:
        repertoire_path = Path(repertoire)
        if not repertoire_path.exists():
            print(f"Attention: Le répertoire '{repertoire}' n'existe pas. Ignoré.", file=sys.stderr)
            continue
        
        if not repertoire_path.is_dir():
            print(f"Attention: '{repertoire}' n'est pas un répertoire. Ignoré.", file=sys.stderr)
            continue
        
        print(f"Analyse du répertoire: {repertoire_path.absolute()}")
        
        # Parcourir récursivement tous les fichiers
        for fichier_path in repertoire_path.rglob('*'):
            if fichier_path.is_file():
                fichiers_traites += 1
                if fichiers_traites % 100 == 0:
                    print(f"  Fichiers analysés: {fichiers_traites}...", end='\r')
                
                try:
                    taille = fichier_path.stat().st_size
                    fichiers_par_taille[taille].append(fichier_path)
                except (OSError, IOError) as e:
                    print(f"Erreur lors de la récupération de la taille de {fichier_path}: {e}", file=sys.stderr)
    
    print(f"\nTotal de fichiers analysés: {fichiers_traites}")
    return fichiers_par_taille


def identifier_doublons(fichiers_par_taille):
    """
    Identifie les fichiers en double en plusieurs étapes :
      1. Regroupe les fichiers par taille (déjà fait dans fichiers_par_taille).
      2. Pour chaque taille, regroupe par les 5 premiers octets.
      3. Pour chaque groupe ayant même taille et mêmes 5 octets, calcule le hash MD5
         pour confirmer les doublons.
    
    Args:
        fichiers_par_taille: Dictionnaire {taille: [liste des chemins]}
    
    Returns:
        Liste de groupes de fichiers en double
    """
    doublons = []
    
    # Étape 1 déjà réalisée : on reçoit déjà les fichiers regroupés par taille.
    for taille, chemins in fichiers_par_taille.items():
        if len(chemins) < 2:
            continue  # avec une seule occurrence, aucun doublon possible
        
        # Étape 2 : regrouper par 5 premiers octets
        groupes_par_prefixe = defaultdict(list)
        for chemin in chemins:
            prefixe = lire_premiers_octets(chemin, n=5)
            if prefixe is None:
                continue
            groupes_par_prefixe[prefixe].append(chemin)
        
        # Étape 3 : pour chaque groupe ayant même taille et même préfixe,
        # calculer les hash MD5 pour trouver les vrais doublons
        for prefixe, chemins_meme_prefixe in groupes_par_prefixe.items():
            if len(chemins_meme_prefixe) < 2:
                continue
            
            fichiers_par_hash = defaultdict(list)
            for chemin in chemins_meme_prefixe:
                hash_fichier = calculer_hash_fichier(chemin)
                if hash_fichier:
                    fichiers_par_hash[hash_fichier].append(chemin)
            
            for hash_fichier, chemins_hash in fichiers_par_hash.items():
                if len(chemins_hash) > 1:
                    doublons.append(chemins_hash)
    
    return doublons

