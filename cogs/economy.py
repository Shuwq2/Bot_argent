"""
Cog gérant l'économie du bot : coffres, inventaire, vente d'objets.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from models import Chest, Rarity
from services import DataManager


class Economy(commands.Cog):
    """Cog pour le système d'économie et de collection."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager
        self.chest = Chest(self.data.get_all_items())

    # ==================== COMMANDE COFFRE ====================

    @app_commands.command(name="coffre", description="🎁 Ouvre un coffre pour obtenir un objet aléatoire")
    @app_commands.describe(payer="Payer 100 💰 pour un coffre supplémentaire si limite atteinte")
    async def open_chest(self, interaction: discord.Interaction, payer: Optional[bool] = False):
        """Ouvre un coffre et donne un objet aléatoire."""
        player = self.data.get_player(interaction.user.id)
        
        # Vérifier si le joueur peut ouvrir un coffre
        if not player.can_open_free_chest() and not payer:
            embed = discord.Embed(
                title="❌ Limite atteinte !",
                description=f"Tu as atteint ta limite de **{player.MAX_DAILY_CHESTS}** coffres gratuits aujourd'hui.\n\n"
                           f"💰 Solde actuel: **{player.coins}** pièces\n"
                           f"💸 Coût d'un coffre: **{player.CHEST_COST}** pièces\n\n"
                           f"Utilise `/coffre payer:True` pour payer un coffre supplémentaire,\n"
                           f"ou reviens demain !",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if payer and not player.can_open_free_chest():
            if not player.can_afford_chest():
                embed = discord.Embed(
                    title="❌ Pas assez de pièces !",
                    description=f"Tu as besoin de **{player.CHEST_COST}** 💰 pour acheter un coffre.\n"
                               f"Solde actuel: **{player.coins}** 💰\n\n"
                               f"Vends des objets avec `/vendre` pour gagner des pièces !",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Ouvrir le coffre
        success = player.open_chest(paid=payer and not player.can_open_free_chest())
        if not success:
            await interaction.response.send_message("❌ Erreur lors de l'ouverture du coffre.", ephemeral=True)
            return

        # Tirer un objet
        item = self.chest.open()
        if not item:
            await interaction.response.send_message("❌ Erreur: aucun objet disponible.", ephemeral=True)
            return

        # Ajouter l'objet à l'inventaire
        player.add_item(item.item_id)
        self.data.save_player(player)

        # Créer l'embed de récompense
        embed = self._create_reward_embed(item, player)
        await interaction.response.send_message(embed=embed)

    def _create_reward_embed(self, item, player) -> discord.Embed:
        """Crée l'embed d'affichage de la récompense."""
        # Couleur selon la rareté
        colors = {
            Rarity.NORMAL: discord.Color.light_grey(),
            Rarity.RARE: discord.Color.blue(),
            Rarity.EPIC: discord.Color.purple(),
            Rarity.LEGENDARY: discord.Color.gold(),
            Rarity.MYTHIC: discord.Color.red()
        }
        
        embed = discord.Embed(
            title="🎁 Coffre ouvert !",
            color=colors.get(item.rarity, discord.Color.greyple())
        )
        
        embed.add_field(
            name=f"{item.rarity.emoji} {item.name}",
            value=f"**Rareté:** {item.rarity.display_name}\n"
                  f"**Valeur:** {item.value} 💰\n"
                  f"**Catégorie:** {item.category}\n\n"
                  f"*{item.description}*",
            inline=False
        )
        
        embed.add_field(
            name="📊 Statistiques",
            value=f"Coffres restants: **{player.get_remaining_free_chests()}**/{player.MAX_DAILY_CHESTS}\n"
                  f"Solde: **{player.coins}** 💰",
            inline=False
        )
        
        return embed

    # ==================== COMMANDE INVENTAIRE ====================

    @app_commands.command(name="inventaire", description="📦 Affiche ton inventaire")
    @app_commands.describe(page="Page de l'inventaire (10 objets par page)")
    async def inventory(self, interaction: discord.Interaction, page: Optional[int] = 1):
        """Affiche l'inventaire du joueur."""
        player = self.data.get_player(interaction.user.id)
        
        if not player.inventory:
            embed = discord.Embed(
                title="📦 Inventaire vide",
                description="Tu n'as aucun objet.\nUtilise `/coffre` pour en obtenir !",
                color=discord.Color.grey()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Préparer les objets avec leurs détails
        items_list = []
        total_value = 0
        for item_id, quantity in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                items_list.append((item, quantity))
                total_value += item.value * quantity

        # Trier par rareté (du plus rare au moins rare)
        rarity_order = {Rarity.MYTHIC: 0, Rarity.LEGENDARY: 1, Rarity.EPIC: 2, Rarity.RARE: 3, Rarity.NORMAL: 4}
        items_list.sort(key=lambda x: rarity_order.get(x[0].rarity, 5))

        # Pagination
        items_per_page = 10
        total_pages = max(1, (len(items_list) + items_per_page - 1) // items_per_page)
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items_list[start_idx:end_idx]

        embed = discord.Embed(
            title=f"📦 Inventaire de {interaction.user.display_name}",
            color=discord.Color.blue()
        )

        items_text = ""
        for item, quantity in page_items:
            items_text += f"{item.rarity.emoji} **{item.name}** x{quantity} - {item.value * quantity} 💰\n"

        embed.add_field(name="Objets", value=items_text or "Aucun objet", inline=False)
        embed.add_field(
            name="💰 Résumé",
            value=f"**Objets uniques:** {len(player.inventory)}\n"
                  f"**Valeur totale:** {total_value} 💰\n"
                  f"**Solde:** {player.coins} 💰",
            inline=False
        )
        embed.set_footer(text=f"Page {page}/{total_pages} • Utilise /inventaire page:X pour naviguer")

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE VENDRE ====================

    @app_commands.command(name="vendre", description="💸 Vend un objet de ton inventaire")
    @app_commands.describe(
        objet="Nom de l'objet à vendre",
        quantite="Nombre d'objets à vendre (défaut: 1)"
    )
    async def sell(self, interaction: discord.Interaction, objet: str, quantite: Optional[int] = 1):
        """Vend un objet de l'inventaire."""
        player = self.data.get_player(interaction.user.id)
        
        # Rechercher l'objet par son nom
        item = None
        for item_id in player.inventory:
            potential_item = self.data.get_item(item_id)
            if potential_item and potential_item.name.lower() == objet.lower():
                item = potential_item
                break

        if not item:
            embed = discord.Embed(
                title="❌ Objet introuvable",
                description=f"Tu n'as pas d'objet nommé **{objet}** dans ton inventaire.\n"
                           f"Utilise `/inventaire` pour voir tes objets.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Vérifier la quantité
        available = player.inventory.get(item.item_id, 0)
        if quantite <= 0 or quantite > available:
            embed = discord.Embed(
                title="❌ Quantité invalide",
                description=f"Tu as **{available}** {item.name}.\n"
                           f"Tu ne peux pas en vendre **{quantite}**.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Effectuer la vente
        total_coins = item.value * quantite
        old_balance = player.coins
        player.sell_item(item.item_id, item.value, quantite)
        self.data.save_player(player)

        embed = discord.Embed(
            title="💸 Vente réussie !",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Transaction",
            value=f"{item.rarity.emoji} **{item.name}** x{quantite}\n"
                  f"Prix unitaire: {item.value} 💰\n"
                  f"**Total: +{total_coins} 💰**",
            inline=False
        )
        embed.add_field(
            name="💰 Nouveau solde",
            value=f"{old_balance} → **{player.coins}** 💰",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE VENDRE TOUT ====================

    @app_commands.command(name="vendretout", description="💸 Vend tous les objets d'une rareté")
    @app_commands.describe(rarete="Rareté des objets à vendre (normal, rare, epic, légendaire, mythique)")
    @app_commands.choices(rarete=[
        app_commands.Choice(name="Normal ⬜", value="NORMAL"),
        app_commands.Choice(name="Rare 🟦", value="RARE"),
        app_commands.Choice(name="Epic 🟪", value="EPIC"),
        app_commands.Choice(name="Légendaire 🟨", value="LEGENDARY"),
        app_commands.Choice(name="Mythique 🟥", value="MYTHIC")
    ])
    async def sell_all(self, interaction: discord.Interaction, rarete: str):
        """Vend tous les objets d'une rareté spécifique."""
        player = self.data.get_player(interaction.user.id)
        
        try:
            target_rarity = Rarity[rarete]
        except KeyError:
            await interaction.response.send_message("❌ Rareté invalide.", ephemeral=True)
            return

        # Trouver tous les objets de cette rareté
        items_to_sell = []
        for item_id, quantity in list(player.inventory.items()):
            item = self.data.get_item(item_id)
            if item and item.rarity == target_rarity:
                items_to_sell.append((item, quantity))

        if not items_to_sell:
            embed = discord.Embed(
                title="❌ Aucun objet à vendre",
                description=f"Tu n'as aucun objet {target_rarity.emoji} **{target_rarity.display_name}**.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Calculer et effectuer la vente
        total_items = 0
        total_coins = 0
        old_balance = player.coins

        for item, quantity in items_to_sell:
            player.sell_item(item.item_id, item.value, quantity)
            total_items += quantity
            total_coins += item.value * quantity

        self.data.save_player(player)

        embed = discord.Embed(
            title="💸 Vente massive réussie !",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Transaction",
            value=f"{target_rarity.emoji} **{total_items}** objets {target_rarity.display_name} vendus\n"
                  f"**Total: +{total_coins} 💰**",
            inline=False
        )
        embed.add_field(
            name="💰 Nouveau solde",
            value=f"{old_balance} → **{player.coins}** 💰",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE PROFIL ====================

    @app_commands.command(name="profil", description="👤 Affiche ton profil et tes statistiques")
    @app_commands.describe(membre="Membre dont afficher le profil (optionnel)")
    async def profile(self, interaction: discord.Interaction, membre: Optional[discord.Member] = None):
        """Affiche le profil d'un joueur."""
        target = membre or interaction.user
        player = self.data.get_player(target.id)

        # Calculer les statistiques
        total_items = sum(player.inventory.values())
        unique_items = len(player.inventory)
        
        # Valeur totale de l'inventaire
        inventory_value = 0
        rarity_counts = {r: 0 for r in Rarity}
        for item_id, quantity in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                inventory_value += item.value * quantity
                rarity_counts[item.rarity] += quantity

        embed = discord.Embed(
            title=f"👤 Profil de {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="💰 Économie",
            value=f"**Solde:** {player.coins} 💰\n"
                  f"**Valeur inventaire:** {inventory_value} 💰\n"
                  f"**Richesse totale:** {player.coins + inventory_value} 💰",
            inline=True
        )

        embed.add_field(
            name="📦 Collection",
            value=f"**Objets totaux:** {total_items}\n"
                  f"**Objets uniques:** {unique_items}\n"
                  f"**Objets vendus:** {player.total_items_sold}",
            inline=True
        )

        embed.add_field(
            name="🎁 Coffres",
            value=f"**Ouverts aujourd'hui:** {player.daily_chests_opened}/{player.MAX_DAILY_CHESTS}\n"
                  f"**Total ouverts:** {player.total_chests_opened}",
            inline=True
        )

        # Répartition par rareté
        rarity_text = ""
        for rarity in Rarity:
            if rarity_counts[rarity] > 0:
                rarity_text += f"{rarity.emoji} {rarity.display_name}: {rarity_counts[rarity]}\n"
        
        if rarity_text:
            embed.add_field(name="📊 Répartition", value=rarity_text, inline=False)

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE CLASSEMENT ====================

    @app_commands.command(name="classement", description="🏆 Affiche le classement des joueurs")
    @app_commands.describe(type="Type de classement")
    @app_commands.choices(type=[
        app_commands.Choice(name="💰 Richesse (pièces)", value="coins"),
        app_commands.Choice(name="📦 Collection (objets uniques)", value="collection")
    ])
    async def leaderboard(self, interaction: discord.Interaction, type: Optional[str] = "coins"):
        """Affiche le classement des joueurs."""
        if type == "collection":
            players = self.data.get_collection_leaderboard(10)
            title = "🏆 Classement des collectionneurs"
        else:
            players = self.data.get_leaderboard(10)
            title = "🏆 Classement des plus riches"

        embed = discord.Embed(title=title, color=discord.Color.gold())

        if not players:
            embed.description = "Aucun joueur n'a encore joué !"
            await interaction.response.send_message(embed=embed)
            return

        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]

        for i, player in enumerate(players):
            try:
                user = await self.bot.fetch_user(player.user_id)
                username = user.display_name
            except:
                username = f"Utilisateur #{player.user_id}"

            medal = medals[i] if i < 3 else f"**{i + 1}.**"
            
            if type == "collection":
                value = len(player.inventory)
                leaderboard_text += f"{medal} {username} - {value} objets uniques\n"
            else:
                leaderboard_text += f"{medal} {username} - {player.coins} 💰\n"

        embed.description = leaderboard_text
        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE TAUX ====================

    @app_commands.command(name="taux", description="📊 Affiche les taux de drop des coffres")
    async def drop_rates(self, interaction: discord.Interaction):
        """Affiche les taux de drop."""
        embed = discord.Embed(
            title="📊 Taux de drop des coffres",
            description="Voici les probabilités d'obtenir chaque rareté :",
            color=discord.Color.blue()
        )

        for rarity in Rarity:
            percentage = rarity.drop_rate * 100
            bar_length = int(percentage / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            embed.add_field(
                name=f"{rarity.emoji} {rarity.display_name}",
                value=f"`{bar}` {percentage:.1f}%\nValeur base: {rarity.base_value} 💰",
                inline=False
            )

        embed.set_footer(text="Les objets de chaque rareté ont des valeurs différentes !")
        await interaction.response.send_message(embed=embed)

    # ==================== AUTOCOMPLÉTION ====================

    @sell.autocomplete('objet')
    async def sell_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplétion pour la commande vendre."""
        player = self.data.get_player(interaction.user.id)
        choices = []

        for item_id in player.inventory:
            item = self.data.get_item(item_id)
            if item and (not current or current.lower() in item.name.lower()):
                quantity = player.inventory[item_id]
                choices.append(
                    app_commands.Choice(
                        name=f"{item.rarity.emoji} {item.name} (x{quantity}) - {item.value} 💰",
                        value=item.name
                    )
                )

        return choices[:25]  # Discord limite à 25 choix


async def setup(bot: commands.Bot):
    """Setup function pour charger le cog."""
    # Le data_manager sera injecté depuis bot.py
    pass
