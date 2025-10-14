# Assets - Logo Aiko

## 📋 Instructions

Pour ajouter le logo Aiko aux rapports générés :

1. **Placez votre logo** dans ce dossier avec le nom : `aiko_logo.png`
2. Le logo doit être au format PNG
3. Dimensions recommandées : 300x100 pixels (ratio 3:1)
4. Le logo apparaîtra en haut à droite du rapport Word généré

## 📁 Structure

```
/home/addeche/aiko/aikoGPT/assets/
└── aiko_logo.png  ← Votre logo ici
```

## ⚠️ Note

Si le logo n'est pas présent, le rapport sera quand même généré mais sans logo.

## 🎨 Format supporté

- **Format** : PNG (recommandé) ou JPG
- **Nom du fichier** : `aiko_logo.png`
- **Taille** : Pas de limite, mais une largeur d'environ 300-500px est idéale
- **Position** : Le logo sera automatiquement redimensionné à 1.5 pouces de largeur dans le rapport

## 🔧 Configuration personnalisée

Si vous souhaitez utiliser un chemin différent pour le logo, modifiez le fichier :
`/home/addeche/aiko/aikoGPT/utils/report_generator.py`

```python
# Ligne 25-27
self.logo_path = logo_path
if not logo_path:
    # Modifier ce chemin pour un emplacement personnalisé
    self.logo_path = "/home/addeche/aiko/aikoGPT/assets/aiko_logo.png"
```

