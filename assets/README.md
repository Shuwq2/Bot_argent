# 🎨 Images de Rareté - Aurores Boréales

Place tes images d'aurore boréale ici et héberge-les sur un service comme :
- **Discord** : Upload l'image dans un serveur, clic droit → Copier le lien
- **Imgur** : https://imgur.com/upload
- **Catbox** : https://catbox.moe

## Images requises

| Fichier | Couleur | Rareté |
|---------|---------|--------|
| `normal.png` | Gris/Blanc | Normal ⬜ |
| `rare.png` | Bleu | Rare 🟦 |
| `epic.png` | Violet | Epic 🟪 |
| `legendary.png` | Or/Jaune | Légendaire 🟨 |
| `mythic.png` | Rouge | Mythique 🟥 |

## Comment configurer

Une fois tes images hébergées, modifie `cogs/economy.py` :

```python
RARITY_IMAGES = {
    "normal": "https://ton-lien.com/normal.png",
    "rare": "https://ton-lien.com/rare.png",        # Image bleue
    "epic": "https://ton-lien.com/epic.png",        # Image violette
    "legendary": "https://ton-lien.com/legendary.png", # Image dorée
    "mythic": "https://ton-lien.com/mythic.png",    # Image rouge
}
```

## Tes images actuelles

D'après les fichiers fournis :
- 🟢 Vert → Non utilisé (ou pour un futur usage)
- 🟣 Violet → Epic
- 🟡 Or/Jaune → Legendary  
- 🔴 Rouge → Mythic
- 🔵 Bleu → Rare
