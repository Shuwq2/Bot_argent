# 🎮 Royal Rush - Bot Discord Economy

Un bot Discord complet avec système d'économie, gacha, combat de boss, pets et équipement.

## ✨ Fonctionnalités

### 💰 Économie
- Système de pièces et inventaire
- Coffres avec différentes raretés (Normal → Mythique)
- Vente d'objets
- Boutique

### ⚔️ Combat
- Affrontez des boss avec différentes difficultés
- Système de skills équipables (max 4)
- Dégâts basés sur l'équipement et la rareté
- XP et niveaux

### 🛡️ Équipement
- 6 slots : Casque, Plastron, Jambières, Bottes, Arme, Accessoire
- Stats de combat : ATK, DEF, HP, SPEED
- Bonus économiques : +% OR, +% XP, +% DROP
- Multiplicateurs selon la rareté (MYTHIC = ×100)

### 🐾 Pets
- Œufs mystérieux à acheter
- Pets avec bonus de drop
- Système de rareté

### 🍖 Consommables
- Nourriture et potions pour se soigner
- Commande `/manger` pour restaurer les PV

## 📊 Raretés

| Rareté | Taux de Drop | Emoji | Multiplicateur Combat |
|--------|--------------|-------|----------------------|
| Normal | 70% | ⬜ | ×2 |
| Rare | 20% | 🟦 | ×5 |
| Épique | 6.5% | 🟪 | ×15 |
| Légendaire | 2% | 🟨 | ×40 |
| Mythique | 1.5% | 🟥 | ×100 |

## 🚀 Installation

```bash
# Cloner le repo
git clone https://github.com/Shuwq2/Bot_argent.git
cd Bot_argent

# Créer l'environnement virtuel
python3 -m venv myenv
source myenv/bin/activate

# Installer les dépendances
pip install -r requirement.txt

# Configurer le token (créer un fichier .env)
echo "DISCORD_TOKEN=votre_token_ici" > .env

# Lancer le bot
python bot.py
```

## 📁 Structure du projet

```
Bot_argent/
├── bot.py              # Point d'entrée principal
├── cogs/               # Commandes Discord
│   ├── admin.py        # Commandes admin
│   ├── battle.py       # Système de combat
│   ├── chests.py       # Coffres et gacha
│   ├── equipment.py    # Gestion équipement
│   ├── inventory.py    # Inventaire et boutique
│   ├── pets.py         # Système de pets
│   ├── profile.py      # Profil joueur
│   └── trading.py      # Échanges
├── data/               # Données JSON
│   ├── bosses.json     # Configuration des boss
│   ├── items.json      # Tous les objets
│   ├── pets.json       # Configuration pets
│   ├── players.json    # Données joueurs
│   ├── sets.json       # Sets d'équipement
│   └── skills.json     # Compétences de combat
├── models/             # Classes de données
│   ├── player.py       # Classe Player
│   ├── item.py         # Classes Item et Rarity
│   ├── combat.py       # Logique de combat
│   └── chest.py        # Logique des coffres
├── services/           # Services
│   └── data_manager.py # Gestion des données
└── utils/              # Utilitaires
    ├── styles.py       # Couleurs et emojis
    └── constants.py    # Constantes
```

## 🎯 Commandes principales

| Commande | Description |
|----------|-------------|
| `/coffre` | Ouvre un coffre gratuit (cooldown) ou payant |
| `/inventaire` | Affiche ton inventaire |
| `/equipement` | Gère ton équipement |
| `/combat [boss]` | Combat un boss |
| `/manger [item]` | Consomme nourriture/potion |
| `/profil` | Affiche ton profil |
| `/boutique` | Affiche la boutique |
| `/vendre [item]` | Vend un objet |

## 🔧 Configuration

Les taux de drop se modifient dans `models/item.py` :

```python
class Rarity(Enum):
    NORMAL = ("Normal", 0.70, "⬜", 10)      # 70%
    RARE = ("Rare", 0.20, "🟦", 50)          # 20%
    EPIC = ("Epic", 0.065, "🟪", 200)        # 6.5%
    LEGENDARY = ("Légendaire", 0.02, "🟨", 1000)  # 2%
    MYTHIC = ("Mythique", 0.015, "🟥", 5000) # 1.5%
```

## 📝 License

MIT License

## 👤 Auteur

**Shuwq2** - [GitHub](https://github.com/Shuwq2)
