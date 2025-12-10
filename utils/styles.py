"""
Module de styles modernes pour le bot.
Contient les éléments de design, barres de progression, ASCII art.
"""
import discord
from typing import Optional
from enum import Enum


# ══════════════════════════════════════════════════════════════════════
# 🎨 PALETTE DE COULEURS MODERNE
# ══════════════════════════════════════════════════════════════════════

class Colors:
    """Palette de couleurs modernes."""
    # Couleurs principales
    PRIMARY = 0x5865F2      # Bleu Discord
    SECONDARY = 0x57F287    # Vert vif
    ACCENT = 0xFEE75C       # Jaune doré
    
    # Couleurs de statut
    SUCCESS = 0x57F287      # Vert succès
    ERROR = 0xED4245        # Rouge erreur
    WARNING = 0xFEE75C      # Jaune avertissement
    INFO = 0x5865F2         # Bleu info
    DANGER = 0xED4245       # Rouge danger (combat/boss)
    
    # Couleurs de rareté
    NORMAL = 0x95A5A6       # Gris
    RARE = 0x3498DB         # Bleu
    EPIC = 0x9B59B6         # Violet
    LEGENDARY = 0xF1C40F    # Or
    MYTHIC = 0xE74C3C       # Rouge
    
    # Couleurs spéciales
    GOLD = 0xFFD700         # Or pur
    PLATINUM = 0xE5E4E2     # Platine
    DIAMOND = 0xB9F2FF      # Diamant
    
    # Dégradés (couleur principale pour les features)
    COMBAT = 0xE74C3C       # Rouge combat
    LEVEL = 0x9B59B6        # Violet niveau
    SHOP = 0x2ECC71         # Vert boutique
    TRADE = 0xE67E22        # Orange trade
    CHEST = 0xF39C12        # Or coffre
    PET = 0xE91E63          # Rose pet
    EQUIPMENT = 0x607D8B    # Gris bleu équipement


# ══════════════════════════════════════════════════════════════════════
# ✨ EMOJIS MODERNES
# ══════════════════════════════════════════════════════════════════════

class Emojis:
    """Collection d'emojis pour l'interface."""
    # Status
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    
    # Navigation & Actions
    ARROW_RIGHT = "▸"
    ARROW_LEFT = "◂"
    ARROW_UP = "▴"
    ARROW_DOWN = "▾"
    DOT = "•"
    BULLET = "›"
    CHECK = "✓"
    CROSS = "✗"
    
    # Barres de progression
    BAR_FULL = "█"
    BAR_MID = "▓"
    BAR_LOW = "░"
    BAR_EMPTY = "░"
    
    # Barres de vie modernes
    HP_FULL_START = "▰"
    HP_FULL = "▰"
    HP_EMPTY = "▱"
    HP_FULL_END = "▰"
    
    # Économie
    COIN = "💰"
    GEM = "💎"
    CHEST = "🎁"
    SHOP = "🏪"
    INVENTORY = "🎒"
    TROPHY = "🏆"
    
    # Combat
    SWORD = "⚔️"
    SHIELD = "🛡️"
    HEART = "❤️"
    STAR = "⭐"
    FIRE = "🔥"
    SKULL = "💀"
    ATTACK = "⚔️"
    DEFENSE = "🛡️"
    SPEED = "💨"
    SKILL = "✨"
    
    # Stats
    ATK = "⚔️"
    DEF = "🛡️"
    HP = "❤️"
    SPD = "💨"
    XP = "✨"
    LVL = "📊"
    STATS = "📊"
    
    # Pets
    EGG = "🥚"
    PET = "🐾"
    GIFT = "🎁"
    
    # Raretés
    RARITY = {
        "NORMAL": "⬜",
        "RARE": "🟦",
        "EPIC": "🟪",
        "LEGENDARY": "🟨",
        "MYTHIC": "🟥"
    }


