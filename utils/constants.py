"""
Constantes partagées pour tous les cogs.
"""
from models import Rarity


# ══════════════════════════════════════════════════════════════
# 📸 IMAGES DE RARETÉ - Aurores boréales par couleur
# ══════════════════════════════════════════════════════════════

RARITY_IMAGES = {
    "normal": "https://i.imgur.com/5IGZUZk.png",      # Vert (Normal)
    "rare": "https://i.imgur.com/OX8kBYX.png",        # Bleu (Rare)
    "epic": "https://i.imgur.com/EZuex8X.png",        # Violet (Epic)
    "legendary": "https://i.imgur.com/V3Nw9TL.png",   # Or/Jaune (Legendary)
    "mythic": "https://i.imgur.com/lgNP9Cg.png",      # Rouge (Mythic)
}

# Séquence d'animation (couleurs qui défilent)
SUSPENSE_SEQUENCE = ["rare", "epic", "legendary", "mythic", "epic", "rare", "legendary", "epic"]

# Couleurs hex pour l'animation de suspense
SUSPENSE_COLORS = {
    "normal": 0x9e9e9e,    # Gris
    "rare": 0x3498db,      # Bleu
    "epic": 0x9b59b6,      # Violet
    "legendary": 0xf1c40f, # Or
    "mythic": 0xe74c3c,    # Rouge
}

# ══════════════════════════════════════════════════════════════
# 📸 GIFS PLACEHOLDER
# ══════════════════════════════════════════════════════════════

GIFS = {
    "chest_opening": "REMPLACE_PAR_TON_GIF",
    "chest_normal": "REMPLACE_PAR_TON_GIF",
    "chest_rare": "REMPLACE_PAR_TON_GIF",
    "chest_epic": "REMPLACE_PAR_TON_GIF",
    "chest_legendary": "REMPLACE_PAR_TON_GIF",
    "chest_mythic": "REMPLACE_PAR_TON_GIF",
    "coins": "REMPLACE_PAR_TON_GIF",
    "sell": "REMPLACE_PAR_TON_GIF",
    "shop": "REMPLACE_PAR_TON_GIF",
    "profile": "REMPLACE_PAR_TON_GIF",
    "inventory": "REMPLACE_PAR_TON_GIF",
    "leaderboard": "REMPLACE_PAR_TON_GIF",
    "trade_pending": "REMPLACE_PAR_TON_GIF",
    "trade_success": "REMPLACE_PAR_TON_GIF",
    "trade_cancel": "REMPLACE_PAR_TON_GIF",
    "error": "REMPLACE_PAR_TON_GIF",
    "success": "REMPLACE_PAR_TON_GIF",
    "empty": "REMPLACE_PAR_TON_GIF",
}

# ══════════════════════════════════════════════════════════════
# 🎨 COULEURS PAR RARETÉ
# ══════════════════════════════════════════════════════════════

COLORS = {
    Rarity.NORMAL: 0x9e9e9e,      # Gris
    Rarity.RARE: 0x3498db,        # Bleu
    Rarity.EPIC: 0x9b59b6,        # Violet
    Rarity.LEGENDARY: 0xf1c40f,   # Or
    Rarity.MYTHIC: 0xe74c3c,      # Rouge
    "success": 0x2ecc71,          # Vert
    "error": 0xe74c3c,            # Rouge
    "info": 0x3498db,             # Bleu
    "warning": 0xf39c12,          # Orange
    "trade": 0x1abc9c,            # Turquoise
    "shop": 0xe91e63,             # Rose
    "profile": 0x9b59b6,          # Violet
}

# ══════════════════════════════════════════════════════════════
# 🎭 EMOJIS DÉCORATIFS
# ══════════════════════════════════════════════════════════════

EMOJIS = {
    "coin": "💰",
    "gem": "💎",
    "chest": "🎁",
    "inventory": "🎒",
    "profile": "👤",
    "trade": "🔄",
    "shop": "🏪",
    "star": "⭐",
    "fire": "🔥",
    "sparkle": "✨",
    "check": "✅",
    "cross": "❌",
    "arrow": "➤",
    "crown": "👑",
    "trophy": "🏆",
    "egg": "🥚",
    "pet": "🐾",
    "shield": "🛡️",
}
