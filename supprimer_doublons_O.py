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
        Dictionnaire {hash: [liste des chemins de fichiers]}
    """
    fichiers_par_hash = defaultdict(list)
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
                
                hash_fichier = calculer_hash_fichier(fichier_path)
                if hash_fichier:
                    fichiers_par_hash[hash_fichier].append(fichier_path)
    
    print(f"\nTotal de fichiers analysés: {fichiers_traites}")
    return fichiers_par_hash


def identifier_doublons(fichiers_par_hash):
    """
    Identifie les fichiers en double (même hash).
    
    Args:
        fichiers_par_hash: Dictionnaire {hash: [liste des chemins]}
    
    Returns:
        Liste de groupes de fichiers en double
    """
    doublons = []
    for hash_fichier, chemins in fichiers_par_hash.items():
        if len(chemins) > 1:
            doublons.append(chemins)
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