# ══════════════════════════════════════════════════════════════════════
# 📊 BARRES DE PROGRESSION
# ══════════════════════════════════════════════════════════════════════

def create_progress_bar(
    current: int, 
    maximum: int, 
    length: int = 10,
    filled_char: str = "▰",
    empty_char: str = "▱",
    show_percentage: bool = False
) -> str:
    """Crée une barre de progression moderne."""
    if maximum <= 0:
        percentage = 0
    else:
        percentage = min(100, int((current / maximum) * 100))
    
    filled = int((percentage / 100) * length)
    empty = length - filled
    
    bar = filled_char * filled + empty_char * empty
    
    if show_percentage:
        return f"`{bar}` {percentage}%"
    return f"`{bar}`"


def create_hp_bar(current: int, maximum: int, length: int = 12) -> str:
    """Crée une barre de vie avec couleurs."""
    if maximum <= 0:
        ratio = 0
    else:
        ratio = current / maximum
    
    filled = int(ratio * length)
    empty = length - filled
    
    # Choisir les caractères selon le ratio
    if ratio > 0.6:
        char = "🟩"
    elif ratio > 0.3:
        char = "🟨"
    else:
        char = "🟥"
    
    return char * filled + "⬛" * empty


def create_xp_bar(current: int, required: int, length: int = 15) -> str:
    """Crée une barre d'XP stylisée."""
    if required <= 0:
        percentage = 100
    else:
        percentage = min(100, int((current / required) * 100))
    
    filled = int((percentage / 100) * length)
    empty = length - filled
    
    bar = "▓" * filled + "░" * empty
    return f"`[{bar}]` **{percentage}%**"


def create_stat_bar(value: int, max_val: int = 100, length: int = 8) -> str:
    """Crée une mini barre pour les stats."""
    ratio = min(1, value / max_val) if max_val > 0 else 0
    filled = int(ratio * length)
    return "█" * filled + "░" * (length - filled)


# ══════════════════════════════════════════════════════════════════════
# 🎨 HEADERS ET BANNERS
# ══════════════════════════════════════════════════════════════════════

def create_header(title: str, emoji: str = "✦", width: int = 32) -> str:
    """Crée un header moderne."""
    padding = (width - len(title) - 4) // 2
    return (
        f"```ansi\n"
        f"\u001b[1;33m{'═' * width}\u001b[0m\n"
        f"\u001b[1;36m{' ' * padding}{emoji} {title} {emoji}\u001b[0m\n"
        f"\u001b[1;33m{'═' * width}\u001b[0m\n"
        f"```"
    )


def create_mini_header(title: str, emoji: str = "▸") -> str:
    """Crée un mini header."""
    return f"**{emoji} {title}**"


def create_separator(style: str = "thin") -> str:
    """Crée un séparateur."""
    if style == "thick":
        return "━" * 32
    elif style == "double":
        return "═" * 32
    elif style == "dots":
        return "• " * 16
    return "─" * 32


# ══════════════════════════════════════════════════════════════════════
# 📦 BOÎTES ET CADRES
# ══════════════════════════════════════════════════════════════════════

def create_box(content: str, title: Optional[str] = None, style: str = "rounded") -> str:
    """Crée une boîte autour du contenu."""
    lines = content.split('\n')
    max_len = max(len(line) for line in lines) if lines else 20
    
    if style == "rounded":
        top = f"╭{'─' * (max_len + 2)}╮"
        bottom = f"╰{'─' * (max_len + 2)}╯"
        side = "│"
    elif style == "double":
        top = f"╔{'═' * (max_len + 2)}╗"
        bottom = f"╚{'═' * (max_len + 2)}╝"
        side = "║"
    else:
        top = f"┌{'─' * (max_len + 2)}┐"
        bottom = f"└{'─' * (max_len + 2)}┘"
        side = "│"
    
    result = [top]
    if title:
        result.append(f"{side} {title:^{max_len}} {side}")
        result.append(f"├{'─' * (max_len + 2)}┤")
    
    for line in lines:
        result.append(f"{side} {line:<{max_len}} {side}")
    
    result.append(bottom)
    return '\n'.join(result)


