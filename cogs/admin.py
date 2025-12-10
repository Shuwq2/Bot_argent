"""
Cog d'administration pour la gestion du bot économie.
Commandes réservées aux administrateurs.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from services import DataManager


class Admin(commands.Cog):
    """Commandes d'administration pour gérer l'économie."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager

    # ══════════════════════════════════════════════════════════════
    # 🔧 VÉRIFICATION ADMIN
    # ══════════════════════════════════════════════════════════════

    def is_admin():
        """Vérificateur de permission administrateur."""
        async def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    # ══════════════════════════════════════════════════════════════
    # 📦 DONNER UN OBJET
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="admin-give", description="🎁 [ADMIN] Donner un objet à un joueur")
    @app_commands.describe(
        joueur="Joueur cible",
        objet="Nom ou ID de l'objet",
        quantite="Quantité à donner"
    )
    @is_admin()
    async def admin_give(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member,
        objet: str,
        quantite: Optional[int] = 1
    ):
        """Donne un objet à un joueur."""
        # Chercher l'objet par nom ou ID
        item = None
        for i in self.data.get_all_items():
            if i.name.lower() == objet.lower() or i.item_id == objet:
                item = i
                break

        if not item:
            embed = discord.Embed(
                title="❌ Objet Introuvable",
                description=f"L'objet **{objet}** n'existe pas.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        player = self.data.get_player(joueur.id)
        player.add_item(item.item_id, quantite)
        self.data.save_player(player)

        embed = discord.Embed(
            title="✅ Objet Donné",
            color=0x2ecc71
        )
        embed.add_field(
            name="📦 Objet",
            value=f"{item.rarity.emoji} **{item.name}** `×{quantite}`",
            inline=True
        )
        embed.add_field(
            name="👤 Destinataire",
            value=joueur.mention,
            inline=True
        )
        embed.add_field(
            name="👮 Admin",
            value=interaction.user.mention,
            inline=True
        )
        embed.set_footer(text=f"ID: {item.item_id}")

        await interaction.response.send_message(embed=embed)

    @admin_give.autocomplete('objet')
    async def give_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplétion pour les objets."""
        choices = []
        for item in self.data.get_all_items():
            if not current or current.lower() in item.name.lower():
                choices.append(
                    app_commands.Choice(
                        name=f"{item.rarity.emoji} {item.name} ({item.rarity.display_name})",
                        value=item.item_id
                    )
                )
        return choices[:25]

    # ══════════════════════════════════════════════════════════════
    # 🗑️ RETIRER UN OBJET
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="admin-remove", description="🗑️ [ADMIN] Retirer un objet d'un joueur")
    @app_commands.describe(
        joueur="Joueur cible",
        objet="Nom ou ID de l'objet",
        quantite="Quantité à retirer"
    )
    @is_admin()
    async def admin_remove(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member,
        objet: str,
        quantite: Optional[int] = 1
    ):
        """Retire un objet d'un joueur."""
        player = self.data.get_player(joueur.id)

        # Chercher l'objet
        item = None
        for i in self.data.get_all_items():
            if i.name.lower() == objet.lower() or i.item_id == objet:
                item = i
                break

        if not item:
            embed = discord.Embed(
                title="❌ Objet Introuvable",
                description=f"L'objet **{objet}** n'existe pas.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        available = player.inventory.get(item.item_id, 0)
        if available < quantite:
            embed = discord.Embed(
                title="❌ Quantité Insuffisante",
                description=f"**{joueur.display_name}** n'a que `{available}×` {item.name}.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        player.remove_item(item.item_id, quantite)
        self.data.save_player(player)

        embed = discord.Embed(
            title="✅ Objet Retiré",
            color=0xe74c3c
        )
        embed.add_field(
            name="📦 Objet",
            value=f"{item.rarity.emoji} **{item.name}** `×{quantite}`",
            inline=True
        )
        embed.add_field(
            name="👤 Joueur",
            value=joueur.mention,
            inline=True
        )
        embed.add_field(
            name="👮 Admin",
            value=interaction.user.mention,
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    @admin_remove.autocomplete('objet')
    async def remove_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplétion pour les objets."""
        return await self.give_autocomplete(interaction, current)

    # ══════════════════════════════════════════════════════════════
    # 👁️ VOIR L'INVENTAIRE
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="admin-inventaire", description="👁️ [ADMIN] Voir l'inventaire d'un joueur")
    @app_commands.describe(joueur="Joueur cible", page="Page de l'inventaire")
    @is_admin()
    async def admin_inventory(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member,
        page: Optional[int] = 1
    ):
        """Affiche l'inventaire détaillé d'un joueur."""
        player = self.data.get_player(joueur.id)

        if not player.inventory:
            embed = discord.Embed(
                title=f"📦 Inventaire de {joueur.display_name}",
                description="```\nInventaire vide\n```",
                color=0x3498db
            )
            embed.add_field(name="💰 Pièces", value=f"`{player.coins:,}`", inline=True)
            embed.add_field(name="📊 Coffres", value=f"`{player.total_chests_opened}`", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Préparer les données
        items_list = []
        total_value = 0

        for item_id, qty in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                items_list.append((item, qty))
                total_value += item.value * qty

        # Trier par rareté (mythic en premier)
        from models import Rarity
        rarity_order = {Rarity.MYTHIC: 0, Rarity.LEGENDARY: 1, Rarity.EPIC: 2, Rarity.RARE: 3, Rarity.NORMAL: 4}
        items_list.sort(key=lambda x: rarity_order.get(x[0].rarity, 5))

        # Pagination
        items_per_page = 15
        total_pages = max(1, (len(items_list) + items_per_page - 1) // items_per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * items_per_page
        page_items = items_list[start_idx:start_idx + items_per_page]

        embed = discord.Embed(
            title=f"📦 Inventaire de {joueur.display_name}",
            color=0x3498db
        )
        embed.set_thumbnail(url=joueur.display_avatar.url)

        # Liste des objets
        items_text = ""
        for item, qty in page_items:
            items_text += f"{item.rarity.emoji} **{item.name}** `×{qty}` - {item.value * qty:,}💰\n"

        embed.description = items_text

        # Stats
        embed.add_field(name="💰 Pièces", value=f"`{player.coins:,}`", inline=True)
        embed.add_field(name="📦 Valeur Inv.", value=f"`{total_value:,}`", inline=True)
        embed.add_field(name="🎯 Objets Uniques", value=f"`{len(items_list)}`", inline=True)
        embed.add_field(name="📊 Coffres Total", value=f"`{player.total_chests_opened}`", inline=True)
        embed.add_field(name="🏷️ Vendus", value=f"`{player.total_items_sold}`", inline=True)
        embed.add_field(name="📅 Coffres Aujourd'hui", value=f"`{player.daily_chests_opened}/50`", inline=True)

        embed.set_footer(text=f"Page {page}/{total_pages} • User ID: {joueur.id}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ══════════════════════════════════════════════════════════════
    # 💰 GÉRER LES PIÈCES
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="admin-coins", description="💰 [ADMIN] Modifier les pièces d'un joueur")
    @app_commands.describe(
        joueur="Joueur cible",
        action="Ajouter ou Retirer",
        montant="Montant de pièces"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="➕ Ajouter", value="add"),
        app_commands.Choice(name="➖ Retirer", value="remove"),
        app_commands.Choice(name="🔄 Définir", value="set")
    ])
    @is_admin()
    async def admin_coins(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member,
        action: str,
        montant: int
    ):
        """Modifie les pièces d'un joueur."""
        if montant < 0:
            await interaction.response.send_message(
                embed=discord.Embed(title="❌ Erreur", description="Le montant doit être positif.", color=0xe74c3c),
                ephemeral=True
            )
            return

        player = self.data.get_player(joueur.id)
        old_coins = player.coins

        if action == "add":
            player.coins += montant
            action_text = f"+{montant:,}"
            color = 0x2ecc71
        elif action == "remove":
            player.coins = max(0, player.coins - montant)
            action_text = f"-{montant:,}"
            color = 0xe74c3c
        else:  # set
            player.coins = montant
            action_text = f"→ {montant:,}"
            color = 0x3498db

        self.data.save_player(player)

        embed = discord.Embed(
            title="💰 Pièces Modifiées",
            color=color
        )
        embed.add_field(name="👤 Joueur", value=joueur.mention, inline=True)
        embed.add_field(name="📊 Action", value=f"`{action_text}`", inline=True)
        embed.add_field(name="👮 Admin", value=interaction.user.mention, inline=True)
        embed.add_field(
            name="💼 Solde",
            value=f"```diff\n- Avant: {old_coins:,}\n+ Après: {player.coins:,}\n```",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 🔄 RESET JOUEUR
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="admin-reset", description="🔄 [ADMIN] Réinitialiser un joueur")
    @app_commands.describe(joueur="Joueur à réinitialiser", confirmer="Confirmer la réinitialisation")
    @is_admin()
    async def admin_reset(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member,
        confirmer: bool = False
    ):
        """Réinitialise complètement un joueur."""
        if not confirmer:
            embed = discord.Embed(
                title="⚠️ Confirmation Requise",
                description=(
                    f"Tu es sur le point de **RÉINITIALISER** le profil de **{joueur.display_name}**.\n\n"
                    f"⚠️ Cela supprimera:\n"
                    f"• Toutes ses pièces\n"
                    f"• Tout son inventaire\n"
                    f"• Toutes ses statistiques\n\n"
                    f"Pour confirmer, utilise:\n"
                    f"`/admin-reset joueur:{joueur.display_name} confirmer:True`"
                ),
                color=0xf39c12
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        player = self.data.get_player(joueur.id)
        
        # Sauvegarder les anciennes stats pour le log
        old_coins = player.coins
        old_items = sum(player.inventory.values())
        old_chests = player.total_chests_opened

        # Reset
        player.coins = 0
        player.inventory = {}
        player.daily_chests_opened = 0
        player.total_chests_opened = 0
        player.total_items_sold = 0
        player.last_chest_date = ""

        self.data.save_player(player)

        embed = discord.Embed(
            title="🔄 Joueur Réinitialisé",
            color=0xe74c3c
        )
        embed.add_field(name="👤 Joueur", value=joueur.mention, inline=True)
        embed.add_field(name="👮 Admin", value=interaction.user.mention, inline=True)
        embed.add_field(
            name="📊 Anciennes Données Supprimées",
            value=(
                f"```yml\n"
                f"Pièces: {old_coins:,}\n"
                f"Objets: {old_items}\n"
                f"Coffres: {old_chests}\n"
                f"```"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 📊 STATISTIQUES GLOBALES
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="admin-stats", description="📊 [ADMIN] Statistiques globales du bot")
    @is_admin()
    async def admin_stats(self, interaction: discord.Interaction):
        """Affiche les statistiques globales."""
        all_items = self.data.get_all_items()
        all_players = self.data.get_leaderboard(1000)

        total_coins = sum(p.coins for p in all_players)
        total_items = sum(sum(p.inventory.values()) for p in all_players)
        total_chests = sum(p.total_chests_opened for p in all_players)
        total_sold = sum(p.total_items_sold for p in all_players)

        # Compter par rareté
        from models import Rarity
        rarity_counts = {r: 0 for r in Rarity}
        for item in all_items:
            rarity_counts[item.rarity] += 1

        embed = discord.Embed(
            title="📊 Statistiques Globales",
            color=0x9b59b6
        )

        embed.add_field(
            name="👥 Joueurs",
            value=f"```yml\nTotal: {len(all_players)}\n```",
            inline=True
        )

        embed.add_field(
            name="📦 Objets Disponibles",
            value=f"```yml\nTotal: {len(all_items)}\n```",
            inline=True
        )

        embed.add_field(
            name="💰 Économie",
            value=(
                f"```yml\n"
                f"Pièces en circulation: {total_coins:,}\n"
                f"Objets possédés: {total_items:,}\n"
                f"Objets vendus: {total_sold:,}\n"
                f"Coffres ouverts: {total_chests:,}\n"
                f"```"
            ),
            inline=False
        )

        rarity_text = ""
        for rarity in Rarity:
            rarity_text += f"{rarity.emoji} {rarity.display_name}: {rarity_counts[rarity]}\n"
        
        embed.add_field(
            name="🎨 Objets par Rareté",
            value=rarity_text,
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ══════════════════════════════════════════════════════════════
    # ❌ GESTION DES ERREURS
    # ══════════════════════════════════════════════════════════════

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Gère les erreurs des commandes admin."""
        if isinstance(error, app_commands.CheckFailure):
            embed = discord.Embed(
                title="🔒 Accès Refusé",
                description="Tu dois être **administrateur** pour utiliser cette commande.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Une erreur s'est produite:\n```{error}```",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function."""
    pass
