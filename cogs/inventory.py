RARITY_IMAGES = {
    "normal": "https://imgur.com/OX8kBYX",      # Vert
    "rare": "https://imgur.com/5IGZUZk.png",        # Bleu
    "epic": "https://imgur.com/lgNP9Cg.png",        # Violet
    "legendary": "https://imgur.com/V3Nw9TL.png",   # Or
    "mythic": "https://imgur.com/EZuex8X.png",      # Rouge
}
"""
Cog gérant l'inventaire et les ventes avec design ultra-moderne.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

from models import Rarity
from services import DataManager
from utils import COLORS
from utils.styles import (
    Colors, Emojis,
    create_progress_bar, create_stat_bar,
    create_rarity_indicator, format_number
)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎒 COG INVENTAIRE - GESTION MODERNE
# ═══════════════════════════════════════════════════════════════════════════════

class Inventory(commands.Cog):
    """Système d'inventaire et ventes ultra-moderne."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager

    # ───────────────────────────────────────────────────────────────
    # 🔍 AUTOCOMPLETE FUNCTIONS
    # ───────────────────────────────────────────────────────────────

    async def item_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour les items de l'inventaire."""
        player = self.data.get_player(interaction.user.id)
        choices = []
        
        for item_id, qty in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                if current.lower() in item.name.lower() or not current:
                    display = f"{item.rarity.emoji} {item.name} (×{qty}) - {format_number(item.value)}"
                    choices.append(app_commands.Choice(name=display[:100], value=item.name))
        
        # Trier par rareté (mythic en premier)
        rarity_order = {"MYTHIC": 0, "LEGENDARY": 1, "EPIC": 2, "RARE": 3, "NORMAL": 4}
        choices.sort(key=lambda c: rarity_order.get(
            next((self.data.get_item(iid).rarity.name for iid, _ in player.inventory.items() 
                  if self.data.get_item(iid) and self.data.get_item(iid).name == c.value), "NORMAL"), 5
        ))
        
        return choices[:25]

    # ───────────────────────────────────────────────────────────────
    # 🎒 COMMANDE INVENTAIRE MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="inventaire", description="🎒 Affiche ta collection d'objets")
    @app_commands.describe(
        page="Page de l'inventaire",
        rarete="Filtrer par rareté"
    )
    @app_commands.choices(rarete=[
        app_commands.Choice(name="🔥 Mythique", value="MYTHIC"),
        app_commands.Choice(name="⭐ Légendaire", value="LEGENDARY"),
        app_commands.Choice(name="🌟 Épique", value="EPIC"),
        app_commands.Choice(name="💎 Rare", value="RARE"),
        app_commands.Choice(name="📦 Normal", value="NORMAL"),
    ])
    async def inventory(
        self, 
        interaction: discord.Interaction, 
        page: Optional[int] = 1,
        rarete: Optional[str] = None
    ):
        """Affiche l'inventaire avec design moderne."""
        player = self.data.get_player(interaction.user.id)
        
        if not player.inventory:
            embed = discord.Embed(
                title=f"{Emojis.INVENTORY} Inventaire",
                color=Colors.SECONDARY
            )
            embed.description = (
                f"```ansi\n"
                f"\u001b[0;33m╔{'═' * 30}╗\u001b[0m\n"
                f"\u001b[0;33m║\u001b[0m      📦 INVENTAIRE VIDE 📦      \u001b[0;33m║\u001b[0m\n"
                f"\u001b[0;33m╚{'═' * 30}╝\u001b[0m\n"
                f"```\n"
                f"💡 Utilise `/coffre` pour obtenir des objets !"
            )
            await interaction.response.send_message(embed=embed)
            return

        # Préparer les données
        items_list = []
        total_value = 0
        rarity_counts = {r: 0 for r in Rarity}
        
        for item_id, quantity in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                # Appliquer le filtre de rareté si spécifié
                if rarete and item.rarity.name != rarete:
                    continue
                items_list.append((item, quantity))
                total_value += item.value * quantity
                rarity_counts[item.rarity] += quantity

        if not items_list and rarete:
            embed = self._error_embed(
                "Aucun objet",
                f"Tu n'as aucun objet de rareté **{Rarity[rarete].display_name}**."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Trier par rareté puis par valeur
        rarity_order = {Rarity.MYTHIC: 0, Rarity.LEGENDARY: 1, Rarity.EPIC: 2, Rarity.RARE: 3, Rarity.NORMAL: 4}
        items_list.sort(key=lambda x: (rarity_order.get(x[0].rarity, 5), -x[0].value))

        # Pagination
        items_per_page = 8
        total_pages = max(1, (len(items_list) + items_per_page - 1) // items_per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * items_per_page
        page_items = items_list[start_idx:start_idx + items_per_page]

        # Couleur selon la meilleure rareté
        best_rarity = min(items_list, key=lambda x: rarity_order.get(x[0].rarity, 5))[0].rarity if items_list else Rarity.NORMAL
        color = COLORS.get(best_rarity, Colors.PRIMARY)

        embed = discord.Embed(
            title=f"{Emojis.INVENTORY} Inventaire",
            color=color
        )

        # Header avec filtre actif
        filter_text = f" │ Filtre: {Rarity[rarete].emoji}" if rarete else ""
        embed.description = (
            f"```ansi\n"
            f"\u001b[0;34m╔{'═' * 34}╗\u001b[0m\n"
            f"\u001b[0;34m║\u001b[0m  📦 {len(items_list)} objets uniques{filter_text:>12} \u001b[0;34m║\u001b[0m\n"
            f"\u001b[0;34m╚{'═' * 34}╝\u001b[0m\n"
            f"```"
        )

        # Liste des objets avec design moderne
        items_text = ""
        for item, qty in page_items:
            value_total = item.value * qty
            items_text += f"{item.rarity.emoji} **{item.name}** `×{qty}`\n"
            items_text += f"└─ {Emojis.COIN} `{format_number(value_total)}`\n"

        embed.add_field(
            name=f"📦 Objets",
            value=items_text or "*Aucun objet*",
            inline=False
        )

        # Stats par rareté avec barres
        if not rarete:
            max_count = max(rarity_counts.values()) if any(rarity_counts.values()) else 1
            rarity_lines = []
            for rarity in [Rarity.MYTHIC, Rarity.LEGENDARY, Rarity.EPIC, Rarity.RARE, Rarity.NORMAL]:
                count = rarity_counts[rarity]
                if count > 0:
                    bar = create_stat_bar(count, max_count, 6)
                    rarity_lines.append(f"{rarity.emoji} {bar} `{count}`")
            
            if rarity_lines:
                embed.add_field(
                    name="📊 Répartition",
                    value="\n".join(rarity_lines),
                    inline=True
                )

        # Valeur et solde
        embed.add_field(
            name=f"{Emojis.COIN} Valeur",
            value=f"📦 `{format_number(total_value)}`\n💰 `{format_number(player.coins)}`",
            inline=True
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Footer avec pagination
        nav_text = ""
        if total_pages > 1:
            nav_text = f"📄 Page {page}/{total_pages}"
            if page < total_pages:
                nav_text += f" │ /inventaire page:{page + 1}"
        else:
            nav_text = "💡 /vendre <objet> pour vendre"
        
        embed.set_footer(text=nav_text, icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 💸 COMMANDE VENDRE MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="vendre", description="💸 Vend un objet de ton inventaire")
    @app_commands.describe(
        objet="Nom de l'objet à vendre",
        quantite="Quantité à vendre (défaut: 1)"
    )
    @app_commands.autocomplete(objet=item_autocomplete)
    async def sell(self, interaction: discord.Interaction, objet: str, quantite: Optional[int] = 1):
        """Vend un objet avec feedback moderne."""
        player = self.data.get_player(interaction.user.id)
        
        # Rechercher l'objet
        item = None
        for item_id in player.inventory:
            potential = self.data.get_item(item_id)
            if potential and potential.name.lower() == objet.lower():
                item = potential
                break

        if not item:
            embed = self._error_embed(
                "Objet Introuvable",
                f"**{objet}** n'est pas dans ton inventaire.\n\n"
                f"💡 Utilise `/inventaire` pour voir tes objets."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        available = player.inventory.get(item.item_id, 0)
        if quantite <= 0 or quantite > available:
            embed = self._error_embed(
                "Quantité Invalide",
                f"```diff\n"
                f"- Demandé: ×{quantite}\n"
                f"+ Disponible: ×{available}\n"
                f"```"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Calculer les gains avec bonus
        coin_bonus = self.data.calculate_total_coin_bonus(player)
        base_total = item.value * quantite
        bonus_coins = int(base_total * coin_bonus)
        total = base_total + bonus_coins
        
        old_balance = player.coins
        player.remove_item(item.item_id, quantite)
        player.add_coins(total)
        player.total_items_sold += quantite
        self.data.save_player(player)

        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} Vente Réussie !",
            color=Colors.SUCCESS
        )

        # Item vendu
        rarity_indicator = create_rarity_indicator(item.rarity.name)
        embed.description = (
            f"{rarity_indicator}\n\n"
            f"{item.rarity.emoji} **{item.name}** `×{quantite}`\n"
            f"└─ Prix unitaire: `{format_number(item.value)}`"
        )

        # Gains
        gain_text = f"+ {format_number(base_total)} pièces"
        if bonus_coins > 0:
            gain_text += f"\n+ {format_number(bonus_coins)} bonus ({coin_bonus*100:.0f}%)"
        
        embed.add_field(
            name=f"{Emojis.COIN} Gains",
            value=f"```diff\n{gain_text}\n```",
            inline=True
        )

        # Solde
        profit_bar = create_stat_bar(total, old_balance + total, 8)
        embed.add_field(
            name="💼 Solde",
            value=(
                f"Avant: `{format_number(old_balance)}`\n"
                f"Après: `{format_number(player.coins)}`\n"
                f"{profit_bar} +{format_number(total)}"
            ),
            inline=True
        )

        embed.set_footer(
            text="💡 Continue à vendre pour acheter des coffres !",
            icon_url=self.bot.user.display_avatar.url
        )
        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 💸 COMMANDE VENDRE TOUT MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="vendretout", description="💸 Vend tous les objets d'une rareté")
    @app_commands.describe(rarete="Rareté des objets à vendre")
    @app_commands.choices(rarete=[
        app_commands.Choice(name="📦 Normal - Tous les objets communs", value="NORMAL"),
        app_commands.Choice(name="💎 Rare - Tous les objets rares", value="RARE"),
        app_commands.Choice(name="🌟 Épique - Tous les objets épiques", value="EPIC"),
        app_commands.Choice(name="⭐ Légendaire - ⚠️ Attention !", value="LEGENDARY"),
        app_commands.Choice(name="🔥 Mythique - ⚠️ Très précieux !", value="MYTHIC")
    ])
    async def sell_all(self, interaction: discord.Interaction, rarete: str):
        """Vend tous les objets d'une rareté avec confirmation visuelle."""
        player = self.data.get_player(interaction.user.id)
        target_rarity = Rarity[rarete]

        items_to_sell = []
        for item_id, qty in list(player.inventory.items()):
            item = self.data.get_item(item_id)
            if item and item.rarity == target_rarity:
                items_to_sell.append((item, qty))

        if not items_to_sell:
            embed = self._error_embed(
                "Aucun Objet",
                f"Tu n'as aucun objet {target_rarity.emoji} **{target_rarity.display_name}**."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        total_items = 0
        base_coins = 0
        old_balance = player.coins

        for item, qty in items_to_sell:
            player.remove_item(item.item_id, qty)
            total_items += qty
            base_coins += item.value * qty

        # Bonus de vente
        coin_bonus = self.data.calculate_total_coin_bonus(player)
        bonus_coins = int(base_coins * coin_bonus)
        total_coins = base_coins + bonus_coins
        
        player.add_coins(total_coins)
        player.total_items_sold += total_items
        self.data.save_player(player)

        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} Vente Massive !",
            color=COLORS.get(target_rarity, Colors.SUCCESS)
        )

        embed.description = (
            f"```ansi\n"
            f"\u001b[1;32m╔{'═' * 32}╗\u001b[0m\n"
            f"\u001b[1;32m║\u001b[0m     💰 TRANSACTION RÉUSSIE 💰     \u001b[1;32m║\u001b[0m\n"
            f"\u001b[1;32m╚{'═' * 32}╝\u001b[0m\n"
            f"```"
        )

        embed.add_field(
            name="📦 Objets Vendus",
            value=f"{target_rarity.emoji} **{total_items}** objets {target_rarity.display_name}",
            inline=False
        )

        # Gains détaillés
        gain_text = f"+ {format_number(base_coins)} pièces"
        if bonus_coins > 0:
            gain_text += f"\n+ {format_number(bonus_coins)} bonus ({coin_bonus*100:.0f}%)"

        embed.add_field(
            name=f"{Emojis.COIN} Gains",
            value=f"```diff\n{gain_text}\n```",
            inline=True
        )
        
        embed.add_field(
            name="💼 Solde",
            value=(
                f"Avant: `{format_number(old_balance)}`\n"
                f"Après: `{format_number(player.coins)}`"
            ),
            inline=True
        )

        embed.set_footer(
            text=f"🏷️ Total vendus: {player.total_items_sold}",
            icon_url=self.bot.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # � COMMANDE MANGER/SOIGNER
    # ───────────────────────────────────────────────────────────────

    async def food_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour la nourriture et potions uniquement."""
        player = self.data.get_player(interaction.user.id)
        choices = []
        
        for item_id, qty in player.inventory.items():
            item = self.data.get_item(item_id)
            if item and item.category in ["Nourriture", "Potions"]:
                if current.lower() in item.name.lower() or not current:
                    display = f"{item.rarity.emoji} {item.name} (×{qty})"
                    choices.append(app_commands.Choice(name=display[:100], value=item.name))
        
        return choices[:25]

    @app_commands.command(name="manger", description="🍖 Consomme de la nourriture ou une potion pour te soigner")
    @app_commands.describe(item="Nourriture ou potion à consommer")
    @app_commands.autocomplete(item=food_autocomplete)
    async def manger(self, interaction: discord.Interaction, item: str):
        """Consomme un item pour restaurer des PV."""
        player = self.data.get_player(interaction.user.id)
        
        # Trouver l'item par nom
        target_item = None
        target_item_id = None
        for item_id, qty in player.inventory.items():
            found_item = self.data.get_item(item_id)
            if found_item and found_item.name.lower() == item.lower():
                target_item = found_item
                target_item_id = item_id
                break
        
        if not target_item:
            embed = self._error_embed(
                "Item introuvable",
                f"Tu n'as pas **{item}** dans ton inventaire !"
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Vérifier si c'est de la nourriture ou une potion
        if target_item.category not in ["Nourriture", "Potions"]:
            embed = self._error_embed(
                "Item non consommable",
                f"**{target_item.name}** n'est pas de la nourriture ou une potion !\n"
                f"Catégorie: {target_item.category}"
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Calculer le soin selon la rareté
        healing_values = {
            "NORMAL": 20,
            "RARE": 50,
            "EPIC": 120,
            "LEGENDARY": 300,
            "MYTHIC": 999  # Full heal pratiquement
        }
        
        # Les potions soignent plus
        base_heal = healing_values.get(target_item.rarity.name, 20)
        if target_item.category == "Potions":
            base_heal = int(base_heal * 1.5)  # +50% pour les potions
        
        # Mettre à jour les stats d'équipement pour avoir le bon max_hp
        player.update_equipment_stats(self.data)
        
        # PV actuels et max
        old_hp = player.current_hp
        max_hp = player.get_max_hp()
        
        # Appliquer le soin
        player.current_hp = min(max_hp, old_hp + base_heal)
        actual_heal = player.current_hp - old_hp
        
        # Retirer l'item de l'inventaire
        player.inventory[target_item_id] -= 1
        if player.inventory[target_item_id] <= 0:
            del player.inventory[target_item_id]
        
        # Sauvegarder
        self.data.save_player(player)
        
        # Créer l'embed de résultat
        if target_item.category == "Potions":
            emoji = "🧪"
            action = "bu"
            title = "Potion consommée !"
        else:
            emoji = "🍖"
            action = "mangé"
            title = "Miam miam !"
        
        # Couleur selon le soin
        if actual_heal >= 200:
            color = Colors.LEGENDARY
        elif actual_heal >= 100:
            color = Colors.EPIC
        elif actual_heal >= 50:
            color = Colors.RARE
        else:
            color = Colors.SUCCESS
        
        embed = discord.Embed(
            title=f"{emoji} {title}",
            color=color
        )
        
        # Barre de vie
        hp_percent = player.current_hp / max_hp
        hp_bar = create_progress_bar(hp_percent, length=15)
        
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;32m╔{'═' * 30}╗\u001b[0m\n"
            f"\u001b[1;32m║\u001b[0m  Tu as {action} {target_item.rarity.emoji} {target_item.name}  \u001b[1;32m║\u001b[0m\n"
            f"\u001b[1;32m╚{'═' * 30}╝\u001b[0m\n"
            f"```"
        )
        
        embed.add_field(
            name="❤️ Points de vie",
            value=(
                f"```diff\n"
                f"- Avant: {old_hp}/{max_hp} PV\n"
                f"+ Après: {player.current_hp}/{max_hp} PV\n"
                f"+ Soin: +{actual_heal} PV\n"
                f"```\n"
                f"{hp_bar} **{player.current_hp}/{max_hp}**"
            ),
            inline=False
        )
        
        if actual_heal < base_heal:
            embed.add_field(
                name="💡 Info",
                value=f"Tu étais presque full HP ! (Soin max: +{base_heal})",
                inline=False
            )
        
        # Quantité restante
        remaining = player.inventory.get(target_item_id, 0)
        embed.set_footer(
            text=f"Il te reste {remaining} {target_item.name}" if remaining > 0 else f"Tu n'as plus de {target_item.name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # �🏪 COMMANDE BOUTIQUE MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="boutique", description="🏪 Affiche la boutique du serveur")
    async def shop(self, interaction: discord.Interaction):
        """Affiche la boutique avec design moderne."""
        player = self.data.get_player(interaction.user.id)
        egg_cost = self.data.get_egg_cost()
        
        embed = discord.Embed(
            title=f"{Emojis.SHOP} Boutique",
            color=Colors.LEGENDARY
        )

        embed.description = (
            f"```ansi\n"
            f"\u001b[1;33m╔{'═' * 32}╗\u001b[0m\n"
            f"\u001b[1;33m║\u001b[0m     🏪 BIENVENUE À LA BOUTIQUE 🏪   \u001b[1;33m║\u001b[0m\n"
            f"\u001b[1;33m╚{'═' * 32}╝\u001b[0m\n"
            f"```\n"
            f"{Emojis.COIN} Ton solde: **{format_number(player.coins)}** pièces"
        )

        # Articles disponibles
        can_afford_chest = "✅" if player.coins >= player.CHEST_COST else "❌"
        can_afford_egg = "✅" if player.coins >= egg_cost else "❌"

        embed.add_field(
            name="🎁 Coffre Bonus",
            value=(
                f"Prix: **{format_number(player.CHEST_COST)}** {Emojis.COIN}\n"
                f"Status: {can_afford_chest}\n"
                f"```\n/coffre payer:True\n```"
            ),
            inline=True
        )

        embed.add_field(
            name="🥚 Œuf Mystérieux",
            value=(
                f"Prix: **{format_number(egg_cost)}** {Emojis.COIN}\n"
                f"Status: {can_afford_egg}\n"
                f"```\n/oeuf\n```"
            ),
            inline=True
        )

        # Info supplémentaire
        embed.add_field(
            name="💡 Conseils",
            value=(
                "▸ Les coffres peuvent contenir des objets **Mythiques** !\n"
                "▸ Les œufs donnent des **pets** qui boostent tes drops\n"
                "▸ Vends des objets avec `/vendre` pour gagner des pièces"
            ),
            inline=False
        )

        embed.set_footer(
            text="💰 Utilise les commandes pour acheter !",
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
