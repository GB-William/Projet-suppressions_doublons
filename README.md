# Suppression de fichiers en double

Programme Python pour identifier et supprimer les fichiers en double dans un ou plusieurs répertoires, y compris les sous-répertoires.

## Fonctionnalités

- ✅ Parcourt récursivement un ou plusieurs répertoires
- ✅ Identifie les doublons par leur contenu (hash MD5)
- ✅ Affiche un résumé détaillé des doublons trouvés
- ✅ Calcule l'espace disque qui peut être récupéré
- ✅ Option de confirmation avant suppression
- ✅ Mode "dry-run" pour voir les doublons sans les supprimer

## Utilisation

### Syntaxe de base

```bash
python supprimer_doublons.py <répertoire1> [répertoire2] [répertoire3] ...
```

### Exemples

**Analyser un seul répertoire:**
```bash
python supprimer_doublons.py C:\MesDocuments
```

**Analyser plusieurs répertoires:**
```bash
python supprimer_doublons.py C:\Rep1 C:\Rep2 C:\Rep3
```

**Supprimer sans demander de confirmation:**
```bash
python supprimer_doublons.py C:\MesDocuments --no-confirm
```

**Voir les doublons sans les supprimer (mode test):**
```bash
python supprimer_doublons.py C:\MesDocuments --dry-run
```

## Options

- `--no-confirm` : Supprime les doublons sans demander de confirmation
- `--dry-run` : Affiche les doublons trouvés sans les supprimer

## Comment ça fonctionne

1. Le programme parcourt récursivement tous les fichiers dans les répertoires spécifiés
2. Pour chaque fichier, il calcule un hash MD5 de son contenu
3. Les fichiers avec le même hash sont identifiés comme doublons
4. Le premier fichier de chaque groupe est conservé, les autres sont supprimés
5. Un résumé affiche le nombre de fichiers supprimés et l'espace récupéré

## Notes importantes

- ⚠️ **Attention** : La suppression est définitive. Utilisez `--dry-run` d'abord pour voir ce qui sera supprimé
- Le programme conserve toujours le premier fichier trouvé dans chaque groupe de doublons
- Les fichiers sont comparés par leur contenu, pas seulement par leur nom

## Prérequis

- Python 3.6 ou supérieur
- Aucune dépendance externe requise (utilise uniquement la bibliothèque standard)