def create_stat_display(label: str, value: str, emoji: str = "▸") -> str:
    """Affiche une stat de manière élégante."""
    return f"{emoji} **{label}**: `{value}`"


# ══════════════════════════════════════════════════════════════════════
# 🎮 AFFICHAGES SPÉCIAUX
# ══════════════════════════════════════════════════════════════════════

def create_level_display(level: int, xp: int, xp_required: int) -> str:
    """Crée un affichage de niveau moderne."""
    xp_bar = create_xp_bar(xp, xp_required)
    return (
        f"```ansi\n"
        f"\u001b[1;35m╔══════════════════════════════╗\u001b[0m\n"
        f"\u001b[1;35m║\u001b[0m      ⭐ \u001b[1;33mNIVEAU {level:>3}\u001b[0m ⭐       \u001b[1;35m║\u001b[0m\n"
        f"\u001b[1;35m╚══════════════════════════════╝\u001b[0m\n"
        f"```"
    )


def create_combat_stats_display(hp: int, max_hp: int, atk: int, defense: int, spd: int) -> str:
    """Crée un affichage des stats de combat."""
    hp_bar = create_hp_bar(hp, max_hp, 10)
    return (
        f"❤️ **PV**: {hp_bar} `{hp}/{max_hp}`\n"
        f"⚔️ **ATK**: `{atk}` {create_stat_bar(atk, 150, 6)}\n"
        f"🛡️ **DEF**: `{defense}` {create_stat_bar(defense, 100, 6)}\n"
        f"💨 **VIT**: `{spd}` {create_stat_bar(spd, 100, 6)}"
    )


def create_reward_display(xp: int, coins: int, items: list = None) -> str:
    """Crée un affichage des récompenses."""
    text = "```diff\n"
    text += f"+ {xp:,} XP\n"
    text += f"+ {coins:,} pièces\n"
    if items:
        for item in items:
            text += f"+ {item}\n"
    text += "```"
    return text


def create_rarity_indicator(rarity_name: str) -> str:
    """Crée un indicateur de rareté visuel."""
    indicators = {
        "NORMAL": "░░░░░",
        "RARE": "▒▒░░░",
        "EPIC": "▓▓▒░░",
        "LEGENDARY": "█▓▓▒░",
        "MYTHIC": "█████"
    }
    return f"`{indicators.get(rarity_name, '░░░░░')}`"


# ══════════════════════════════════════════════════════════════════════
# 🔧 UTILITAIRES
# ══════════════════════════════════════════════════════════════════════

