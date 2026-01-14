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
   