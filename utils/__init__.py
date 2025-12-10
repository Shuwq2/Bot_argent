"""
Module utils pour les constantes et helpers partagés.
"""
from .constants import (
    RARITY_IMAGES,
    SUSPENSE_SEQUENCE,
    SUSPENSE_COLORS,
    GIFS,
    COLORS,
    EMOJIS
)

from .styles import (
    Colors, Emojis,
    create_progress_bar, create_hp_bar, create_xp_bar, create_stat_bar,
    create_header, create_mini_header, create_separator,
    create_box, create_stat_display,
    create_level_display, create_combat_stats_display, create_reward_display,
    create_rarity_indicator, format_number, create_embed_footer, truncate_text,
    EmbedTheme,
    ModernTheme, ModernEmbed
)

__all__ = [
    'RARITY_IMAGES',
    'SUSPENSE_SEQUENCE', 
    'SUSPENSE_COLORS',
    'GIFS',
    'COLORS',
    'EMOJIS',
    # New modern styles
    'Colors', 'Emojis',
    'create_progress_bar', 'create_hp_bar', 'create_xp_bar', 'create_stat_bar',
    'create_header', 'create_mini_header', 'create_separator',
    'create_box', 'create_stat_display',
    'create_level_display', 'create_combat_stats_display', 'create_reward_display',
    'create_rarity_indicator', 'format_number', 'create_embed_footer', 'truncate_text',
    'EmbedTheme',
    'ModernTheme', 'ModernEmbed'
]
