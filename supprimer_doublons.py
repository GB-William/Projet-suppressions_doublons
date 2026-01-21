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

def regrouper_par_taille(fichiers: list[Path]) -> dict[int, list[Path]]:
    """
    Regroupe les fichiers par taille et élimine les tailles uniques.
    """
    tailles = defaultdict(list)

    for fichier in fichiers:
        try:
            taille = fichier.stat().st_size
            tailles[taille].append(fichier)
        except OSError:
            continue

    # On ne garde que les tailles avec au moins deux fichiers
    return {t: lst for t, lst in tailles.items() if len(lst) > 1}

def comparer_octets(groupes_par_taille: dict[int, list[Path]], x: int = 8) -> list[Path]:
    """
    Compare les x premiers octets des fichiers de même taille.
    Retourne la liste des fichiers candidats (non isolés).
    """
    candidats = []

    for fichiers in groupes_par_taille.values():
        octets_map = defaultdict(list)

        for fichier in fichiers:
            try:
                with open(fichier, "rb") as f:
                    prefixe = f.read(x)
                octets_map[prefixe].append(fichier)
            except OSError:
                continue

        # On ne garde que les groupes avec doublons
        for groupe in octets_map.values():
            if len(groupe) > 1:
                candidats.extend(groupe)

    return candidats

def comparer_hash(fichiers: list[Path]) -> list[list[Path]]:
    """
    Compare les hash des fichiers et retourne les vrais doublons.
    """
    hash_map = defaultdict(list)

    for fichier in fichiers:
        try:
            hasher = hashlib.md5()
            with open(fichier, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            hash_map[hasher.hexdigest()].append(fichier)
        except OSError:
            continue

    # Chaque groupe contient uniquement de vrais doublons
    return [groupe for groupe in hash_map.values() if len(groupe) > 1]

def formater_taille(taille_octets: int) -> str:
    """
    Formate une taille en octets en format lisible (Ko, Mo, Go).
    """
    for unite in ['o', 'Ko', 'Mo', 'Go', 'To']:
        if taille_octets < 1024.0:
            return f"{taille_octets:.2f} {unite}"
        taille_octets /= 1024.0
    return f"{taille_octets:.2f} Po"

def afficher_doublons(doublons: list[list[Path]]):
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


def supprimer_doublons(doublons: list[list[Path]], confirmer: bool = True) -> tuple[int, int]:
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


def enumerer_fichiers(repertoires: list[str], recursif: bool = True) -> list[Path]:
    """
    Énumère tous les fichiers dans les répertoires donnés.
    
    Args:
        repertoires: Liste des chemins de répertoires à parcourir
        recursif: Si True, parcourt récursivement les sous-répertoires
    
    Returns:
        Liste de tous les fichiers trouvés
    """
    fichiers = []
    
    for rep in repertoires:
        chemin = Path(rep)
        
        if not chemin.exists():
            print(f"⚠️  Le répertoire '{rep}' n'existe pas.", file=sys.stderr)
            continue
        
        if chemin.is_file():
            fichiers.append(chemin)
        elif chemin.is_dir():
            if recursif:
                fichiers.extend([f for f in chemin.rglob('*') if f.is_file()])
            else:
                fichiers.extend([f for f in chemin.glob('*') if f.is_file()])
    
    return fichiers


def main():
    """
    Fonction principale du programme.
    """
    parser = argparse.ArgumentParser(
        description="Trouve et supprime les fichiers en double dans un ou plusieurs répertoires.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'repertoires',
        nargs='+',
        help='Répertoire(s) à analyser'
    )
    
    parser.add_argument(
        '-d', '--delete',
        action='store_true',
        help='Supprimer les doublons (demande confirmation par défaut)'
    )
    
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Supprimer sans demander confirmation (à utiliser avec --delete)'
    )
    
    parser.add_argument(
        '-n', '--non-recursive',
        action='store_true',
        help='Ne pas parcourir récursivement les sous-répertoires'
    )
    
    args = parser.parse_args()
    
    print("🔍 Énumération des fichiers...")
    fichiers = enumerer_fichiers(args.repertoires, recursif=not args.non_recursive)
    
    if not fichiers:
        print("Aucun fichier trouvé.")
        return
    
    print(f"   {len(fichiers)} fichier(s) trouvé(s).")
    
    print("\n📊 Regroupement par taille...")
    groupes_taille = regrouper_par_taille(fichiers)
    nb_candidats_taille = sum(len(g) for g in groupes_taille.values())
    print(f"   {nb_candidats_taille} fichier(s) avec des tailles en commun.")
    
    if not groupes_taille:
        print("\nAucun doublon trouvé!")
        return
    
    print("\n🔬 Comparaison des premiers octets...")
    candidats = comparer_octets(groupes_taille)
    print(f"   {len(candidats)} candidat(s) potentiel(s).")
    
    if not candidats:
        print("\nAucun doublon trouvé!")
        return
    
    print("\n🔐 Calcul des hash MD5...")
    doublons = comparer_hash(candidats)
    
    afficher_doublons(doublons)
    
    if args.delete and doublons:
        nb_supprimes, espace = supprimer_doublons(doublons, confirmer=not args.yes)
        if nb_supprimes > 0:
            print(f"\n✅ {nb_supprimes} fichier(s) supprimé(s), {formater_taille(espace)} récupéré(s).")


if __name__ == "__main__":
    main()