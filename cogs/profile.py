"""
Cog gérant le profil et le classement avec design ultra-moderne.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from models import Rarity
from services import DataManager
from utils import COLORS
from utils.styles import (
    Colors, Emojis,
    create_progress_bar, create_stat_bar, create_xp_bar,
    create_level_display, format_number, create_rarity_indicator
)


# ═══════════════════════════════════════════════════════════════════════════════
# 👤 COG PROFIL - AFFICHAGE MODERNE
# ═══════════════════════════════════════════════════════════════════════════════

class Profile(commands.Cog):
    """Système de profil et classement ultra-moderne."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager

    def _get_rank(self, wealth: int) -> tuple:
        """Retourne emoji, nom et couleur du rang."""
        ranks = [
            (1000000, "👑", "Empereur Légendaire", Colors.MYTHIC),
            (500000, "🏆", "Grand Maître", Colors.LEGENDARY),
            (250000, "💎", "Diamant", Colors.EPIC),
            (100000, "🥇", "Or", 0xFFD700),
            (50000, "🥈", "Argent", 0xC0C0C0),
            (25000, "🥉", "Bronze", 0xCD7F32),
            (10000, "⭐", "Étoile", Colors.PRIMARY),
            (5000, "🌟", "Apprenti", Colors.INFO),
            (0, "🌱", "Débutant", Colors.SECONDARY)
        ]
        for threshold, emoji, name, color in ranks:
            if wealth >= threshold:
                return emoji, name, color
        return "🌱", "Débutant", Colors.SECONDARY

    # ───────────────────────────────────────────────────────────────
    # 👤 COMMANDE PROFIL MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="profil", description="👤 Affiche ton profil détaillé")
    @app_commands.describe(membre="Joueur à afficher")
    async def profile(self, interaction: discord.Interaction, membre: Optional[discord.Member] = None):
        """Affiche le profil avec design ultra-moderne."""
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
        rank_emoji, rank_name, rank_color = self._get_rank(total_wealth)

        embed = discord.Embed(color=rank_color)
        embed.set_thumbnail(url=target.display_avatar.url)

        # Header moderne avec niveau si disponible
        level_display = ""
        if hasattr(player, 'level'):
            level_display = f" │ ⭐ Niv.{player.level}"
        
        embed.title = f"{rank_emoji} {target.display_name}"
        embed.description = (
            f"```ansi\n"
            f"\u001b[0;37m╔{'═' * 34}╗\u001b[0m\n"
            f"\u001b[0;37m║\u001b[0m  🏆 \u001b[1;33m{rank_name:^24}\u001b[0m{level_display:>4} \u001b[0;37m║\u001b[0m\n"
            f"\u001b[0;37m╚{'═' * 34}╝\u001b[0m\n"
            f"```"
        )

        # Économie avec barre de progression vers le rang suivant
        ranks_thresholds = [0, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000]
        current_threshold = 0
        next_threshold = ranks_thresholds[-1]
        for i, threshold in enumerate(ranks_thresholds):
            if total_wealth >= threshold:
                current_threshold = threshold
                if i + 1 < len(ranks_thresholds):
                    next_threshold = ranks_thresholds[i + 1]
        
        progress_to_next = create_progress_bar(
            total_wealth - current_threshold, 
            next_threshold - current_threshold, 
            10
        )
        
        embed.add_field(
            name=f"{Emojis.COIN} Économie",
            value=(
                f"💰 Solde: `{format_number(player.coins)}`\n"
                f"📦 Inventaire: `{format_number(inventory_value)}`\n"
                f"💎 Fortune: `{format_number(total_wealth)}`\n"
                f"▸ Prochain rang: {progress_to_next}"
            ),
            inline=True
        )

        # Collection avec stats
        embed.add_field(
            name=f"{Emojis.INVENTORY} Collection",
            value=(
                f"📦 Total: `{total_items}`\n"
                f"🎯 Uniques: `{unique_items}`\n"
                f"🏷️ Vendus: `{player.total_items_sold}`\n"
                f"💫 Qualité: {self._get_collection_rating(rarity_counts)}"
            ),
            inline=True
        )

        # Coffres avec barre
        chest_bar = create_progress_bar(player.daily_chests_opened, 50, 8, show_percentage=False)
        embed.add_field(
            name=f"{Emojis.CHEST} Coffres",
            value=(
                f"📅 {chest_bar} `{player.daily_chests_opened}/50`\n"
                f"📊 Total: `{player.total_chests_opened}`"
            ),
            inline=True
        )

        # Stats de combat si disponibles
        if hasattr(player, 'level'):
            current_xp, required_xp, percentage = player.get_xp_progress()
            xp_bar = create_xp_bar(current_xp, required_xp, 10)
            
            embed.add_field(
                name=f"{Emojis.SWORD} Combat",
                value=(
                    f"⭐ Niveau: `{player.level}`\n"
                    f"📈 XP: {xp_bar} `{percentage}%`\n"
                    f"👹 Boss vaincus: `{player.bosses_defeated}`"
                ),
                inline=True
            )

        # Graphique de rareté moderne
        max_count = max(rarity_counts.values()) if any(rarity_counts.values()) else 1
        rarity_lines = []
        
        for rarity in [Rarity.MYTHIC, Rarity.LEGENDARY, Rarity.EPIC, Rarity.RARE, Rarity.NORMAL]:
            count = rarity_counts[rarity]
            bar = create_stat_bar(count, max_count, 8) if count > 0 else "░░░░░░░░"
            rarity_lines.append(f"{rarity.emoji} {bar} `{count}`")
        
        embed.add_field(
            name="📊 Répartition",
            value="\n".join(rarity_lines),
            inline=True
        )

        # Pet équipé si existant
        if hasattr(player, 'active_pet') and player.active_pet:
            pet = self.data.get_pet(player.active_pet)
            if pet:
                embed.add_field(
                    name=f"🐾 Compagnon",
                    value=f"{pet.emoji} **{pet.name}**\n*{pet.rarity.display_name}*",
                    inline=True
                )

        embed.set_footer(
            text="🎮 Joue pour améliorer ton profil !",
            icon_url=self.bot.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

    def _get_collection_rating(self, rarity_counts: dict) -> str:
        """Calcule la note de qualité de la collection."""
        score = (
            rarity_counts.get(Rarity.MYTHIC, 0) * 100 +
            rarity_counts.get(Rarity.LEGENDARY, 0) * 50 +
            rarity_counts.get(Rarity.EPIC, 0) * 20 +
            rarity_counts.get(Rarity.RARE, 0) * 5 +
            rarity_counts.get(Rarity.NORMAL, 0) * 1
        )
        
        if score >= 1000:
            return "⭐⭐⭐⭐⭐"
        elif score >= 500:
            return "⭐⭐⭐⭐"
        elif score >= 200:
            return "⭐⭐⭐"
        elif score >= 50:
            return "⭐⭐"
        else:
            return "⭐"

    # ───────────────────────────────────────────────────────────────
    # 🏆 COMMANDE CLASSEMENT MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="classement", description="🏆 Top des joueurs du serveur")
    @app_commands.describe(type="Type de classement à afficher")
    @app_commands.choices(type=[
        app_commands.Choice(name="💰 Richesse totale", value="coins"),
        app_commands.Choice(name="📦 Collection", value="collection"),
        app_commands.Choice(name="⭐ Niveau", value="level"),
        app_commands.Choice(name="👹 Boss vaincus", value="bosses")
    ])
    async def leaderboard(self, interaction: discord.Interaction, type: Optional[str] = "coins"):
        """Affiche le classement avec design moderne."""
        
        # Déterminer le type de classement
        if type == "collection":
            players = self.data.get_collection_leaderboard(10)
            title = "📦 Top Collectionneurs"
            color = Colors.EPIC
        elif type == "level":
            players = self.data.get_level_leaderboard(10) if hasattr(self.data, 'get_level_leaderboard') else []
            title = "⭐ Top Niveaux"
            color = Colors.PRIMARY
        elif type == "bosses":
            players = self.data.get_boss_leaderboard(10) if hasattr(self.data, 'get_boss_leaderboard') else []
            title = "👹 Top Chasseurs de Boss"
            color = Colors.DANGER
        else:
            players = self.data.get_leaderboard(10)
            title = "💰 Top Richesse"
            color = Colors.LEGENDARY

        embed = discord.Embed(
            title=f"{Emojis.TROPHY} {title}",
            color=color
        )

        if not players:
            embed.description = (
                f"```ansi\n"
                f"\u001b[0;33m╔{'═' * 30}╗\u001b[0m\n"
                f"\u001b[0;33m║\u001b[0m   Aucun joueur pour l'instant   \u001b[0;33m║\u001b[0m\n"
                f"\u001b[0;33m╚{'═' * 30}╝\u001b[0m\n"
                f"```\n"
                f"💡 Sois le premier à jouer !"
            )
            await interaction.response.send_message(embed=embed)
            return

        # Header du classement
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;33m╔{'═' * 36}╗\u001b[0m\n"
            f"\u001b[1;33m║\u001b[0m       🏆 TABLEAU D'HONNEUR 🏆        \u001b[1;33m║\u001b[0m\n"
            f"\u001b[1;33m╚{'═' * 36}╝\u001b[0m\n"
            f"```"
        )

        # Construire le classement
        position_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        leaderboard_lines = []
        for i, p in enumerate(players[:10]):
            try:
                user = await self.bot.fetch_user(p.user_id)
                name = user.display_name[:15]
            except:
                name = f"Joueur#{p.user_id}"[:15]

            pos_emoji = position_emojis[i] if i < len(position_emojis) else f"`{i+1}.`"
            
            # Score selon le type
            if type == "collection":
                score = f"`{len(p.inventory)}` objets"
            elif type == "level":
                score = f"`Niv.{p.level if hasattr(p, 'level') else 1}`"
            elif type == "bosses":
                score = f"`{p.bosses_defeated if hasattr(p, 'bosses_defeated') else 0}` boss"
            else:
                score = f"`{format_number(p.coins)}`"

            # Barre de progression relative
            if players:
                if type == "collection":
                    max_val = max(len(pl.inventory) for pl in players) or 1
                    current_val = len(p.inventory)
                elif type == "level":
                    max_val = max(getattr(pl, 'level', 1) for pl in players) or 1
                    current_val = getattr(p, 'level', 1)
                elif type == "bosses":
                    max_val = max(getattr(pl, 'bosses_defeated', 0) for pl in players) or 1
                    current_val = getattr(p, 'bosses_defeated', 0)
                else:
                    max_val = players[0].coins or 1
                    current_val = p.coins
                
                bar = create_stat_bar(current_val, max_val, 6)
            else:
                bar = "██████"

            leaderboard_lines.append(f"{pos_emoji} **{name}** {bar} {score}")

        embed.add_field(
            name="🎖️ Classement",
            value="\n".join(leaderboard_lines),
            inline=False
        )

        # Position du joueur actuel
        user_position = None
        for i, p in enumerate(players):
            if p.user_id == interaction.user.id:
                user_position = i + 1
                break
        
        if user_position:
            embed.add_field(
                name="📍 Ta Position",
                value=f"Tu es **#{user_position}** dans ce classement !",
                inline=False
            )
        else:
            embed.add_field(
                name="📍 Ta Position",
                value="Tu n'es pas encore dans le top 10. Continue à jouer !",
                inline=False
            )

        embed.set_footer(
            text="🎮 Joue pour monter dans le classement !",
            icon_url=self.bot.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 📊 COMMANDE STATISTIQUES GLOBALES
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="stats", description="📊 Statistiques globales du serveur")
    async def server_stats(self, interaction: discord.Interaction):
        """Affiche les statistiques globales du serveur."""
        all_players = list(self.data._players.values())
        
        if not all_players:
            embed = discord.Embed(
                title=f"{Emojis.STATS} Statistiques Serveur",
                description="Aucune donnée disponible pour l'instant.",
                color=Colors.SECONDARY
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Calculs
        total_coins = sum(p.coins for p in all_players)
        total_items = sum(sum(p.inventory.values()) for p in all_players)
        total_chests = sum(p.total_chests_opened for p in all_players)
        total_sold = sum(p.total_items_sold for p in all_players)
        
        avg_coins = total_coins // len(all_players) if all_players else 0
        avg_items = total_items // len(all_players) if all_players else 0
        
        embed = discord.Embed(
            title=f"{Emojis.STATS} Statistiques Serveur",
            color=Colors.PRIMARY
        )
        
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;34m╔{'═' * 32}╗\u001b[0m\n"
            f"\u001b[1;34m║\u001b[0m     📊 STATISTIQUES GLOBALES 📊    \u001b[1;34m║\u001b[0m\n"
            f"\u001b[1;34m╚{'═' * 32}╝\u001b[0m\n"
            f"```"
        )
        
        embed.add_field(
            name="👥 Joueurs",
            value=f"`{len(all_players)}` joueurs actifs",
            inline=True
        )
        
        embed.add_field(
            name=f"{Emojis.COIN} Économie",
            value=(
                f"💰 Total: `{format_number(total_coins)}`\n"
                f"📊 Moyenne: `{format_number(avg_coins)}`/joueur"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📦 Items",
            value=(
                f"🎯 Total: `{format_number(total_items)}`\n"
                f"📊 Moyenne: `{avg_items}`/joueur"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🎁 Activité",
            value=(
                f"📦 Coffres ouverts: `{format_number(total_chests)}`\n"
                f"🏷️ Items vendus: `{format_number(total_sold)}`"
            ),
            inline=False
        )
        
        embed.set_footer(
            text="💡 Ces stats sont en temps réel",
            icon_url=self.bot.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    pass
