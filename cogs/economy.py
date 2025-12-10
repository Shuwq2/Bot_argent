"""
Cog gérant l'économie du bot : coffres, inventaire, vente, trade.
Design amélioré avec animations et système d'échange.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict
import asyncio
from datetime import datetime, timedelta

from models import Chest, Rarity
from services import DataManager


class Economy(commands.Cog):
    """Cog pour le système d'économie et de collection."""

    # ══════════════════════════════════════════════════════════════
    # 📸 IMAGES DE RARETÉ - Aurores boréales par couleur
    # ══════════════════════════════════════════════════════════════
    
    # Images locales hébergées (tu peux les uploader sur Discord ou un CDN)
    RARITY_IMAGES = {
        "normal": "https://i.imgur.com/placeholder_grey.png",      # Gris/Blanc
        "rare": "https://i.imgur.com/placeholder_blue.png",        # Bleu - ton image bleue
        "epic": "https://i.imgur.com/placeholder_purple.png",      # Violet - ton image violette  
        "legendary": "https://i.imgur.com/placeholder_gold.png",   # Or/Jaune - ton image dorée
        "mythic": "https://i.imgur.com/placeholder_red.png",       # Rouge - ton image rouge
    }
    
    # Séquence d'animation (couleurs qui défilent)
    SUSPENSE_SEQUENCE = ["rare", "epic", "legendary", "mythic", "epic", "rare", "legendary", "epic"]
    
    GIFS = {
        # Ouverture de coffre
        "chest_opening": "REMPLACE_PAR_TON_GIF",  # Animation d'ouverture
        "chest_normal": "REMPLACE_PAR_TON_GIF",   # Révélation Normal
        "chest_rare": "REMPLACE_PAR_TON_GIF",     # Révélation Rare
        "chest_epic": "REMPLACE_PAR_TON_GIF",     # Révélation Epic
        "chest_legendary": "REMPLACE_PAR_TON_GIF", # Révélation Légendaire
        "chest_mythic": "REMPLACE_PAR_TON_GIF",   # Révélation Mythique
        
        # Économie
        "coins": "REMPLACE_PAR_TON_GIF",          # Animation pièces
        "sell": "REMPLACE_PAR_TON_GIF",           # Animation vente
        "shop": "REMPLACE_PAR_TON_GIF",           # Animation boutique
        
        # Profil et stats
        "profile": "REMPLACE_PAR_TON_GIF",        # Animation profil
        "inventory": "REMPLACE_PAR_TON_GIF",      # Animation inventaire
        "leaderboard": "REMPLACE_PAR_TON_GIF",    # Animation classement
        
        # Trade
        "trade_pending": "REMPLACE_PAR_TON_GIF",  # Attente de trade
        "trade_success": "REMPLACE_PAR_TON_GIF",  # Trade réussi
        "trade_cancel": "REMPLACE_PAR_TON_GIF",   # Trade annulé
        
        # Erreurs et succès
        "error": "REMPLACE_PAR_TON_GIF",          # Animation erreur
        "success": "REMPLACE_PAR_TON_GIF",        # Animation succès
        "empty": "REMPLACE_PAR_TON_GIF",          # Inventaire vide
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
    }

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager
        self.chest = Chest(self.data.get_all_items())
        self.pending_trades: Dict[int, dict] = {}  # user_id -> trade_info

    # ══════════════════════════════════════════════════════════════
    # 🎁 COMMANDE COFFRE
    # ══════════════════════════════════════════════════════════════

    # Couleurs hex pour l'animation
    SUSPENSE_COLORS = {
        "normal": 0x9e9e9e,    # Gris
        "rare": 0x3498db,      # Bleu
        "epic": 0x9b59b6,      # Violet
        "legendary": 0xf1c40f, # Or
        "mythic": 0xe74c3c,    # Rouge
    }

    @app_commands.command(name="coffre", description="🎁 Ouvre un coffre mystérieux !")
    @app_commands.describe(payer="💎 Payer 3500 pièces pour un coffre bonus")
    async def open_chest(self, interaction: discord.Interaction, payer: Optional[bool] = False):
        """Ouvre un coffre avec animation de suspense."""
        player = self.data.get_player(interaction.user.id)
        
        # Vérifications
        if not player.can_open_free_chest() and not payer:
            embed = self._create_error_embed(
                "🚫 Limite Journalière Atteinte",
                f"Tu as ouvert **{player.MAX_DAILY_CHESTS}/{player.MAX_DAILY_CHESTS}** coffres aujourd'hui.\n\n"
                f"╭─────────────────────────╮\n"
                f"│ {self.EMOJIS['coin']} Solde: **{player.coins:,}**\n"
                f"│ {self.EMOJIS['gem']} Coût: **{player.CHEST_COST:,}**\n"
                f"╰─────────────────────────╯\n\n"
                f"➤ `/coffre payer:True` pour acheter\n"
                f"➤ Reviens demain pour 50 coffres gratuits !"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if payer and not player.can_open_free_chest():
            if not player.can_afford_chest():
                embed = self._create_error_embed(
                    "💸 Fonds Insuffisants",
                    f"```diff\n"
                    f"- Requis:  {player.CHEST_COST:,} 💰\n"
                    f"- Solde:   {player.coins:,} 💰\n"
                    f"- Manque:  {player.CHEST_COST - player.coins:,} 💰\n"
                    f"```\n"
                    f"💡 Vends des objets avec `/vendre` !"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Logique d'ouverture (avant l'animation pour déterminer le résultat)
        success = player.open_chest(paid=payer and not player.can_open_free_chest())
        if not success:
            await interaction.response.send_message(embed=self._create_error_embed("Erreur", "Impossible d'ouvrir le coffre."))
            return

        # Calcul du bonus de drop (pet + sets)
        drop_bonus = self.data.calculate_total_drop_bonus(player)
        item = self.chest.open(drop_bonus)
        if not item:
            await interaction.response.send_message(embed=self._create_error_embed("Erreur", "Aucun objet disponible."))
            return

        player.add_item(item.item_id)
        self.data.save_player(player)

        # ═══ ANIMATION DE SUSPENSE ═══
        # Séquence de raretés qui défilent (plus de suspense pour les raretés hautes)
        rarity_name = item.rarity.name.lower()
        
        # Premier embed d'ouverture
        opening_embed = discord.Embed(
            title=f"{self.EMOJIS['sparkle']} Ouverture du Coffre... {self.EMOJIS['sparkle']}",
            description="```\n✨ Le coffre s'illumine... ✨\n```",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=opening_embed)
        await asyncio.sleep(0.8)

        # Animation de suspense - défilement des couleurs
        suspense_sequence = ["rare", "epic", "legendary", "mythic", "legendary", "epic", "rare", "epic", "legendary"]
        
        for i, rarity_key in enumerate(suspense_sequence):
            # Ralentir progressivement
            delay = 0.15 + (i * 0.05)
            
            suspense_embed = discord.Embed(
                title="🎲 Tirage en cours...",
                description=f"```\n{'▓' * (i + 1)}{'░' * (len(suspense_sequence) - i - 1)}\n```",
                color=self.SUSPENSE_COLORS.get(rarity_key, 0xFFFFFF)
            )
            
            # Ajouter l'image de la rareté si disponible
            if self.RARITY_IMAGES.get(rarity_key) and "placeholder" not in self.RARITY_IMAGES[rarity_key]:
                suspense_embed.set_image(url=self.RARITY_IMAGES[rarity_key])
            
            await interaction.edit_original_response(embed=suspense_embed)
            await asyncio.sleep(delay)

        # Pause dramatique avant la révélation
        await asyncio.sleep(0.5)

        # ═══ RÉVÉLATION FINALE ═══
        reveal_embed = discord.Embed(
            title=self._get_reveal_title(item.rarity),
            description=f"```\n{'⭐' * 10}\n```",
            color=self.COLORS.get(item.rarity, 0x9e9e9e)
        )
        
        # Image finale de la vraie rareté
        if self.RARITY_IMAGES.get(rarity_name) and "placeholder" not in self.RARITY_IMAGES[rarity_name]:
            reveal_embed.set_image(url=self.RARITY_IMAGES[rarity_name])
        
        await interaction.edit_original_response(embed=reveal_embed)
        await asyncio.sleep(1.2)

        # ═══ AFFICHAGE FINAL DE L'ITEM ═══
        final_embed = self._create_item_reveal_embed(item, player)
        await interaction.edit_original_response(embed=final_embed)

    def _create_chest_art(self) -> str:
        """Art ASCII du coffre."""
        return (
            "```\n"
            "    ╔═══════════════════════╗\n"
            "    ║  ┌─────────────────┐  ║\n"
            "    ║  │  ▄▄▄▄▄▄▄▄▄▄▄▄▄  │  ║\n"
            "    ║  │  █████████████  │  ║\n"
            "    ║  │  █▓▓▓▓▓▓▓▓▓▓▓█  │  ║\n"
            "    ║  │  █▓▓▓ 🔒 ▓▓▓█  │  ║\n"
            "    ║  │  █▓▓▓▓▓▓▓▓▓▓▓█  │  ║\n"
            "    ║  │  █████████████  │  ║\n"
            "    ║  └─────────────────┘  ║\n"
            "    ╚═══════════════════════╝\n"
            "```"
        )

    def _get_reveal_title(self, rarity: Rarity) -> str:
        """Titre selon la rareté."""
        titles = {
            Rarity.NORMAL: "📦 Un objet apparaît...",
            Rarity.RARE: "💎 Quelque chose de RARE brille !",
            Rarity.EPIC: "🌟 EPIC ! Une aura violette émane !",
            Rarity.LEGENDARY: "⚡ LÉGENDAIRE !! Lumière dorée !!",
            Rarity.MYTHIC: "🔥🔥 MYTHIQUE !!! INCROYABLE !!! 🔥🔥"
        }
        return titles.get(rarity, "📦 Un objet apparaît...")

    def _create_item_reveal_embed(self, item, player) -> discord.Embed:
        """Embed de révélation d'objet."""
        color = self.COLORS.get(item.rarity, 0x9e9e9e)
        
        # Titre stylisé selon rareté
        rarity_decorations = {
            Rarity.NORMAL: ("", ""),
            Rarity.RARE: ("💎 ", " 💎"),
            Rarity.EPIC: ("🌟 ", " 🌟"),
            Rarity.LEGENDARY: ("⭐ ", " ⭐"),
            Rarity.MYTHIC: ("🔥 ", " 🔥"),
        }
        prefix, suffix = rarity_decorations.get(item.rarity, ("", ""))
        
        embed = discord.Embed(
            title=f"{prefix}{item.name}{suffix}",
            color=color
        )

        # Info box stylisée
        embed.add_field(
            name="╔══ 📋 Informations ══╗",
            value=(
                f"```yml\n"
                f"Rareté: {item.rarity.display_name}\n"
                f"Valeur: {item.value:,} pièces\n"
                f"Catégorie: {item.category}\n"
                f"```"
            ),
            inline=True
        )

        embed.add_field(
            name="╔══ 📊 Stats ══╗",
            value=(
                f"```yml\n"
                f"Coffres: {player.get_remaining_free_chests()}/50\n"
                f"Solde: {player.coins:,}\n"
                f"Total: {player.total_chests_opened}\n"
                f"```"
            ),
            inline=True
        )

        embed.add_field(
            name="📖 Description",
            value=f"*« {item.description} »*",
            inline=False
        )

        # Barre de rareté visuelle
        embed.add_field(
            name="✨ Rareté",
            value=self._create_rarity_bar(item.rarity),
            inline=False
        )

        embed.set_footer(text=f"{item.rarity.emoji} {item.rarity.display_name} • /inventaire pour voir ta collection")
        
        return embed

    def _create_rarity_bar(self, rarity: Rarity) -> str:
        """Crée une barre visuelle de rareté."""
        levels = {
            Rarity.NORMAL: 1,
            Rarity.RARE: 2,
            Rarity.EPIC: 3,
            Rarity.LEGENDARY: 4,
            Rarity.MYTHIC: 5
        }
        level = levels.get(rarity, 1)
        filled = "◆" * level
        empty = "◇" * (5 - level)
        return f"`[{filled}{empty}]` {rarity.emoji} {rarity.display_name}"

    # ══════════════════════════════════════════════════════════════
    # � COMMANDE COFFRES MULTIPLES
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="coffres", description="🎁 Ouvre plusieurs coffres d'un coup !")
    @app_commands.describe(
        nombre="Nombre de coffres à ouvrir",
        payer="Payer 3500 pièces par coffre au-delà de la limite gratuite"
    )
    @app_commands.choices(nombre=[
        app_commands.Choice(name="🎁 10 coffres", value=10),
        app_commands.Choice(name="🎁 25 coffres", value=25),
        app_commands.Choice(name="🎁 30 coffres", value=30),
        app_commands.Choice(name="🎁 45 coffres", value=45),
        app_commands.Choice(name="🎁 50 coffres", value=50),
    ])
    async def open_multiple_chests(
        self, 
        interaction: discord.Interaction, 
        nombre: int,
        payer: Optional[bool] = False
    ):
        """Ouvre plusieurs coffres avec résumé."""
        player = self.data.get_player(interaction.user.id)
        
        # Calculer combien on peut ouvrir
        free_remaining = player.get_remaining_free_chests()
        
        if not payer:
            # Mode gratuit uniquement
            if free_remaining == 0:
                embed = self._create_error_embed(
                    "🚫 Limite Journalière Atteinte",
                    f"Tu as utilisé tous tes coffres gratuits aujourd'hui.\n\n"
                    f"💡 Utilise `/coffres nombre:X payer:True` pour acheter des coffres.\n"
                    f"💰 Coût: **{player.CHEST_COST:,}** pièces/coffre"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            chests_to_open = min(nombre, free_remaining)
            cost = 0
        else:
            # Mode payant autorisé
            free_to_use = min(nombre, free_remaining)
            paid_to_use = nombre - free_to_use
            cost = paid_to_use * player.CHEST_COST
            
            if cost > player.coins:
                max_affordable = player.coins // player.CHEST_COST
                embed = self._create_error_embed(
                    "💸 Fonds Insuffisants",
                    f"```diff\n"
                    f"- Coffres demandés: {nombre}\n"
                    f"- Coffres gratuits restants: {free_remaining}\n"
                    f"- Coffres à payer: {paid_to_use}\n"
                    f"- Coût total: {cost:,} 💰\n"
                    f"- Ton solde: {player.coins:,} 💰\n"
                    f"```\n"
                    f"💡 Tu peux ouvrir max **{free_remaining + max_affordable}** coffres."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            chests_to_open = nombre

        # Animation d'ouverture
        opening_embed = discord.Embed(
            title=f"🎁 Ouverture de {chests_to_open} Coffres...",
            description=(
                f"```\n"
                f"╔═══════════════════════════════════╗\n"
                f"║     📦📦📦 OUVERTURE EN COURS 📦📦📦   ║\n"
                f"║                                    ║\n"
                f"║        Chargement...               ║\n"
                f"╚═══════════════════════════════════╝\n"
                f"```"
            ),
            color=0xFFD700
        )
        if self.GIFS["chest_opening"] != "REMPLACE_PAR_TON_GIF":
            opening_embed.set_thumbnail(url=self.GIFS["chest_opening"])

        await interaction.response.send_message(embed=opening_embed)
        await asyncio.sleep(2)

        # Ouvrir les coffres et collecter les items
        items_obtained = []
        rarity_counts = {r: 0 for r in Rarity}
        total_value = 0
        
        # Calcul du bonus de drop (pet + sets)
        drop_bonus = self.data.calculate_total_drop_bonus(player)

        for i in range(chests_to_open):
            # Déterminer si gratuit ou payant
            if player.can_open_free_chest():
                success = player.open_chest(paid=False)
            else:
                success = player.open_chest(paid=True)
            
            if success:
                item = self.chest.open(drop_bonus)
                if item:
                    player.add_item(item.item_id)
                    items_obtained.append(item)
                    rarity_counts[item.rarity] += 1
                    total_value += item.value

        self.data.save_player(player)

        # Créer le résumé
        result_embed = discord.Embed(
            title=f"🎉 {len(items_obtained)} Coffres Ouverts !",
            color=0x2ecc71
        )

        # Résumé par rareté
        rarity_summary = ""
        for rarity in [Rarity.MYTHIC, Rarity.LEGENDARY, Rarity.EPIC, Rarity.RARE, Rarity.NORMAL]:
            count = rarity_counts[rarity]
            if count > 0:
                rarity_summary += f"{rarity.emoji} **{rarity.display_name}**: `{count}`\n"

        result_embed.add_field(
            name="📊 Résumé par Rareté",
            value=rarity_summary or "Aucun objet",
            inline=True
        )

        # Stats
        result_embed.add_field(
            name="💰 Valeur Totale",
            value=f"`{total_value:,}` pièces",
            inline=True
        )

        if cost > 0:
            result_embed.add_field(
                name="💳 Coût",
                value=f"`{cost:,}` pièces",
                inline=True
            )

        # Meilleurs drops (top 5)
        if items_obtained:
            # Trier par valeur
            best_items = sorted(items_obtained, key=lambda x: x.value, reverse=True)[:5]
            best_text = ""
            for item in best_items:
                best_text += f"{item.rarity.emoji} **{item.name}** - {item.value:,}💰\n"
            
            result_embed.add_field(
                name="🏆 Meilleurs Drops",
                value=best_text,
                inline=False
            )

        # Stats joueur
        result_embed.add_field(
            name="📈 Tes Stats",
            value=(
                f"```yml\n"
                f"Coffres restants: {player.get_remaining_free_chests()}/50\n"
                f"Solde: {player.coins:,}\n"
                f"Total ouverts: {player.total_chests_opened}\n"
                f"```"
            ),
            inline=False
        )

        # Check pour objets rares
        mythic_count = rarity_counts[Rarity.MYTHIC]
        legendary_count = rarity_counts[Rarity.LEGENDARY]
        
        if mythic_count > 0:
            result_embed.set_footer(text=f"🔥 INCROYABLE ! Tu as obtenu {mythic_count} MYTHIQUE(S) ! 🔥")
        elif legendary_count > 0:
            result_embed.set_footer(text=f"⭐ Bravo ! {legendary_count} LÉGENDAIRE(S) obtenu(s) ! ⭐")
        else:
            result_embed.set_footer(text="💡 /inventaire pour voir ta collection")

        await interaction.edit_original_response(embed=result_embed)

    # ══════════════════════════════════════════════════════════════
    # �🎒 COMMANDE INVENTAIRE
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="inventaire", description="🎒 Affiche ta collection")
    @app_commands.describe(page="Page de l'inventaire")
    async def inventory(self, interaction: discord.Interaction, page: Optional[int] = 1):
        """Affiche l'inventaire stylisé."""
        player = self.data.get_player(interaction.user.id)
        
        if not player.inventory:
            embed = discord.Embed(
                title=f"{self.EMOJIS['inventory']} Inventaire de {interaction.user.display_name}",
                description=self._create_empty_inventory_art(),
                color=self.COLORS["info"]
            )
            embed.add_field(
                name="💡 Astuce",
                value="Utilise `/coffre` pour obtenir des objets !",
                inline=False
            )
            if self.GIFS["empty"] != "REMPLACE_PAR_TON_GIF":
                embed.set_thumbnail(url=self.GIFS["empty"])
            await interaction.response.send_message(embed=embed)
            return

        # Préparer les données
        items_list = []
        total_value = 0
        rarity_counts = {r: 0 for r in Rarity}
        
        for item_id, quantity in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                items_list.append((item, quantity))
                total_value += item.value * quantity
                rarity_counts[item.rarity] += quantity

        # Trier par rareté
        rarity_order = {Rarity.MYTHIC: 0, Rarity.LEGENDARY: 1, Rarity.EPIC: 2, Rarity.RARE: 3, Rarity.NORMAL: 4}
        items_list.sort(key=lambda x: rarity_order.get(x[0].rarity, 5))

        # Pagination
        items_per_page = 8
        total_pages = max(1, (len(items_list) + items_per_page - 1) // items_per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * items_per_page
        page_items = items_list[start_idx:start_idx + items_per_page]

        embed = discord.Embed(
            title=f"{self.EMOJIS['inventory']} Inventaire de {interaction.user.display_name}",
            color=self.COLORS["info"]
        )

        # Liste des objets
        items_text = ""
        for item, qty in page_items:
            items_text += f"{item.rarity.emoji} **{item.name}** `×{qty}`\n"
            items_text += f"╰➤ {item.value * qty:,} {self.EMOJIS['coin']}\n"

        embed.add_field(
            name=f"📦 Objets ({len(items_list)} uniques)",
            value=items_text or "Aucun objet",
            inline=False
        )

        # Stats par rareté
        rarity_text = ""
        for rarity in Rarity:
            if rarity_counts[rarity] > 0:
                rarity_text += f"{rarity.emoji} `{rarity_counts[rarity]:>3}` "
        
        embed.add_field(
            name="📊 Par Rareté",
            value=rarity_text or "Aucun",
            inline=True
        )

        # Résumé
        embed.add_field(
            name=f"{self.EMOJIS['coin']} Valeur",
            value=f"`{total_value:,}` pièces",
            inline=True
        )

        embed.add_field(
            name="💰 Solde",
            value=f"`{player.coins:,}` pièces",
            inline=True
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"📄 Page {page}/{total_pages} • /inventaire page:{page + 1 if page < total_pages else 1}")

        if self.GIFS["inventory"] != "REMPLACE_PAR_TON_GIF":
            embed.set_image(url=self.GIFS["inventory"])

        await interaction.response.send_message(embed=embed)

    def _create_empty_inventory_art(self) -> str:
        """Art ASCII inventaire vide."""
        return (
            "```\n"
            "  ╔═══════════════════════════╗\n"
            "  ║                           ║\n"
            "  ║      📦 INVENTAIRE        ║\n"
            "  ║          VIDE             ║\n"
            "  ║                           ║\n"
            "  ║      ┌───────────┐        ║\n"
            "  ║      │  (vide)   │        ║\n"
            "  ║      └───────────┘        ║\n"
            "  ║                           ║\n"
            "  ╚═══════════════════════════╝\n"
            "```"
        )

    # ══════════════════════════════════════════════════════════════
    # 💸 COMMANDE VENDRE
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="vendre", description="💸 Vend un objet")
    @app_commands.describe(objet="Nom de l'objet", quantite="Quantité à vendre")
    async def sell(self, interaction: discord.Interaction, objet: str, quantite: Optional[int] = 1):
        """Vend un objet avec animation."""
        player = self.data.get_player(interaction.user.id)
        
        # Rechercher l'objet
        item = None
        for item_id in player.inventory:
            potential = self.data.get_item(item_id)
            if potential and potential.name.lower() == objet.lower():
                item = potential
                break

        if not item:
            embed = self._create_error_embed(
                "❌ Objet Introuvable",
                f"L'objet **{objet}** n'est pas dans ton inventaire.\n\n"
                f"💡 Utilise `/inventaire` pour voir tes objets."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        available = player.inventory.get(item.item_id, 0)
        if quantite <= 0 or quantite > available:
            embed = self._create_error_embed(
                "❌ Quantité Invalide",
                f"```diff\n"
                f"- Demandé: {quantite}×\n"
                f"+ Disponible: {available}×\n"
                f"```"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Effectuer la vente
        total = item.value * quantite
        old_balance = player.coins
        player.sell_item(item.item_id, item.value, quantite)
        self.data.save_player(player)

        embed = discord.Embed(
            title=f"{self.EMOJIS['check']} Vente Réussie !",
            color=self.COLORS["success"]
        )

        embed.add_field(
            name="📦 Objet Vendu",
            value=(
                f"{item.rarity.emoji} **{item.name}** `×{quantite}`\n"
                f"╰➤ Prix unitaire: `{item.value:,}` {self.EMOJIS['coin']}"
            ),
            inline=False
        )

        embed.add_field(
            name=f"{self.EMOJIS['coin']} Transaction",
            value=(
                f"```diff\n"
                f"+ {total:,} pièces reçues\n"
                f"```"
            ),
            inline=True
        )

        embed.add_field(
            name="💼 Nouveau Solde",
            value=(
                f"```yml\n"
                f"Avant: {old_balance:,}\n"
                f"Après: {player.coins:,}\n"
                f"```"
            ),
            inline=True
        )

        if self.GIFS["sell"] != "REMPLACE_PAR_TON_GIF":
            embed.set_thumbnail(url=self.GIFS["sell"])

        embed.set_footer(text="💡 Continue à vendre pour acheter des coffres !")

        await interaction.response.send_message(embed=embed)

    @sell.autocomplete('objet')
    async def sell_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplétion pour la vente."""
        player = self.data.get_player(interaction.user.id)
        choices = []
        for item_id in player.inventory:
            item = self.data.get_item(item_id)
            if item and (not current or current.lower() in item.name.lower()):
                qty = player.inventory[item_id]
                choices.append(
                    app_commands.Choice(
                        name=f"{item.rarity.emoji} {item.name} (×{qty}) - {item.value:,}💰",
                        value=item.name
                    )
                )
        return choices[:25]

    # ══════════════════════════════════════════════════════════════
    # 💸 COMMANDE VENDRE TOUT
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="vendretout", description="💸 Vend tous les objets d'une rareté")
    @app_commands.describe(rarete="Rareté à vendre")
    @app_commands.choices(rarete=[
        app_commands.Choice(name="⬜ Normal", value="NORMAL"),
        app_commands.Choice(name="🟦 Rare", value="RARE"),
        app_commands.Choice(name="🟪 Epic", value="EPIC"),
        app_commands.Choice(name="🟨 Légendaire", value="LEGENDARY"),
        app_commands.Choice(name="🟥 Mythique", value="MYTHIC")
    ])
    async def sell_all(self, interaction: discord.Interaction, rarete: str):
        """Vend tous les objets d'une rareté."""
        player = self.data.get_player(interaction.user.id)
        target_rarity = Rarity[rarete]

        items_to_sell = []
        for item_id, qty in list(player.inventory.items()):
            item = self.data.get_item(item_id)
            if item and item.rarity == target_rarity:
                items_to_sell.append((item, qty))

        if not items_to_sell:
            embed = self._create_error_embed(
                "📦 Aucun Objet",
                f"Tu n'as aucun objet {target_rarity.emoji} **{target_rarity.display_name}**."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        total_items = 0
        total_coins = 0
        old_balance = player.coins

        for item, qty in items_to_sell:
            player.sell_item(item.item_id, item.value, qty)
            total_items += qty
            total_coins += item.value * qty

        self.data.save_player(player)

        embed = discord.Embed(
            title=f"{self.EMOJIS['check']} Vente Massive !",
            color=self.COLORS.get(target_rarity, self.COLORS["success"])
        )

        embed.add_field(
            name="📦 Objets Vendus",
            value=f"{target_rarity.emoji} **{total_items}** objets {target_rarity.display_name}",
            inline=False
        )

        embed.add_field(
            name=f"{self.EMOJIS['coin']} Gains",
            value=f"```diff\n+ {total_coins:,} pièces\n```",
            inline=True
        )

        embed.add_field(
            name="💼 Solde",
            value=f"```yml\nAvant: {old_balance:,}\nAprès: {player.coins:,}\n```",
            inline=True
        )

        if self.GIFS["sell"] != "REMPLACE_PAR_TON_GIF":
            embed.set_thumbnail(url=self.GIFS["sell"])

        await interaction.response.send_message(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 👤 COMMANDE PROFIL
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="profil", description="👤 Affiche ton profil")
    @app_commands.describe(membre="Joueur à afficher")
    async def profile(self, interaction: discord.Interaction, membre: Optional[discord.Member] = None):
        """Affiche le profil stylisé."""
        target = membre or interaction.user
        player = self.data.get_player(target.id)

        # Calculs
        total_items = sum(player.inventory.values())
        unique_items = len(player.inventory)
        inventory_value = 0
        rarity_counts = {r: 0 for r in Rarity}
        
        for item_id, qty in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                inventory_value += item.value * qty
                rarity_counts[item.rarity] += qty

        total_wealth = player.coins + inventory_value
        rank_emoji, rank_name = self._get_rank(total_wealth)

        embed = discord.Embed(
            title=f"{rank_emoji} {target.display_name}",
            color=self.COLORS["profile"]
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        # Bannière de rang
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;33m╔════════════════════════════╗\u001b[0m\n"
            f"\u001b[1;33m║\u001b[0m   🏆 Rang: \u001b[1;36m{rank_name}\u001b[0m\n"
            f"\u001b[1;33m╚════════════════════════════╝\u001b[0m\n"
            f"```"
        )

        # Économie
        embed.add_field(
            name=f"{self.EMOJIS['coin']} Économie",
            value=(
                f"💰 Solde: `{player.coins:,}`\n"
                f"📦 Inventaire: `{inventory_value:,}`\n"
                f"💎 Total: `{total_wealth:,}`"
            ),
            inline=True
        )

        # Collection
        embed.add_field(
            name=f"{self.EMOJIS['inventory']} Collection",
            value=(
                f"📦 Objets: `{total_items}`\n"
                f"🎯 Uniques: `{unique_items}`\n"
                f"🏷️ Vendus: `{player.total_items_sold}`"
            ),
            inline=True
        )

        # Coffres
        embed.add_field(
            name=f"{self.EMOJIS['chest']} Coffres",
            value=(
                f"📅 Aujourd'hui: `{player.daily_chests_opened}/50`\n"
                f"📊 Total: `{player.total_chests_opened}`"
            ),
            inline=True
        )

        # Graphique de rareté
        rarity_bar = ""
        for rarity in Rarity:
            count = rarity_counts[rarity]
            bar_len = min(8, count // 3) if count > 0 else 0
            bar = "█" * bar_len + "░" * (8 - bar_len)
            rarity_bar += f"{rarity.emoji} `{bar}` {count}\n"
        
        embed.add_field(name="📊 Collection", value=rarity_bar, inline=False)

        if self.GIFS["profile"] != "REMPLACE_PAR_TON_GIF":
            embed.set_image(url=self.GIFS["profile"])

        embed.set_footer(text="🎮 Ouvre des coffres pour progresser !")

        await interaction.response.send_message(embed=embed)

    def _get_rank(self, wealth: int) -> tuple:
        """Retourne emoji et nom du rang."""
        ranks = [
            (1000000, "👑", "Empereur Légendaire"),
            (500000, "🏆", "Grand Maître"),
            (250000, "💎", "Diamant"),
            (100000, "🥇", "Or"),
            (50000, "🥈", "Argent"),
            (25000, "🥉", "Bronze"),
            (10000, "⭐", "Étoile"),
            (5000, "🌟", "Apprenti"),
            (0, "🌱", "Débutant")
        ]
        for threshold, emoji, name in ranks:
            if wealth >= threshold:
                return emoji, name
        return "🌱", "Débutant"

    # ══════════════════════════════════════════════════════════════
    # 🏆 COMMANDE CLASSEMENT
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="classement", description="🏆 Top des joueurs")
    @app_commands.describe(type="Type de classement")
    @app_commands.choices(type=[
        app_commands.Choice(name="💰 Richesse", value="coins"),
        app_commands.Choice(name="📦 Collection", value="collection")
    ])
    async def leaderboard(self, interaction: discord.Interaction, type: Optional[str] = "coins"):
        """Affiche le classement."""
        if type == "collection":
            players = self.data.get_collection_leaderboard(10)
            title = f"{self.EMOJIS['trophy']} Top Collectionneurs"
            icon = "📦"
        else:
            players = self.data.get_leaderboard(10)
            title = f"{self.EMOJIS['trophy']} Top Richesse"
            icon = "💰"

        embed = discord.Embed(title=title, color=0xFFD700)

        if not players:
            embed.description = "```\nAucun joueur n'a encore joué !\n```"
            await interaction.response.send_message(embed=embed)
            return

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        leaderboard_text = "```\n"
        leaderboard_text += "╔═══╤═══════════════╤════════════╗\n"
        leaderboard_text += "║ # │ Joueur        │ Score      ║\n"
        leaderboard_text += "╠═══╪═══════════════╪════════════╣\n"

        for i, p in enumerate(players):
            try:
                user = await self.bot.fetch_user(p.user_id)
                name = user.display_name[:13]
            except:
                name = f"Joueur#{p.user_id}"[:13]

            if type == "collection":
                score = f"{len(p.inventory)} obj"
            else:
                score = f"{p.coins:,}"

            leaderboard_text += f"║ {i+1} │ {name:<13} │ {score:>10} ║\n"

        leaderboard_text += "╚═══╧═══════════════╧════════════╝\n"
        leaderboard_text += "```"

        embed.description = leaderboard_text

        if self.GIFS["leaderboard"] != "REMPLACE_PAR_TON_GIF":
            embed.set_thumbnail(url=self.GIFS["leaderboard"])

        embed.set_footer(text="🎮 Joue pour monter dans le classement !")

        await interaction.response.send_message(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 📊 COMMANDE TAUX
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="taux", description="📊 Taux de drop")
    async def drop_rates(self, interaction: discord.Interaction):
        """Affiche les taux de drop."""
        embed = discord.Embed(
            title="🎰 Taux de Drop",
            color=self.COLORS["info"]
        )

        embed.description = (
            "```\n"
            "╔═════════════════════════════════╗\n"
            "║   PROBABILITÉS D'OBTENTION      ║\n"
            "╚═════════════════════════════════╝\n"
            "```"
        )

        for rarity in Rarity:
            pct = rarity.drop_rate * 100
            bar_len = int(pct / 2.5)
            bar = "▓" * bar_len + "░" * (20 - bar_len)
            
            embed.add_field(
                name=f"{rarity.emoji} {rarity.display_name}",
                value=f"`[{bar}]` **{pct:.1f}%**\n💰 Valeur: `{rarity.base_value:,}+`",
                inline=False
            )

        embed.add_field(
            name="📋 Infos",
            value=(
                f"```yml\n"
                f"Coffres gratuits/jour: 50\n"
                f"Coût coffre bonus: 3,500\n"
                f"```"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 🏪 COMMANDE BOUTIQUE
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="boutique", description="🏪 Boutique")
    async def shop(self, interaction: discord.Interaction):
        """Affiche la boutique."""
        player = self.data.get_player(interaction.user.id)
        
        embed = discord.Embed(
            title=f"{self.EMOJIS['shop']} Boutique",
            color=self.COLORS["shop"]
        )

        embed.description = (
            "```\n"
            "╔═════════════════════════════════╗\n"
            "║     BIENVENUE À LA BOUTIQUE     ║\n"
            "╚═════════════════════════════════╝\n"
            "```"
        )

        embed.add_field(
            name=f"{self.EMOJIS['chest']} Coffre Bonus",
            value=(
                f"💎 Prix: `3,500` pièces\n"
                f"📝 `/coffre payer:True`\n"
                f"*Ouvre un coffre supplémentaire*"
            ),
            inline=True
        )

        embed.add_field(
            name=f"{self.EMOJIS['coin']} Ton Solde",
            value=f"```yml\n{player.coins:,} pièces\n```",
            inline=True
        )

        can_buy = "✅ Tu peux acheter !" if player.coins >= 3500 else "❌ Fonds insuffisants"
        embed.add_field(
            name="📊 Status",
            value=can_buy,
            inline=True
        )

        embed.add_field(
            name="💡 Gagner des pièces",
            value=(
                f"• `/coffre` - Coffres gratuits\n"
                f"• `/vendre` - Vends un objet\n"
                f"• `/vendretout` - Vente en masse"
            ),
            inline=False
        )

        if self.GIFS["shop"] != "REMPLACE_PAR_TON_GIF":
            embed.set_thumbnail(url=self.GIFS["shop"])

        await interaction.response.send_message(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 🔄 SYSTÈME DE TRADE
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="trade", description="🔄 Proposer un échange")
    @app_commands.describe(
        joueur="Joueur avec qui échanger",
        ton_objet="Objet que tu donnes",
        quantite_donnee="Quantité que tu donnes",
        objet_demande="Objet que tu veux (optionnel)",
        quantite_demandee="Quantité demandée",
        pieces="Pièces à échanger (positif = tu donnes, négatif = tu demandes)"
    )
    async def trade(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member,
        ton_objet: str,
        quantite_donnee: Optional[int] = 1,
        objet_demande: Optional[str] = None,
        quantite_demandee: Optional[int] = 1,
        pieces: Optional[int] = 0
    ):
        """Propose un échange avec un autre joueur."""
        
        # Vérifications de base
        if joueur.id == interaction.user.id:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Erreur", "Tu ne peux pas échanger avec toi-même !"),
                ephemeral=True
            )
            return

        if joueur.bot:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Erreur", "Tu ne peux pas échanger avec un bot !"),
                ephemeral=True
            )
            return

        player = self.data.get_player(interaction.user.id)
        target_player = self.data.get_player(joueur.id)

        # Vérifier l'objet donné
        given_item = None
        for item_id in player.inventory:
            item = self.data.get_item(item_id)
            if item and item.name.lower() == ton_objet.lower():
                given_item = item
                break

        if not given_item:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Objet Introuvable", f"Tu n'as pas **{ton_objet}** dans ton inventaire."),
                ephemeral=True
            )
            return

        if player.inventory.get(given_item.item_id, 0) < quantite_donnee:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Quantité Insuffisante", f"Tu n'as que {player.inventory.get(given_item.item_id, 0)}× {given_item.name}."),
                ephemeral=True
            )
            return

        # Vérifier l'objet demandé (si spécifié)
        requested_item = None
        if objet_demande:
            for item_id in target_player.inventory:
                item = self.data.get_item(item_id)
                if item and item.name.lower() == objet_demande.lower():
                    requested_item = item
                    break

            if not requested_item:
                await interaction.response.send_message(
                    embed=self._create_error_embed("❌ Objet Introuvable", f"**{joueur.display_name}** n'a pas **{objet_demande}**."),
                    ephemeral=True
                )
                return

            if target_player.inventory.get(requested_item.item_id, 0) < quantite_demandee:
                await interaction.response.send_message(
                    embed=self._create_error_embed("❌ Quantité Insuffisante", f"**{joueur.display_name}** n'a pas assez de {requested_item.name}."),
                    ephemeral=True
                )
                return

        # Vérifier les pièces
        if pieces > 0 and player.coins < pieces:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Fonds Insuffisants", f"Tu n'as que {player.coins:,} pièces."),
                ephemeral=True
            )
            return

        if pieces < 0 and target_player.coins < abs(pieces):
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Fonds Insuffisants", f"**{joueur.display_name}** n'a pas assez de pièces."),
                ephemeral=True
            )
            return

        # Créer le trade
        trade_id = interaction.user.id
        self.pending_trades[trade_id] = {
            "sender": interaction.user.id,
            "receiver": joueur.id,
            "given_item": given_item,
            "given_qty": quantite_donnee,
            "requested_item": requested_item,
            "requested_qty": quantite_demandee if requested_item else 0,
            "coins": pieces,
            "timestamp": datetime.now()
        }

        # Créer l'embed de proposition
        embed = discord.Embed(
            title=f"{self.EMOJIS['trade']} Proposition d'Échange",
            color=self.COLORS["trade"]
        )

        embed.description = (
            f"**{interaction.user.display_name}** propose un échange à **{joueur.display_name}**"
        )

        # Ce que donne l'initiateur
        give_text = f"{given_item.rarity.emoji} **{given_item.name}** `×{quantite_donnee}`"
        if pieces > 0:
            give_text += f"\n{self.EMOJIS['coin']} `{pieces:,}` pièces"
        embed.add_field(name=f"📤 {interaction.user.display_name} donne", value=give_text, inline=True)

        # Ce que reçoit l'initiateur
        receive_text = ""
        if requested_item:
            receive_text = f"{requested_item.rarity.emoji} **{requested_item.name}** `×{quantite_demandee}`"
        if pieces < 0:
            if receive_text:
                receive_text += "\n"
            receive_text += f"{self.EMOJIS['coin']} `{abs(pieces):,}` pièces"
        if not receive_text:
            receive_text = "*Rien (cadeau)*"
        embed.add_field(name=f"📥 {interaction.user.display_name} reçoit", value=receive_text, inline=True)

        embed.add_field(
            name="⏳ En attente",
            value=f"**{joueur.mention}**, utilise les boutons ci-dessous !",
            inline=False
        )

        if self.GIFS["trade_pending"] != "REMPLACE_PAR_TON_GIF":
            embed.set_thumbnail(url=self.GIFS["trade_pending"])

        embed.set_footer(text="⏰ Cette offre expire dans 60 secondes")

        # Créer les boutons
        view = TradeView(self, trade_id, joueur.id)
        await interaction.response.send_message(embed=embed, view=view)

        # Timeout après 60 secondes
        await asyncio.sleep(60)
        if trade_id in self.pending_trades:
            del self.pending_trades[trade_id]
            try:
                timeout_embed = discord.Embed(
                    title=f"{self.EMOJIS['cross']} Échange Expiré",
                    description="L'offre n'a pas été acceptée à temps.",
                    color=self.COLORS["error"]
                )
                await interaction.edit_original_response(embed=timeout_embed, view=None)
            except:
                pass

    @trade.autocomplete('ton_objet')
    async def trade_give_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplétion pour l'objet donné."""
        player = self.data.get_player(interaction.user.id)
        choices = []
        for item_id in player.inventory:
            item = self.data.get_item(item_id)
            if item and (not current or current.lower() in item.name.lower()):
                qty = player.inventory[item_id]
                choices.append(
                    app_commands.Choice(
                        name=f"{item.rarity.emoji} {item.name} (×{qty})",
                        value=item.name
                    )
                )
        return choices[:25]

    async def execute_trade(self, trade_id: int, accepted: bool, interaction: discord.Interaction):
        """Exécute ou annule un trade."""
        if trade_id not in self.pending_trades:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Erreur", "Cet échange n'existe plus."),
                ephemeral=True
            )
            return

        trade = self.pending_trades[trade_id]
        
        if interaction.user.id != trade["receiver"]:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Erreur", "Seul le destinataire peut répondre."),
                ephemeral=True
            )
            return

        del self.pending_trades[trade_id]

        if not accepted:
            embed = discord.Embed(
                title=f"{self.EMOJIS['cross']} Échange Refusé",
                description=f"**{interaction.user.display_name}** a refusé l'échange.",
                color=self.COLORS["error"]
            )
            if self.GIFS["trade_cancel"] != "REMPLACE_PAR_TON_GIF":
                embed.set_thumbnail(url=self.GIFS["trade_cancel"])
            await interaction.response.edit_message(embed=embed, view=None)
            return

        # Exécuter l'échange
        sender = self.data.get_player(trade["sender"])
        receiver = self.data.get_player(trade["receiver"])

        # Transférer l'objet donné
        sender.remove_item(trade["given_item"].item_id, trade["given_qty"])
        receiver.add_item(trade["given_item"].item_id, trade["given_qty"])

        # Transférer l'objet demandé (si existe)
        if trade["requested_item"]:
            receiver.remove_item(trade["requested_item"].item_id, trade["requested_qty"])
            sender.add_item(trade["requested_item"].item_id, trade["requested_qty"])

        # Transférer les pièces
        if trade["coins"] > 0:
            sender.coins -= trade["coins"]
            receiver.coins += trade["coins"]
        elif trade["coins"] < 0:
            receiver.coins -= abs(trade["coins"])
            sender.coins += abs(trade["coins"])

        self.data.save_player(sender)
        self.data.save_player(receiver)

        # Message de succès
        try:
            sender_user = await self.bot.fetch_user(trade["sender"])
            sender_name = sender_user.display_name
        except:
            sender_name = "Joueur"

        embed = discord.Embed(
            title=f"{self.EMOJIS['check']} Échange Réussi !",
            description=f"L'échange entre **{sender_name}** et **{interaction.user.display_name}** a été effectué !",
            color=self.COLORS["success"]
        )

        # Résumé
        summary = f"**{sender_name}** a donné:\n"
        summary += f"• {trade['given_item'].rarity.emoji} {trade['given_item'].name} ×{trade['given_qty']}\n"
        if trade["coins"] > 0:
            summary += f"• {trade['coins']:,} {self.EMOJIS['coin']}\n"

        summary += f"\n**{interaction.user.display_name}** a donné:\n"
        if trade["requested_item"]:
            summary += f"• {trade['requested_item'].rarity.emoji} {trade['requested_item'].name} ×{trade['requested_qty']}\n"
        if trade["coins"] < 0:
            summary += f"• {abs(trade['coins']):,} {self.EMOJIS['coin']}\n"
        if not trade["requested_item"] and trade["coins"] >= 0:
            summary += "• *Rien (cadeau reçu)*\n"

        embed.add_field(name="📋 Résumé", value=summary, inline=False)

        if self.GIFS["trade_success"] != "REMPLACE_PAR_TON_GIF":
            embed.set_thumbnail(url=self.GIFS["trade_success"])

        await interaction.response.edit_message(embed=embed, view=None)

    # ══════════════════════════════════════════════════════════════
    # 🎁 COMMANDE CADEAU
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="cadeau", description="🎁 Offrir un objet à un joueur")
    @app_commands.describe(
        joueur="Joueur à qui offrir",
        objet="Objet à offrir",
        quantite="Quantité"
    )
    async def gift(self, interaction: discord.Interaction, joueur: discord.Member, objet: str, quantite: Optional[int] = 1):
        """Offre un objet gratuitement."""
        if joueur.id == interaction.user.id:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Erreur", "Tu ne peux pas t'offrir un cadeau !"),
                ephemeral=True
            )
            return

        player = self.data.get_player(interaction.user.id)
        target = self.data.get_player(joueur.id)

        # Vérifier l'objet
        item = None
        for item_id in player.inventory:
            potential = self.data.get_item(item_id)
            if potential and potential.name.lower() == objet.lower():
                item = potential
                break

        if not item:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Introuvable", f"Tu n'as pas **{objet}**."),
                ephemeral=True
            )
            return

        if player.inventory.get(item.item_id, 0) < quantite:
            await interaction.response.send_message(
                embed=self._create_error_embed("❌ Insuffisant", f"Tu n'as que {player.inventory.get(item.item_id, 0)}× {item.name}."),
                ephemeral=True
            )
            return

        # Transférer
        player.remove_item(item.item_id, quantite)
        target.add_item(item.item_id, quantite)
        self.data.save_player(player)
        self.data.save_player(target)

        embed = discord.Embed(
            title="🎁 Cadeau Envoyé !",
            description=(
                f"**{interaction.user.display_name}** a offert à **{joueur.display_name}**:\n\n"
                f"{item.rarity.emoji} **{item.name}** `×{quantite}`\n"
                f"💰 Valeur: `{item.value * quantite:,}` pièces"
            ),
            color=self.COLORS["success"]
        )

        embed.set_thumbnail(url=joueur.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @gift.autocomplete('objet')
    async def gift_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplétion pour le cadeau."""
        return await self.sell_autocomplete(interaction, current)

    # ══════════════════════════════════════════════════════════════
    # 🛠️ UTILITAIRES
    # ══════════════════════════════════════════════════════════════

    def _create_error_embed(self, title: str, description: str) -> discord.Embed:
        """Crée un embed d'erreur stylisé."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=self.COLORS["error"]
        )
        if self.GIFS["error"] != "REMPLACE_PAR_TON_GIF":
            embed.set_thumbnail(url=self.GIFS["error"])
        return embed

    # ══════════════════════════════════════════════════════════════
    # 🥚 SYSTÈME DE PETS - OEUFS
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="oeuf", description="🥚 Ouvre un œuf mystérieux pour obtenir un pet !")
    async def open_egg(self, interaction: discord.Interaction):
        """Ouvre un œuf pour obtenir un pet aléatoire."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        egg_cost = self.data.get_egg_cost()
        
        if player.coins < egg_cost:
            embed = self._create_error_embed(
                "🥚 Pas assez de pièces !",
                f"Tu as besoin de **{egg_cost:,}** 💰 pour ouvrir un œuf.\n"
                f"Tu as seulement **{player.coins:,}** 💰"
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Animation d'ouverture
        opening_embed = discord.Embed(
            title="🥚 Ouverture de l'œuf...",
            description="✨ L'œuf commence à se fissurer...",
            color=0xf39c12
        )
        message = await interaction.followup.send(embed=opening_embed)
        await asyncio.sleep(1.5)
        
        # Déduction des pièces et drop du pet
        player.coins -= egg_cost
        player.eggs_opened += 1
        
        # Sélection du pet
        import random
        egg_rates = self.data.get_egg_drop_rates()
        all_pets = self.data.get_all_pets()
        
        # Déterminer la rareté
        rand = random.random()
        cumulative = 0.0
        selected_rarity = "NORMAL"
        for rarity, rate in egg_rates.items():
            cumulative += rate
            if rand < cumulative:
                selected_rarity = rarity
                break
        
        # Filtrer les pets de cette rareté
        pets_of_rarity = [p for p in all_pets if p.rarity.name == selected_rarity]
        if pets_of_rarity:
            pet = random.choice(pets_of_rarity)
        else:
            pet = random.choice(all_pets)
        
        # Ajouter le pet au joueur
        player.add_pet(pet.pet_id)
        self.data.save_player(player)
        
        # Embed de révélation
        reveal_embed = discord.Embed(
            title="🐣 Un nouveau compagnon !",
            description=f"Tu as obtenu **{pet.emoji} {pet.name}** !",
            color=self.COLORS.get(pet.rarity, 0x3498db)
        )
        reveal_embed.add_field(
            name="📖 Description",
            value=pet.description,
            inline=False
        )
        reveal_embed.add_field(
            name="⭐ Rareté",
            value=f"{pet.rarity.emoji} {pet.rarity.display_name}",
            inline=True
        )
        reveal_embed.add_field(
            name="📈 Bonus de drop",
            value=f"+{pet.drop_bonus * 100:.1f}%",
            inline=True
        )
        reveal_embed.set_footer(text=f"💰 {player.coins:,} pièces restantes | Œufs ouverts: {player.eggs_opened}")
        
        await message.edit(embed=reveal_embed)

    @app_commands.command(name="pets", description="🐾 Affiche ta collection de pets")
    async def show_pets(self, interaction: discord.Interaction):
        """Affiche les pets du joueur."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        if not player.pets:
            embed = discord.Embed(
                title="🐾 Collection de Pets",
                description="Tu n'as aucun pet !\n\n"
                            f"Utilise `/oeuf` pour en obtenir un ({self.data.get_egg_cost():,} 💰)",
                color=0x95a5a6
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"🐾 Tes Compagnons ({len(player.pets)} pets)",
            color=0x9b59b6
        )
        
        pets_text = ""
        for pet_id, quantity in player.pets.items():
            pet = self.data.get_pet(pet_id)
            if pet:
                equipped = " 🔹 **ÉQUIPÉ**" if player.equipped_pet == pet_id else ""
                pets_text += f"{pet.emoji} **{pet.name}** x{quantity}\n"
                pets_text += f"   {pet.rarity.emoji} {pet.rarity.display_name} • +{pet.drop_bonus * 100:.1f}% drop{equipped}\n\n"
        
        embed.description = pets_text
        
        # Bonus actuel
        if player.equipped_pet:
            current_pet = self.data.get_pet(player.equipped_pet)
            if current_pet:
                embed.add_field(
                    name="📈 Bonus actif",
                    value=f"{current_pet.emoji} {current_pet.name}: **+{current_pet.drop_bonus * 100:.1f}%** taux de drop",
                    inline=False
                )
        else:
            embed.add_field(
                name="⚠️ Aucun pet équipé",
                value="Utilise `/equiper-pet <nom>` pour équiper un pet !",
                inline=False
            )
        
        embed.set_footer(text=f"💰 {player.coins:,} pièces | 🥚 {player.eggs_opened} œufs ouverts")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="equiper-pet", description="🐾 Équipe un pet pour obtenir son bonus")
    @app_commands.describe(nom="Le nom du pet à équiper")
    async def equip_pet(self, interaction: discord.Interaction, nom: str):
        """Équipe un pet."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        # Chercher le pet par nom
        all_pets = self.data.get_all_pets()
        target_pet = None
        for pet in all_pets:
            if pet.name.lower() == nom.lower():
                target_pet = pet
                break
        
        if not target_pet:
            # Recherche partielle
            for pet in all_pets:
                if nom.lower() in pet.name.lower():
                    target_pet = pet
                    break
        
        if not target_pet:
            embed = self._create_error_embed(
                "❌ Pet introuvable",
                f"Aucun pet avec le nom **{nom}** n'existe."
            )
            await interaction.followup.send(embed=embed)
            return
        
        if target_pet.pet_id not in player.pets:
            embed = self._create_error_embed(
                "❌ Pet non possédé",
                f"Tu ne possèdes pas **{target_pet.emoji} {target_pet.name}**."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Équiper le pet
        player.equip_pet(target_pet.pet_id)
        self.data.save_player(player)
        
        embed = discord.Embed(
            title="🐾 Pet équipé !",
            description=f"{target_pet.emoji} **{target_pet.name}** t'accompagne maintenant !",
            color=self.COLORS.get(target_pet.rarity, 0x2ecc71)
        )
        embed.add_field(
            name="📈 Bonus actif",
            value=f"+**{target_pet.drop_bonus * 100:.1f}%** taux de drop sur tous les coffres",
            inline=False
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="desequiper-pet", description="🐾 Retire le pet actuellement équipé")
    async def unequip_pet(self, interaction: discord.Interaction):
        """Déséquipe le pet actuel."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        if not player.equipped_pet:
            embed = self._create_error_embed(
                "❌ Aucun pet équipé",
                "Tu n'as pas de pet équipé actuellement."
            )
            await interaction.followup.send(embed=embed)
            return
        
        old_pet = self.data.get_pet(player.equipped_pet)
        player.unequip_pet()
        self.data.save_player(player)
        
        embed = discord.Embed(
            title="🐾 Pet déséquipé",
            description=f"{old_pet.emoji if old_pet else ''} **{old_pet.name if old_pet else 'Ton pet'}** retourne se reposer.",
            color=0x95a5a6
        )
        await interaction.followup.send(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 🛡️ SYSTÈME D'ÉQUIPEMENT
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="equipement", description="🛡️ Affiche ton équipement et tes bonus de set")
    async def show_equipment(self, interaction: discord.Interaction):
        """Affiche l'équipement actuel du joueur."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        embed = discord.Embed(
            title="🛡️ Ton Équipement",
            color=0xe67e22
        )
        
        # Slots d'équipement
        slot_emojis = {
            "HELMET": "🪖",
            "CHESTPLATE": "🛡️",
            "LEGGINGS": "👖",
            "BOOTS": "👢",
            "WEAPON": "⚔️",
            "ACCESSORY": "💍"
        }
        
        equipment_text = ""
        for slot, item_id in player.equipment.items():
            emoji = slot_emojis.get(slot, "📦")
            slot_name = {
                "HELMET": "Casque",
                "CHESTPLATE": "Plastron",
                "LEGGINGS": "Jambières",
                "BOOTS": "Bottes",
                "WEAPON": "Arme",
                "ACCESSORY": "Accessoire"
            }.get(slot, slot)
            
            if item_id:
                item = self.data.get_item(item_id)
                if item:
                    set_info = f" [{self.data.get_set(item.set_id).name}]" if item.set_id else ""
                    equipment_text += f"{emoji} **{slot_name}**: {item.rarity.emoji} {item.name}{set_info}\n"
                else:
                    equipment_text += f"{emoji} **{slot_name}**: ❓ Item inconnu\n"
            else:
                equipment_text += f"{emoji} **{slot_name}**: *Vide*\n"
        
        embed.add_field(name="📋 Slots", value=equipment_text, inline=False)
        
        # Bonus de sets
        set_bonuses = self.data.get_set_bonuses(player)
        if set_bonuses:
            bonus_text = ""
            for set_id, info in set_bonuses.items():
                bonus_text += f"**{info['set_name']}** ({info['pieces']}/4 pièces)\n"
                bonus_text += f"   ➤ {info['bonus'].get('description', 'Bonus actif')}\n"
            embed.add_field(name="✨ Bonus de Set Actifs", value=bonus_text, inline=False)
        
        # Bonus totaux
        total_drop = self.data.calculate_total_drop_bonus(player)
        total_coin = self.data.calculate_total_coin_bonus(player)
        
        if total_drop > 0 or total_coin > 0:
            bonus_total = ""
            if total_drop > 0:
                bonus_total += f"📈 Drop: **+{total_drop * 100:.1f}%**\n"
            if total_coin > 0:
                bonus_total += f"💰 Vente: **+{total_coin * 100:.0f}%**\n"
            embed.add_field(name="🎯 Bonus Totaux", value=bonus_total, inline=False)
        
        embed.set_footer(text="Utilise /equiper <nom_item> pour équiper un objet")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="equiper", description="🛡️ Équipe un objet de ton inventaire")
    @app_commands.describe(nom="Le nom de l'objet à équiper")
    async def equip_item(self, interaction: discord.Interaction, nom: str):
        """Équipe un objet."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        # Chercher l'item dans l'inventaire
        target_item = None
        for item_id in player.inventory:
            item = self.data.get_item(item_id)
            if item and item.name.lower() == nom.lower():
                target_item = item
                break
        
        if not target_item:
            # Recherche partielle
            for item_id in player.inventory:
                item = self.data.get_item(item_id)
                if item and nom.lower() in item.name.lower():
                    target_item = item
                    break
        
        if not target_item:
            embed = self._create_error_embed(
                "❌ Objet introuvable",
                f"Tu ne possèdes pas d'objet nommé **{nom}**."
            )
            await interaction.followup.send(embed=embed)
            return
        
        if not target_item.is_equipable():
            embed = self._create_error_embed(
                "❌ Non équipable",
                f"**{target_item.name}** ne peut pas être équipé.\n"
                "Seuls les casques, plastrons, jambières, bottes, armes et accessoires sont équipables."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Équiper l'item
        slot = target_item.item_type
        old_item_id = player.equip_item(target_item.item_id, slot)
        self.data.save_player(player)
        
        embed = discord.Embed(
            title="🛡️ Équipement modifié !",
            color=self.COLORS.get(target_item.rarity, 0x2ecc71)
        )
        
        slot_name = {
            "HELMET": "Casque",
            "CHESTPLATE": "Plastron",
            "LEGGINGS": "Jambières",
            "BOOTS": "Bottes",
            "WEAPON": "Arme",
            "ACCESSORY": "Accessoire"
        }.get(slot, slot)
        
        if old_item_id:
            old_item = self.data.get_item(old_item_id)
            old_name = old_item.name if old_item else old_item_id
            embed.description = f"**{slot_name}**: {old_name} ➤ {target_item.rarity.emoji} **{target_item.name}**"
        else:
            embed.description = f"**{slot_name}**: {target_item.rarity.emoji} **{target_item.name}** équipé !"
        
        # Afficher le bonus de set si applicable
        if target_item.set_id:
            equipment_set = self.data.get_set(target_item.set_id)
            if equipment_set:
                set_pieces = self.data.get_equipped_set_pieces(player)
                count = set_pieces.get(target_item.set_id, 0)
                embed.add_field(
                    name=f"📦 {equipment_set.name}",
                    value=f"{count}/4 pièces équipées",
                    inline=False
                )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="desequiper", description="🛡️ Retire un équipement")
    @app_commands.describe(slot="Le slot à vider (casque, plastron, jambieres, bottes, arme, accessoire)")
    @app_commands.choices(slot=[
        app_commands.Choice(name="Casque", value="HELMET"),
        app_commands.Choice(name="Plastron", value="CHESTPLATE"),
        app_commands.Choice(name="Jambières", value="LEGGINGS"),
        app_commands.Choice(name="Bottes", value="BOOTS"),
        app_commands.Choice(name="Arme", value="WEAPON"),
        app_commands.Choice(name="Accessoire", value="ACCESSORY"),
    ])
    async def unequip_item(self, interaction: discord.Interaction, slot: str):
        """Déséquipe un objet."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        old_item_id = player.unequip_item(slot)
        
        if not old_item_id:
            slot_name = {
                "HELMET": "Casque",
                "CHESTPLATE": "Plastron",
                "LEGGINGS": "Jambières",
                "BOOTS": "Bottes",
                "WEAPON": "Arme",
                "ACCESSORY": "Accessoire"
            }.get(slot, slot)
            embed = self._create_error_embed(
                "❌ Slot vide",
                f"Tu n'as rien d'équipé dans le slot **{slot_name}**."
            )
            await interaction.followup.send(embed=embed)
            return
        
        self.data.save_player(player)
        
        old_item = self.data.get_item(old_item_id)
        old_name = old_item.name if old_item else old_item_id
        
        embed = discord.Embed(
            title="🛡️ Équipement retiré",
            description=f"**{old_name}** a été déséquipé.",
            color=0x95a5a6
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="sets", description="📦 Affiche tous les sets d'équipement disponibles")
    async def show_sets(self, interaction: discord.Interaction):
        """Affiche la liste des sets et leurs bonus."""
        await interaction.response.defer()
        
        all_sets = self.data.get_all_sets()
        
        if not all_sets:
            embed = discord.Embed(
                title="📦 Sets d'Équipement",
                description="Aucun set disponible pour le moment.",
                color=0x95a5a6
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📦 Sets d'Équipement Disponibles",
            description="Collecte les pièces d'un set pour obtenir des bonus !",
            color=0xe67e22
        )
        
        for eq_set in all_sets:
            set_text = f"*{eq_set.description}*\n\n"
            set_text += f"**2 pièces**: {eq_set.bonus_2.get('description', 'Bonus')}\n"
            set_text += f"**4 pièces**: {eq_set.bonus_4.get('description', 'Bonus complet')}\n\n"
            set_text += f"Pièces: "
            
            # Lister les pièces du set
            pieces_names = []
            for piece_id in eq_set.pieces:
                item = self.data.get_item(piece_id)
                if item:
                    pieces_names.append(item.name)
                else:
                    pieces_names.append(piece_id)
            set_text += ", ".join(pieces_names)
            
            embed.add_field(name=f"✨ {eq_set.name}", value=set_text, inline=False)
        
        await interaction.followup.send(embed=embed)


# ══════════════════════════════════════════════════════════════
# 🔘 VIEW POUR LE TRADE
# ══════════════════════════════════════════════════════════════

class TradeView(discord.ui.View):
    """Boutons pour accepter/refuser un trade."""

    def __init__(self, cog: Economy, trade_id: int, receiver_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.trade_id = trade_id
        self.receiver_id = receiver_id

    @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.receiver_id:
            await interaction.response.send_message("❌ Seul le destinataire peut accepter.", ephemeral=True)
            return
        await self.cog.execute_trade(self.trade_id, True, interaction)

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.receiver_id:
            await interaction.response.send_message("❌ Seul le destinataire peut refuser.", ephemeral=True)
            return
        await self.cog.execute_trade(self.trade_id, False, interaction)


async def setup(bot: commands.Bot):
    """Setup function."""
    pass
