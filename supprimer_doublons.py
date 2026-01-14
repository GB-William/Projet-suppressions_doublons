#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Programme pour supprimer les fichiers en double dans un ou plusieurs répertoires.
Parcourt récursivement tous les sous-répertoires et identifie les doublons par leur contenu (hash MD5).
"""

import os
import sys
import hashlib
import argparse
from collections import defaultdict
from pathlib import Path


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
        Hash MD5 du fichier en hexadécimal
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


def afficher_doublons(doublons):
    """
    Affiche la liste des fichiers en double.
    
    Args:
        doublons: Liste de groupes de fichiers en double
    """
    if not doublons:
        print("\nAucun doublon trouvé!")
        return
    
    print(f"\n{len(doublons)} groupe(s) de fichiers en double trouvé(s):\n")
    espace_total_recupere = 0
    
    for i, groupe in enumerate(doublons, 1):
        taille_fichier = groupe[0].stat().st_size
        espace_groupe = taille_fichier * (len(groupe) - 1)
        espace_total_recupere += espace_groupe
        
        print(f"Groupe {i} ({formater_taille(taille_fichier)} par fichier):")
        print(f"  → Conserver: {groupe[0]}")
        for doublon in groupe[1:]:
            print(f"  ✗ Supprimer: {doublon}")
        print()
    
    print(f"Espace total qui peut être récupéré: {formater_taille(espace_total_recupere)}")


def supprimer_doublons(doublons, confirmer=True):
    """
    Supprime les fichiers en double.
    
    Args:
        doublons: Liste de groupes de fichiers en double
        confirmer: Si True, demande confirmation avant de supprimer
    
    Returns:
        Nombre de fichiers supprimés, espace récupéré
    """
    if not doublons:
        return 0, 0
    
    if confirmer:
        reponse = input(f"\nVoulez-vous supprimer {sum(len(g) - 1 for g in doublons)} fichier(s) en double? (o/n): ")
        if reponse.lower() not in ['o', 'oui', 'y', 'yes']:
            print("Suppression annulée.")
            return 0, 0
    
    fichiers_supprimes = 0
    espace_recupere = 0
    
    for groupe in doublons:
        taille_fichier = groupe[0].stat().st_size
        # Conserver le premier fichier, supprimer les autres
        for doublon in groupe[1:]:
            try:
                espace_recupere += doublon.stat().st_size
                doublon.unlink()
                fichiers_supprimes += 1
                print(f"✓ Supprimé: {doublon}")
            except (OSError, IOError) as e:
                print(f"✗ Erreur lors de la suppression de {doublon}: {e}", file=sys.stderr)
    
    return fichiers_supprimes, espace_recupere


def main():
    """
    Fonction principale du programme.
    """
    parser = argparse.ArgumentParser(
        description='Supprime les fichiers en double dans un ou plusieurs répertoires.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python supprimer_doublons.py /chemin/vers/repertoire
  python supprimer_doublons.py /rep1 /rep2 /rep3
  python supprimer_doublons.py /rep1 /rep2 --no-confirm
        """
    )
    
    parser.add_argument(
        'repertoires',
        nargs='+',
        help='Un ou plusieurs répertoires à analyser'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Supprime les doublons sans demander de confirmation'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Affiche les doublons sans les supprimer'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Programme de suppression de fichiers en double")
    print("=" * 60)
    
    # Parcourir les répertoires et identifier les doublons
    fichiers_par_hash = parcourir_repertoires(args.repertoires)
    doublons = identifier_doublons(fichiers_par_hash)
    
    # Afficher les résultats
    afficher_doublons(doublons)
    
    # Supprimer les doublons si demandé
    if not args.dry_run and doublons:
        confirmer = not args.no_confirm
        fichiers_supprimes, espace_recupere = supprimer_doublons(doublons, confirmer=confirmer)
        
        if fichiers_supprimes > 0:
            print(f"\n{'=' * 60}")
            print(f"Résumé:")
            print(f"  Fichiers supprimés: {fichiers_supprimes}")
            print(f"  Espace récupéré: {formater_taille(espace_recupere)}")
            print(f"{'=' * 60}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\nErreur inattendue: {e}", file=sys.stderr)
        sys.exit(1)

