#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Programme pour supprimer les fichiers en double dans un ou plusieurs répertoires.
Parcourt récursivement tous les sous-répertoires et identifie les doublons par leur contenu (hash MD5).
"""

import sys
import argparse

from scan import parcourir_repertoires, identifier_doublons
from operations import afficher_doublons, supprimer_doublons
from fichier_utils import formater_taille


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

