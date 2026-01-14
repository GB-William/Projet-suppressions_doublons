import sys

from fichier_utils import formater_taille


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

