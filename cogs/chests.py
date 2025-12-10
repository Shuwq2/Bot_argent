"""
Cog gérant le système de coffres (gacha) avec design ultra-moderne.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from models import Chest, Rarity
from services import DataManager
from utils import RARITY_IMAGES, SUSPENSE_COLORS, GIFS, COLORS, EMOJIS
from utils.styles import (
    Colors, Emojis,
    create_progress_bar, create_rarity_indicator,
    create_header, create_separator, create_box,
    format_number, EmbedTheme
)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎁 COG COFFRES - SYSTÈME GACHA MODERNE
# ═══════════════════════════════════════════════════════════════════════════════

class Chests(commands.Cog):
    """Système de coffres gacha ultra-moderne."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager
        self.chest = Chest(self.data.get_all_items())

    # ───────────────────────────────────────────────────────────────
    # 🎁 COMMANDE COFFRE - OUVERTURE UNIQUE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="coffre", description="🎁 Ouvre un coffre mystérieux !")
    @app_commands.describe(payer="💎 Payer 3500 pièces pour un coffre bonus")
    async def open_chest(self, interaction: discord.Interaction, payer: Optional[bool] = False):
        """Ouvre un coffre avec animation de suspense moderne."""
        player = self.data.get_player(interaction.user.id)
        
        # Vérifications
        if not player.can_open_free_chest() and not payer:
            embed = self._error_embed(
                "Limite Journalière",
                f"Tu as ouvert **{player.MAX_DAILY_CHESTS}/{player.MAX_DAILY_CHESTS}** coffres aujourd'hui.\n\n"
                f"```ansi\n"
                f"\u001b[0;33m┌─────────────────────────┐\u001b[0m\n"
                f"\u001b[0;33m│\u001b[0m {Emojis.COIN} Solde: {format_number(player.coins):>15}\u001b[0;33m│\u001b[0m\n"
                f"\u001b[0;33m│\u001b[0m 💎 Coût:  {format_number(player.CHEST_COST):>15}\u001b[0;33m│\u001b[0m\n"
                f"\u001b[0;33m└─────────────────────────┘\u001b[0m\n"
                f"```\n"
                f"▸ `/coffre payer:True` pour acheter\n"
                f"▸ Reviens demain pour 50 coffres gratuits !"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if payer and not player.can_open_free_chest():
            if not player.can_afford_chest():
                embed = self._error_embed(
                    "Fonds Insuffisants",
                    f"```diff\n"
                    f"- Requis:  {format_number(player.CHEST_COST)} {Emojis.COIN}\n"
                    f"- Solde:   {format_number(player.coins)} {Emojis.COIN}\n"
                    f"- Manque:  {format_number(player.CHEST_COST - player.coins)} {Emojis.COIN}\n"
                    f"```\n"
                    f"💡 Vends des objets avec `/vendre` !"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Logique d'ouverture
        success = player.open_chest(paid=payer and not player.can_open_free_chest())
        if not success:
            await interaction.response.send_message(embed=self._error_embed("Erreur", "Impossible d'ouvrir le coffre."))
            return

        # Calcul du bonus de drop (pet + sets)
        drop_bonus = self.data.calculate_total_drop_bonus(player)
        item = self.chest.open(drop_bonus)
        if not item:
            await interaction.response.send_message(embed=self._error_embed("Erreur", "Aucun objet disponible."))
            return

        player.add_item(item.item_id)
        self.data.save_player(player)

        # ═══ ANIMATION DE SUSPENSE MODERNE ═══
        opening_embed = discord.Embed(
            title=f"✨ Ouverture du Coffre... ✨",
            description=(
                f"```ansi\n"
                f"\u001b[1;33m╔{'═' * 34}╗\u001b[0m\n"
                f"\u001b[1;33m║\u001b[0m      📦 LE COFFRE S'ILLUMINE...     \u001b[1;33m║\u001b[0m\n"
                f"\u001b[1;33m╚{'═' * 34}╝\u001b[0m\n"
                f"```"
            ),
            color=Colors.LEGENDARY
        )
        await interaction.response.send_message(embed=opening_embed)
        await asyncio.sleep(0.8)

        # Animation de suspense - défilement progressif
        suspense_sequence = ["rare", "epic", "legendary", "mythic", "legendary", "epic", "rare", "epic", "legendary"]
        
        for i, rarity_key in enumerate(suspense_sequence):
            delay = 0.12 + (i * 0.04)
            progress = create_progress_bar(i + 1, len(suspense_sequence), 20)
            
            suspense_embed = discord.Embed(
                title="🎲 Tirage en cours...",
                description=f"{progress}\n\n*La roue du destin tourne...*",
                color=SUSPENSE_COLORS.get(rarity_key, 0xFFFFFF)
            )
            
            if RARITY_IMAGES.get(rarity_key):
                suspense_embed.set_image(url=RARITY_IMAGES[rarity_key])
            
            await interaction.edit_original_response(embed=suspense_embed)
            await asyncio.sleep(delay)

        await asyncio.sleep(0.5)

        # ═══ RÉVÉLATION FINALE ═══
        rarity_name = item.rarity.name.lower()
        reveal_embed = discord.Embed(
            title=self._get_reveal_title(item.rarity),
            description=f"```\n{'⭐' * 10}\n```",
            color=COLORS.get(item.rarity, 0x9e9e9e)
        )
        
        if RARITY_IMAGES.get(rarity_name):
            reveal_embed.set_image(url=RARITY_IMAGES[rarity_name])
        
        await interaction.edit_original_response(embed=reveal_embed)
        await asyncio.sleep(1.2)

        # ═══ AFFICHAGE FINAL MODERNE ═══
        final_embed = self._create_modern_reveal_embed(item, player)
        await interaction.edit_original_response(embed=final_embed)

    # ───────────────────────────────────────────────────────────────
    # 🎁 COMMANDE COFFRES MULTIPLES
    # ───────────────────────────────────────────────────────────────

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
        """Ouvre plusieurs coffres avec résumé moderne."""
        player = self.data.get_player(interaction.user.id)
        
        free_remaining = player.get_remaining_free_chests()
        
        if not payer:
            if free_remaining == 0:
                embed = self._error_embed(
                    "Limite Journalière",
                    f"Tu as utilisé tous tes coffres gratuits.\n\n"
                    f"💡 `/coffres nombre:X payer:True` pour acheter\n"
                    f"{Emojis.COIN} Coût: **{format_number(player.CHEST_COST)}**/coffre"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            chests_to_open = min(nombre, free_remaining)
            cost = 0
        else:
            free_to_use = min(nombre, free_remaining)
            paid_to_use = nombre - free_to_use
            cost = paid_to_use * player.CHEST_COST
            
            if cost > player.coins:
                max_affordable = player.coins // player.CHEST_COST
                embed = self._error_embed(
                    "Fonds Insuffisants",
                    f"```diff\n"
                    f"- Coffres demandés: {nombre}\n"
                    f"- Gratuits restants: {free_remaining}\n"
                    f"- À payer: {paid_to_use}\n"
                    f"- Coût: {format_number(cost)} {Emojis.COIN}\n"
                    f"- Solde: {format_number(player.coins)} {Emojis.COIN}\n"
                    f"```\n"
                    f"💡 Maximum possible: **{free_remaining + max_affordable}** coffres"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            chests_to_open = nombre

        # Animation d'ouverture moderne
        opening_embed = discord.Embed(
            title=f"🎁 Ouverture de {chests_to_open} Coffres...",
            description=(
                f"```ansi\n"
                f"\u001b[1;33m╔{'═' * 40}╗\u001b[0m\n"
                f"\u001b[1;33m║\u001b[0m     📦📦📦 OUVERTURE EN COURS 📦📦📦      \u001b[1;33m║\u001b[0m\n"
                f"\u001b[1;33m╚{'═' * 40}╝\u001b[0m\n"
                f"```"
            ),
            color=Colors.LEGENDARY
        )
        await interaction.response.send_message(embed=opening_embed)
        await asyncio.sleep(2)

        # Ouvrir les coffres
        items_obtained = []
        rarity_counts = {r: 0 for r in Rarity}
        total_value = 0
        drop_bonus = self.data.calculate_total_drop_bonus(player)

        for i in range(chests_to_open):
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

        # ═══ RÉSUMÉ MODERNE ═══
        result_embed = discord.Embed(
            title=f"🎉 {len(items_obtained)} Coffres Ouverts !",
            description=(
                f"```ansi\n"
                f"\u001b[1;32m╔{'═' * 36}╗\u001b[0m\n"
                f"\u001b[1;32m║\u001b[0m       ✨ RÉSUMÉ DES DROPS ✨         \u001b[1;32m║\u001b[0m\n"
                f"\u001b[1;32m╚{'═' * 36}╝\u001b[0m\n"
                f"```"
            ),
            color=Colors.SUCCESS
        )

        # Résumé par rareté avec barres visuelles
        rarity_lines = []
        max_count = max(rarity_counts.values()) if items_obtained else 1
        
        for rarity in [Rarity.MYTHIC, Rarity.LEGENDARY, Rarity.EPIC, Rarity.RARE, Rarity.NORMAL]:
            count = rarity_counts[rarity]
            if count > 0:
                bar = create_progress_bar(count, max_count, 8, show_percentage=False)
                rarity_lines.append(f"{rarity.emoji} **{rarity.display_name}** {bar} `×{count}`")

        result_embed.add_field(
            name="📊 Par Rareté",
            value="\n".join(rarity_lines) if rarity_lines else "*Aucun objet*",
            inline=True
        )
        
        # Valeur et coût
        stats_text = f"{Emojis.COIN} **Valeur**: `{format_number(total_value)}`"
        if cost > 0:
            stats_text += f"\n💳 **Coût**: `{format_number(cost)}`"
            profit = total_value - cost
            if profit > 0:
                stats_text += f"\n📈 **Profit**: `+{format_number(profit)}`"
            else:
                stats_text += f"\n📉 **Perte**: `{format_number(profit)}`"
        
        result_embed.add_field(name="💰 Économie", value=stats_text, inline=True)

        # Meilleurs drops
        if items_obtained:
            best_items = sorted(items_obtained, key=lambda x: x.value, reverse=True)[:5]
            best_text = "\n".join([
                f"{item.rarity.emoji} **{item.name}** `{format_number(item.value)}`" 
                for item in best_items
            ])
            result_embed.add_field(name=f"{Emojis.TROPHY} Top Drops", value=best_text, inline=False)

        # Stats du joueur
        remaining_bar = create_progress_bar(player.get_remaining_free_chests(), 50, 12)
        result_embed.add_field(
            name="📈 Tes Stats",
            value=(
                f"📦 Coffres: {remaining_bar} `{player.get_remaining_free_chests()}/50`\n"
                f"{Emojis.COIN} Solde: `{format_number(player.coins)}`\n"
                f"🎯 Total ouverts: `{player.total_chests_opened}`"
            ),
            inline=False
        )

        # Footer spécial si mythic/legendary
        mythic_count = rarity_counts[Rarity.MYTHIC]
        legendary_count = rarity_counts[Rarity.LEGENDARY]
        
        if mythic_count > 0:
            result_embed.set_footer(text=f"🔥 INCROYABLE ! {mythic_count} MYTHIQUE(S) ! 🔥")
            result_embed.color = Colors.MYTHIC
        elif legendary_count > 0:
            result_embed.set_footer(text=f"⭐ Bravo ! {legendary_count} LÉGENDAIRE(S) ! ⭐")
            result_embed.color = Colors.LEGENDARY
        else:
            result_embed.set_footer(text="💡 /inventaire pour voir ta collection")

        await interaction.edit_original_response(embed=result_embed)

    # ───────────────────────────────────────────────────────────────
    # 📊 COMMANDE TAUX DE DROP
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="taux", description="📊 Affiche les taux de drop")
    async def drop_rates(self, interaction: discord.Interaction):
        """Affiche les taux de drop avec design moderne."""
        player = self.data.get_player(interaction.user.id)
        drop_bonus = self.data.calculate_total_drop_bonus(player)
        
        embed = discord.Embed(
            title=f"📊 Taux de Drop",
            color=Colors.PRIMARY
        )
        
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;34m╔{'═' * 32}╗\u001b[0m\n"
            f"\u001b[1;34m║\u001b[0m    🎲 PROBABILITÉS DU GACHA 🎲     \u001b[1;34m║\u001b[0m\n"
            f"\u001b[1;34m╚{'═' * 32}╝\u001b[0m\n"
            f"```"
        )
        
        # Taux avec barres visuelles
        rates_text = ""
        for rarity in [Rarity.MYTHIC, Rarity.LEGENDARY, Rarity.EPIC, Rarity.RARE, Rarity.NORMAL]:
            base_rate = rarity.drop_rate * 100
            bar = create_progress_bar(base_rate, 60, 8, show_percentage=False)
            rates_text += f"{rarity.emoji} **{rarity.display_name}** {bar} `{base_rate:.2f}%`\n"
        
        embed.add_field(name="🎲 Taux de Base", value=rates_text, inline=False)
        
        if drop_bonus > 0:
            bonus_text = (
                f"```diff\n"
                f"+ {drop_bonus * 100:.1f}% de chance bonus\n"
                f"```\n"
                f"*Bonus provenant de ton pet et sets équipés*"
            )
            embed.add_field(name="📈 Ton Bonus", value=bonus_text, inline=False)
        else:
            embed.add_field(
                name="💡 Conseils",
                value="▸ Équipe un **pet** pour +5-15% de chances\n▸ Complète des **sets** pour des bonus supplémentaires",
                inline=False
            )
        
        embed.set_footer(
            text="💡 Les taux sont calculés avec ton bonus actuel",
            icon_url=self.bot.user.display_avatar.url
        )
        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 🛠️ MÉTHODES UTILITAIRES
    # ───────────────────────────────────────────────────────────────

    def _get_reveal_title(self, rarity: Rarity) -> str:
        """Retourne le titre de révélation selon la rareté."""
        titles = {
            Rarity.NORMAL: "📦 Un objet apparaît...",
            Rarity.RARE: "💎 RARE ! Quelque chose brille !",
            Rarity.EPIC: "🌟 ÉPIQUE ! Aura violette !",
            Rarity.LEGENDARY: "⚡ LÉGENDAIRE !! Lumière dorée !!",
            Rarity.MYTHIC: "🔥🔥 MYTHIQUE !!! INCROYABLE !!! 🔥🔥"
        }
        return titles.get(rarity, "📦 Un objet apparaît...")

    def _create_modern_reveal_embed(self, item, player) -> discord.Embed:
        """Crée l'embed de révélation moderne."""
        color = COLORS.get(item.rarity, Colors.SECONDARY)
        
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
        
        # Indicateur de rareté visuel
        rarity_indicator = create_rarity_indicator(item.rarity.name)
        
        embed.description = (
            f"{rarity_indicator}\n\n"
            f"*« {item.description} »*"
        )

        # Infos de l'item
        embed.add_field(
            name="📋 Informations",
            value=(
                f"```yml\n"
                f"Rareté:    {item.rarity.display_name}\n"
                f"Valeur:    {format_number(item.value)} pièces\n"
                f"Catégorie: {item.category}\n"
                f"```"
            ),
            inline=True
        )

        # Stats du joueur
        remaining_bar = create_progress_bar(player.get_remaining_free_chests(), 50, 8, show_percentage=False)
        embed.add_field(
            name="📊 Stats",
            value=(
                f"📦 {remaining_bar} `{player.get_remaining_free_chests()}/50`\n"
                f"{Emojis.COIN} `{format_number(player.coins)}`\n"
                f"🎯 `{player.total_chests_opened}` ouverts"
            ),
            inline=True
        )

        embed.set_footer(
            text=f"{item.rarity.emoji} {item.rarity.display_name} • /inventaire pour ta collection",
            icon_url=self.bot.user.display_avatar.url
        )
        
        return embed

    def _error_embed(self, title: str, description: str) -> discord.Embed:
        """Crée un embed d'erreur moderne."""
        return discord.Embed(
            title=f"{Emojis.ERROR} {title}",
            description=description,
            color=Colors.ERROR
        )


async def setup(bot: commands.Bot):
    pass
