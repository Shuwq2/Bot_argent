"""
Cog gérant les pets et les œufs avec design ultra-moderne.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Optional
import asyncio
import random

from services import DataManager
from utils import COLORS
from utils.styles import (
    Colors, Emojis,
    create_progress_bar, create_stat_bar,
    create_rarity_indicator, format_number
)


# ═══════════════════════════════════════════════════════════════════════════════
# 🐾 COG PETS - SYSTÈME DE COMPAGNONS MODERNE
# ═══════════════════════════════════════════════════════════════════════════════

class Pets(commands.Cog):
    """Système de pets et œufs ultra-moderne."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager

    # ───────────────────────────────────────────────────────────────
    # 🔍 AUTOCOMPLETE FUNCTIONS
    # ───────────────────────────────────────────────────────────────

    async def owned_pet_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour les pets possédés."""
        player = self.data.get_player(interaction.user.id)
        choices = []
        
        for pet_id, qty in player.pets.items():
            pet = self.data.get_pet(pet_id)
            if pet:
                if current.lower() in pet.name.lower() or not current:
                    equipped = " ✓" if player.equipped_pet == pet_id else ""
                    display = f"{pet.emoji} {pet.name} (+{pet.drop_bonus*100:.1f}%){equipped}"
                    choices.append(app_commands.Choice(name=display[:100], value=pet.name))
        
        return choices[:25]

    # ───────────────────────────────────────────────────────────────
    # 🥚 COMMANDE OEUF MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="oeuf", description="🥚 Ouvre un œuf mystérieux pour obtenir un pet !")
    async def open_egg(self, interaction: discord.Interaction):
        """Ouvre un œuf avec animation moderne."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        egg_cost = self.data.get_egg_cost()
        
        if player.coins < egg_cost:
            embed = self._error_embed(
                "Pas assez de pièces",
                f"Tu as besoin de **{format_number(egg_cost)}** {Emojis.COIN}\n"
                f"Tu as seulement **{format_number(player.coins)}** {Emojis.COIN}"
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Animation d'ouverture moderne
        opening_embed = discord.Embed(
            title="🥚 Incubation en cours...",
            description=(
                f"```ansi\n"
                f"\u001b[1;33m╔{'═' * 30}╗\u001b[0m\n"
                f"\u001b[1;33m║\u001b[0m   ✨ L'ŒUF SE FISSURE... ✨    \u001b[1;33m║\u001b[0m\n"
                f"\u001b[1;33m╚{'═' * 30}╝\u001b[0m\n"
                f"```"
            ),
            color=Colors.LEGENDARY
        )
        message = await interaction.followup.send(embed=opening_embed)
        
        # Animation de progression
        for i in range(1, 6):
            await asyncio.sleep(0.4)
            progress = create_progress_bar(i, 5, 20)
            opening_embed.description = (
                f"```ansi\n"
                f"\u001b[1;33m╔{'═' * 30}╗\u001b[0m\n"
                f"\u001b[1;33m║\u001b[0m   🥚 ÉCLOSION EN COURS... 🐣   \u001b[1;33m║\u001b[0m\n"
                f"\u001b[1;33m╚{'═' * 30}╝\u001b[0m\n"
                f"```\n"
                f"{progress}"
            )
            await message.edit(embed=opening_embed)
        
        # Déduction des pièces et drop du pet
        player.coins -= egg_cost
        player.eggs_opened += 1
        
        # Sélection du pet
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
        is_new = pet.pet_id not in player.pets
        player.add_pet(pet.pet_id)
        self.data.save_player(player)
        
        # Embed de révélation moderne
        rarity_indicator = create_rarity_indicator(pet.rarity.name)
        
        reveal_embed = discord.Embed(
            title="🐣 Nouveau Compagnon !",
            color=COLORS.get(pet.rarity, Colors.SUCCESS)
        )
        
        new_badge = " 🆕" if is_new else ""
        reveal_embed.description = (
            f"```ansi\n"
            f"\u001b[1;32m╔{'═' * 32}╗\u001b[0m\n"
            f"\u001b[1;32m║\u001b[0m     🐣 ÉCLOSION RÉUSSIE ! 🐣      \u001b[1;32m║\u001b[0m\n"
            f"\u001b[1;32m╚{'═' * 32}╝\u001b[0m\n"
            f"```\n"
            f"{rarity_indicator}\n\n"
            f"{pet.emoji} **{pet.name}**{new_badge}"
        )
        
        reveal_embed.add_field(
            name="📖 Description",
            value=f"*{pet.description}*",
            inline=False
        )
        
        reveal_embed.add_field(
            name="⭐ Rareté",
            value=f"{pet.rarity.emoji} {pet.rarity.display_name}",
            inline=True
        )
        
        reveal_embed.add_field(
            name="📈 Bonus de drop",
            value=f"`+{pet.drop_bonus * 100:.1f}%`",
            inline=True
        )
        
        reveal_embed.add_field(
            name="💰 Restant",
            value=f"`{format_number(player.coins)}`",
            inline=True
        )
        
        reveal_embed.set_footer(
            text=f"🥚 {player.eggs_opened} œufs ouverts • /equiper-pet pour l'équiper",
            icon_url=self.bot.user.display_avatar.url
        )
        
        await message.edit(embed=reveal_embed)

    # ───────────────────────────────────────────────────────────────
    # 🐾 COMMANDE PETS MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="pets", description="🐾 Affiche ta collection de pets")
    async def show_pets(self, interaction: discord.Interaction):
        """Affiche les pets avec design moderne."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        if not player.pets:
            embed = discord.Embed(
                title=f"🐾 Collection de Pets",
                color=Colors.SECONDARY
            )
            embed.description = (
                f"```ansi\n"
                f"\u001b[0;33m╔{'═' * 28}╗\u001b[0m\n"
                f"\u001b[0;33m║\u001b[0m   AUCUN COMPAGNON... 😢    \u001b[0;33m║\u001b[0m\n"
                f"\u001b[0;33m╚{'═' * 28}╝\u001b[0m\n"
                f"```\n"
                f"💡 Utilise `/oeuf` pour obtenir ton premier pet !\n"
                f"{Emojis.COIN} Coût: **{format_number(self.data.get_egg_cost())}** pièces"
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"🐾 Tes Compagnons",
            color=Colors.SPECIAL
        )
        
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;35m╔{'═' * 30}╗\u001b[0m\n"
            f"\u001b[1;35m║\u001b[0m   🐾 {len(player.pets)} PETS COLLECTÉS 🐾    \u001b[1;35m║\u001b[0m\n"
            f"\u001b[1;35m╚{'═' * 30}╝\u001b[0m\n"
            f"```"
        )
        
        # Liste des pets
        pets_text = ""
        for pet_id, quantity in player.pets.items():
            pet = self.data.get_pet(pet_id)
            if pet:
                equipped_badge = " 🔹" if player.equipped_pet == pet_id else ""
                pets_text += f"{pet.emoji} **{pet.name}**{equipped_badge} `×{quantity}`\n"
                pets_text += f"└─ {pet.rarity.emoji} `+{pet.drop_bonus * 100:.1f}%` drop\n"
        
        embed.add_field(
            name="📋 Collection",
            value=pets_text or "*Aucun pet*",
            inline=False
        )
        
        # Bonus actuel
        if player.equipped_pet:
            current_pet = self.data.get_pet(player.equipped_pet)
            if current_pet:
                embed.add_field(
                    name="🔹 Compagnon Actif",
                    value=(
                        f"{current_pet.emoji} **{current_pet.name}**\n"
                        f"└─ Bonus: `+{current_pet.drop_bonus * 100:.1f}%` taux de drop"
                    ),
                    inline=False
                )
        else:
            embed.add_field(
                name="⚠️ Aucun pet équipé",
                value="💡 `/equiper-pet` pour activer un bonus !",
                inline=False
            )
        
        embed.set_footer(
            text=f"💰 {format_number(player.coins)} pièces │ 🥚 {player.eggs_opened} œufs ouverts",
            icon_url=self.bot.user.display_avatar.url
        )
        await interaction.followup.send(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 🐾 COMMANDE EQUIPER-PET MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="equiper-pet", description="🐾 Équipe un pet pour obtenir son bonus")
    @app_commands.describe(nom="Le nom du pet à équiper")
    @app_commands.autocomplete(nom=owned_pet_autocomplete)
    async def equip_pet(self, interaction: discord.Interaction, nom: str):
        """Équipe un pet avec feedback moderne."""
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
            embed = self._error_embed(
                "Pet introuvable",
                f"Aucun pet avec le nom **{nom}**."
            )
            await interaction.followup.send(embed=embed)
            return
        
        if target_pet.pet_id not in player.pets:
            embed = self._error_embed(
                "Pet non possédé",
                f"Tu ne possèdes pas {target_pet.emoji} **{target_pet.name}**."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Pet précédent
        old_pet = None
        if player.equipped_pet:
            old_pet = self.data.get_pet(player.equipped_pet)
        
        # Équiper le pet
        player.equip_pet(target_pet.pet_id)
        self.data.save_player(player)
        
        embed = discord.Embed(
            title="🐾 Pet Équipé !",
            color=COLORS.get(target_pet.rarity, Colors.SUCCESS)
        )
        
        embed.description = (
            f"```diff\n"
            f"+ {target_pet.name} t'accompagne !\n"
            f"```\n"
            f"{target_pet.emoji} **{target_pet.name}** est maintenant actif !"
        )
        
        # Comparaison avec l'ancien
        if old_pet and old_pet.pet_id != target_pet.pet_id:
            diff = target_pet.drop_bonus - old_pet.drop_bonus
            diff_text = f"+{diff*100:.1f}%" if diff > 0 else f"{diff*100:.1f}%"
            embed.add_field(
                name="🔄 Changement",
                value=f"{old_pet.emoji} ➜ {target_pet.emoji}\nDifférence: `{diff_text}`",
                inline=True
            )
        
        embed.add_field(
            name="📈 Bonus Actif",
            value=f"`+{target_pet.drop_bonus * 100:.1f}%` taux de drop",
            inline=True
        )
        
        embed.set_footer(
            text="💡 Ce bonus s'applique à tous tes coffres !",
            icon_url=self.bot.user.display_avatar.url
        )
        await interaction.followup.send(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 🐾 COMMANDE DESEQUIPER-PET MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="desequiper-pet", description="🐾 Retire le pet actuellement équipé")
    async def unequip_pet(self, interaction: discord.Interaction):
        """Déséquipe le pet avec feedback moderne."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        if not player.equipped_pet:
            embed = self._error_embed(
                "Aucun pet équipé",
                "Tu n'as pas de pet équipé actuellement."
            )
            await interaction.followup.send(embed=embed)
            return
        
        old_pet = self.data.get_pet(player.equipped_pet)
        player.unequip_pet()
        self.data.save_player(player)
        
        embed = discord.Embed(
            title="🐾 Pet Déséquipé",
            color=Colors.SECONDARY
        )
        
        embed.description = (
            f"```diff\n"
            f"- Bonus désactivé\n"
            f"```\n"
            f"{old_pet.emoji if old_pet else '🐾'} **{old_pet.name if old_pet else 'Ton pet'}** retourne se reposer."
        )
        
        embed.add_field(
            name="⚠️ Bonus perdu",
            value=f"`-{old_pet.drop_bonus * 100:.1f}%` taux de drop" if old_pet else "Aucun bonus",
            inline=False
        )
        
        embed.set_footer(
            text="💡 /equiper-pet pour réactiver un bonus",
            icon_url=self.bot.user.display_avatar.url
        )
        await interaction.followup.send(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 📊 COMMANDE INFO OEUFS
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="oeufs-info", description="🥚 Affiche les informations sur les œufs")
    async def egg_info(self, interaction: discord.Interaction):
        """Affiche les taux de drop des œufs."""
        egg_cost = self.data.get_egg_cost()
        egg_rates = self.data.get_egg_drop_rates()
        player = self.data.get_player(interaction.user.id)
        
        embed = discord.Embed(
            title="🥚 Informations Œufs",
            color=Colors.LEGENDARY
        )
        
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;33m╔{'═' * 30}╗\u001b[0m\n"
            f"\u001b[1;33m║\u001b[0m   🥚 TAUX D'ÉCLOSION 🐣        \u001b[1;33m║\u001b[0m\n"
            f"\u001b[1;33m╚{'═' * 30}╝\u001b[0m\n"
            f"```"
        )
        
        # Taux avec barres
        rates_text = ""
        rarity_emojis = {"MYTHIC": "🔥", "LEGENDARY": "⭐", "EPIC": "🌟", "RARE": "💎", "NORMAL": "📦"}
        rarity_names = {"MYTHIC": "Mythique", "LEGENDARY": "Légendaire", "EPIC": "Épique", "RARE": "Rare", "NORMAL": "Normal"}
        
        for rarity in ["MYTHIC", "LEGENDARY", "EPIC", "RARE", "NORMAL"]:
            rate = egg_rates.get(rarity, 0) * 100
            bar = create_progress_bar(rate, 60, 8, show_percentage=False)
            rates_text += f"{rarity_emojis[rarity]} **{rarity_names[rarity]}** {bar} `{rate:.2f}%`\n"
        
        embed.add_field(name="🎲 Probabilités", value=rates_text, inline=False)
        
        embed.add_field(
            name=f"{Emojis.COIN} Prix",
            value=f"`{format_number(egg_cost)}` pièces",
            inline=True
        )
        
        embed.add_field(
            name="💼 Ton solde",
            value=f"`{format_number(player.coins)}` pièces",
            inline=True
        )
        
        can_buy = player.coins // egg_cost if egg_cost > 0 else 0
        embed.add_field(
            name="🛒 Tu peux acheter",
            value=f"`{can_buy}` œufs",
            inline=True
        )
        
        embed.set_footer(
            text="💡 /oeuf pour ouvrir un œuf │ /pets pour ta collection",
            icon_url=self.bot.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 🛠️ HELPERS
    # ───────────────────────────────────────────────────────────────

    def _error_embed(self, title: str, description: str) -> discord.Embed:
        """Crée un embed d'erreur moderne."""
        return discord.Embed(
            title=f"{Emojis.ERROR} {title}",
            description=description,
            color=Colors.ERROR
        )


async def setup(bot: commands.Bot):
    pass