def format_number(n: int) -> str:
    """Formate un nombre avec séparateurs."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


def create_embed_footer(tip: str = None) -> str:
    """Crée un footer avec astuce."""
    if tip:
        return f"💡 {tip}"
    return "Bot Économie • discord.gg/server"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Tronque le texte si trop long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


# ══════════════════════════════════════════════════════════════════════
# 🎨 THÈMES D'EMBED
# ══════════════════════════════════════════════════════════════════════

class EmbedTheme:
    """Thèmes prédéfinis pour les embeds."""
    
    @staticmethod
    def combat(title: str, description: str = None) -> discord.Embed:
        """Embed style combat."""
        embed = discord.Embed(title=title, color=Colors.COMBAT)
        if description:
            embed.description = description
        return embed
    
    @staticmethod
    def success(title: str, description: str = None) -> discord.Embed:
        """Embed succès."""
        embed = discord.Embed(title=f"✅ {title}", color=Colors.SUCCESS)
        if description:
            embed.description = description
        return embed
    
    @staticmethod
    def error(title: str, description: str = None) -> discord.Embed:
        """Embed erreur."""
        embed = discord.Embed(title=f"❌ {title}", color=Colors.ERROR)
        if description:
            embed.description = description
        return embed
    
    @staticmethod
    def warning(title: str, description: str = None) -> discord.Embed:
        """Embed avertissement."""
        embed = discord.Embed(title=f"⚠️ {title}", color=Colors.WARNING)
        if description:
            embed.description = description
        return embed
    
    @staticmethod
    def info(title: str, description: str = None) -> discord.Embed:
        """Embed information."""
        embed = discord.Embed(title=title, color=Colors.INFO)
        if description:
            embed.description = description
        return embed
    
    @staticmethod
    def chest(title: str, description: str = None) -> discord.Embed:
        """Embed coffre."""
        embed = discord.Embed(title=title, color=Colors.CHEST)
        if description:
            embed.description = description
        return embed
    
    @staticmethod
    def level_up(level: int) -> discord.Embed:
        """Embed level up."""
        embed = discord.Embed(
            title="🎊 LEVEL UP !",
            description=f"Tu es maintenant **niveau {level}** !",
            color=Colors.LEVEL
        )
        return embed
    
    @staticmethod
    def victory() -> discord.Embed:
        """Embed victoire."""
        return discord.Embed(
            title="🎉 VICTOIRE !",
            color=Colors.SUCCESS
        )
    
    @staticmethod
    def defeat() -> discord.Embed:
        """Embed défaite."""
        return discord.Embed(
            title="💀 DÉFAITE...",
            color=0x7F8C8D
        )


# ══════════════════════════════════════════════════════════════════════
# 🎨 ALIAS POUR COMPATIBILITÉ (ModernTheme / ModernEmbed)
# ══════════════════════════════════════════════════════════════════════

class ModernTheme:
    """Palette de couleurs modernes (alias de Colors)."""
    PRIMARY = Colors.PRIMARY
    SECONDARY = Colors.SECONDARY
    SUCCESS = Colors.SUCCESS
    ERROR = Colors.ERROR
    WARNING = Colors.WARNING
    INFO = Colors.INFO
    LEGENDARY = Colors.LEGENDARY
    MYTHIC = Colors.MYTHIC
    GOLD = Colors.GOLD
    COMBAT = Colors.COMBAT
    CHEST = Colors.CHEST
    PET = Colors.PET
    EQUIPMENT = Colors.EQUIPMENT


class ModernEmbed:
    """Factory pour créer des embeds modernes."""
    
    @staticmethod
    def create(
        title: str,
        description: str = None,
        style: str = "info",
        thumbnail: str = None,
        footer: str = None
    ) -> discord.Embed:
        """
        Crée un embed moderne avec le style spécifié.
        
        Args:
            title: Titre de l'embed
            description: Description de l'embed
            style: "success", "error", "warning", "info", "combat", "chest", "pet"
            thumbnail: URL de la miniature
            footer: Texte du footer
        """
        style_config = {
            "success": {"color": Colors.SUCCESS, "emoji": "✅"},
            "error": {"color": Colors.ERROR, "emoji": "❌"},
            "warning": {"color": Colors.WARNING, "emoji": "⚠️"},
            "info": {"color": Colors.INFO, "emoji": "ℹ️"},
            "combat": {"color": Colors.COMBAT, "emoji": "⚔️"},
            "chest": {"color": Colors.CHEST, "emoji": "🎁"},
            "pet": {"color": Colors.PET, "emoji": "🥚"},
            "legendary": {"color": Colors.LEGENDARY, "emoji": "⭐"},
            "mythic": {"color": Colors.MYTHIC, "emoji": "🔥"}
        }
        
        config = style_config.get(style, style_config["info"])
        
        embed = discord.Embed(
            title=title,
            color=config["color"]
        )
        
        if description:
            embed.description = description
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        if footer:
            embed.set_footer(text=footer)
        
        return embed
