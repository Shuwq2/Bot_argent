"""
Cog gérant l'économie du bot : coffres, inventaire, vente d'objets.
Version améliorée avec animations et visuels.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from models import Chest, Rarity
from services import DataManager


class Economy(commands.Cog):
    """Cog pour le système d'économie et de collection."""

    # GIFs d'animation pour l'ouverture des coffres
    CHEST_OPENING_GIFS = {
        "opening": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHd4OHZwMnRiMHBhMnVxdWVqNjhqYnVhMnQwY3g5dDdqYzBrZ2FqZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xUOwGdA2o7E4TPJICQ/giphy.gif",
        Rarity.NORMAL: "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNnE4bWd2OWVwMW5xZWNzYmxmN2RyMTJzcHBxMmV5cHp2a3QzZWFkaiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/12FfNKPlSN8d1e/giphy.gif",
        Rarity.RARE: "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaG9mZWFuY3VpNnVxcjFndmR6dHF6cDFuNmNqYTBhY3Y5cWs4eWR6aSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/l0MYC0LajbaPoEADu/giphy.gif",
        Rarity.EPIC: "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHZ3cTd0cWFyeGx6NHdtbGV6cjBtdm5xZjZ2ZHl1OWVuaHlhcDVuYSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/3o7TKSjRrfIPjeiVyM/giphy.gif",
        Rarity.LEGENDARY: "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHRhbGFtdmZ0ZGRwY2Zja2xhNnVwaGdvaTFkbHhzNXl0aGlqeXdpcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/26BRzozg4TCBXv6QU/giphy.gif",
        Rarity.MYTHIC: "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN3VsY2FwcnE4ejVvYzVzNmlzMTBxZ2x4N2NqaGZ0dG56cHZlZnVjaSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/l4FGni1RBAR2OWsGk/giphy.gif"
    }

    # Images par catégorie d'objets
    CATEGORY_IMAGES = {
        "Armes": "https://i.imgur.com/6QZ7K5E.png",
        "Armures": "https://i.imgur.com/8HJ0YR1.png", 
        "Gemmes": "https://i.imgur.com/xQzKnNa.png",
        "Accessoires": "https://i.imgur.com/W3Z5xXw.png",
        "Potions": "https://i.imgur.com/YK7j3Gg.png",
        "Parchemins": "https://i.imgur.com/5wH7Lam.png",
        "Créatures": "https://i.imgur.com/NJ9bKzP.png",
        "Livres": "https://i.imgur.com/qKjGk8s.png",
        "Nourriture": "https://i.imgur.com/RZnV8Hx.png"
    }

    # Images par rareté
    RARITY_IMAGES = {
        Rarity.NORMAL: "https://i.imgur.com/vJSKJHh.png",
        Rarity.RARE: "https://i.imgur.com/Px0bVCq.png",
        Rarity.EPIC: "https://i.imgur.com/kV5G1HQ.png",
        Rarity.LEGENDARY: "https://i.imgur.com/MdJ3yZB.png",
        Rarity.MYTHIC: "https://i.imgur.com/1kR8nN9.png"
    }

    # Couleurs Discord par rareté
    RARITY_COLORS = {
        Rarity.NORMAL: 0x9e9e9e,      # Gris
        Rarity.RARE: 0x2196F3,        # Bleu
        Rarity.EPIC: 0x9C27B0,        # Violet
        Rarity.LEGENDARY: 0xFFD700,   # Or
        Rarity.MYTHIC: 0xFF1744       # Rouge flamboyant
    }

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager
        self.chest = Chest(self.data.get_all_items())

    # ==================== COMMANDE COFFRE ====================

    @app_commands.command(name="coffre", description="🎁 Ouvre un coffre mystérieux pour obtenir un objet !")
    @app_commands.describe(payer="💎 Payer 3500 pièces pour un coffre supplémentaire")
    async def open_chest(self, interaction: discord.Interaction, payer: Optional[bool] = False):
        """Ouvre un coffre avec animation et donne un objet aléatoire."""
        player = self.data.get_player(interaction.user.id)
        
        # Vérifier si le joueur peut ouvrir un coffre
        if not player.can_open_free_chest() and not payer:
            embed = discord.Embed(
                title="🚫 Limite Journalière Atteinte !",
                description=(
                    f"```fix\n"
                    f"Tu as ouvert {player.MAX_DAILY_CHESTS}/{player.MAX_DAILY_CHESTS} coffres aujourd'hui\n"
                    f"```\n"
                    f"╔══════════════════════════════════╗\n"
                    f"║  💰 Solde: **{player.coins:,}** pièces\n"
                    f"║  💎 Coût coffre: **{player.CHEST_COST:,}** pièces\n"
                    f"╚══════════════════════════════════╝\n\n"
                    f"🔮 Utilise `/coffre payer:True` pour acheter\n"
                    f"⏰ Ou reviens demain pour tes coffres gratuits !"
                ),
                color=0xFF6B6B
            )
            embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHd4OHZwMnRiMHBhMnVxdWVqNjhqYnVhMnQwY3g5dDdqYzBrZ2FqZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xUOwGdA2o7E4TPJICQ/giphy.gif")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if payer and not player.can_open_free_chest():
            if not player.can_afford_chest():
                embed = discord.Embed(
                    title="💸 Fonds Insuffisants !",
                    description=(
                        f"```diff\n"
                        f"- Coffre requis: {player.CHEST_COST:,} 💰\n"
                        f"- Ton solde: {player.coins:,} 💰\n"
                        f"- Manque: {player.CHEST_COST - player.coins:,} 💰\n"
                        f"```\n"
                        f"💡 **Astuce:** Vends tes objets avec `/vendre` !"
                    ),
                    color=0xFF6B6B
                )
                embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3k5cHh4czBvNnVmYjJ4YWRobTVqZXBrMGdvcG5leXl4cXo0aXMzbiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/hpXxJ78YtpT0s/giphy.gif")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # ═══════════ ANIMATION D'OUVERTURE ═══════════
        
        # Phase 1: Coffre qui apparaît
        opening_embed = discord.Embed(
            title="✨ Ouverture du Coffre Mystérieux... ✨",
            description=(
                "```\n"
                "╔═══════════════════════════════════╗\n"
                "║     🎁 COFFRE EN COURS...         ║\n"
                "║                                   ║\n"
                "║        ████████████               ║\n"
                "║       █▓▓▓▓▓▓▓▓▓▓▓▓█             ║\n"
                "║      █▓▓▓▓▓▓▓▓▓▓▓▓▓▓█            ║\n"
                "║      ██████████████████           ║\n"
                "╚═══════════════════════════════════╝\n"
                "```"
            ),
            color=0xFFD700
        )
        opening_embed.set_image(url=self.CHEST_OPENING_GIFS["opening"])
        await interaction.response.send_message(embed=opening_embed)

        # Attendre pour l'animation
        await asyncio.sleep(2.5)

        # Ouvrir le coffre (logique)
        success = player.open_chest(paid=payer and not player.can_open_free_chest())
        if not success:
            error_embed = discord.Embed(
                title="❌ Erreur",
                description="Une erreur est survenue lors de l'ouverture.",
                color=0xFF0000
            )
            await interaction.edit_original_response(embed=error_embed)
            return

        # Tirer un objet
        item = self.chest.open()
        if not item:
            error_embed = discord.Embed(
                title="❌ Erreur",
                description="Aucun objet disponible.",
                color=0xFF0000
            )
            await interaction.edit_original_response(embed=error_embed)
            return

        # Ajouter l'objet à l'inventaire
        player.add_item(item.item_id)
        self.data.save_player(player)

        # Phase 2: Révélation avec animation selon rareté
        rarity_gif = self.CHEST_OPENING_GIFS.get(item.rarity, self.CHEST_OPENING_GIFS[Rarity.NORMAL])
        
        reveal_embed = discord.Embed(
            title=self._get_reveal_title(item.rarity),
            color=self.RARITY_COLORS.get(item.rarity, 0x9e9e9e)
        )
        reveal_embed.set_image(url=rarity_gif)
        await interaction.edit_original_response(embed=reveal_embed)
        
        await asyncio.sleep(1.5)

        # Phase 3: Affichage final de l'objet
        final_embed = self._create_reward_embed(item, player)
        await interaction.edit_original_response(embed=final_embed)

    def _get_reveal_title(self, rarity: Rarity) -> str:
        """Retourne un titre de révélation selon la rareté."""
        titles = {
            Rarity.NORMAL: "📦 Un objet apparaît...",
            Rarity.RARE: "💎 Quelque chose de rare brille...",
            Rarity.EPIC: "🌟 Une aura épique émane du coffre !",
            Rarity.LEGENDARY: "⚡ LÉGENDAIRE ! Le coffre explose de lumière !",
            Rarity.MYTHIC: "🔥 MYTHIQUE !! UN TRÉSOR INCROYABLE !!!"
        }
        return titles.get(rarity, "📦 Un objet apparaît...")

    def _create_reward_embed(self, item, player) -> discord.Embed:
        """Crée l'embed stylisé d'affichage de la récompense."""
        color = self.RARITY_COLORS.get(item.rarity, 0x9e9e9e)
        
        # Créer le cadre décoratif selon la rareté
        if item.rarity == Rarity.MYTHIC:
            title = f"🔥 MYTHIQUE ! 🔥 {item.name} 🔥 MYTHIQUE ! 🔥"
        elif item.rarity == Rarity.LEGENDARY:
            title = f"⭐ LÉGENDAIRE ⭐ {item.name}"
        elif item.rarity == Rarity.EPIC:
            title = f"💜 EPIC 💜 {item.name}"
        elif item.rarity == Rarity.RARE:
            title = f"💙 RARE 💙 {item.name}"
        else:
            title = f"📦 {item.name}"

        embed = discord.Embed(
            title=title,
            color=color
        )

        # Zone d'information principale
        info_box = (
            f"```ansi\n"
            f"\u001b[1;37m╔══════════════════════════════════╗\u001b[0m\n"
            f"\u001b[1;37m║\u001b[0m  {item.rarity.emoji} Rareté: \u001b[1;33m{item.rarity.display_name}\u001b[0m\n"
            f"\u001b[1;37m║\u001b[0m  💰 Valeur: \u001b[1;32m{item.value:,} pièces\u001b[0m\n"
            f"\u001b[1;37m║\u001b[0m  📁 Catégorie: \u001b[1;36m{item.category}\u001b[0m\n"
            f"\u001b[1;37m╚══════════════════════════════════╝\u001b[0m\n"
            f"```"
        )
        
        embed.add_field(
            name="📋 Informations",
            value=info_box,
            inline=False
        )

        embed.add_field(
            name="📖 Description",
            value=f"*« {item.description} »*",
            inline=False
        )

        # Statistiques du joueur
        stats_box = (
            f"```\n"
            f"🎁 Coffres restants: {player.get_remaining_free_chests()}/{player.MAX_DAILY_CHESTS}\n"
            f"💰 Solde actuel: {player.coins:,} pièces\n"
            f"📦 Total ouverts: {player.total_chests_opened}\n"
            f"```"
        )
        embed.add_field(
            name="📊 Tes Statistiques",
            value=stats_box,
            inline=False
        )

        # Ajouter une image selon la catégorie
        thumbnail = self.CATEGORY_IMAGES.get(item.category, self.RARITY_IMAGES.get(item.rarity))
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        embed.set_footer(text=f"🎮 Utilise /inventaire pour voir ta collection !")
        
        return embed

    # ==================== COMMANDE INVENTAIRE ====================

    @app_commands.command(name="inventaire", description="📦 Affiche ta collection d'objets")
    @app_commands.describe(page="Page de l'inventaire (10 objets par page)")
    async def inventory(self, interaction: discord.Interaction, page: Optional[int] = 1):
        """Affiche l'inventaire stylisé du joueur."""
        player = self.data.get_player(interaction.user.id)
        
        if not player.inventory:
            embed = discord.Embed(
                title="📦 Inventaire Vide",
                description=(
                    "```\n"
                    "╔═══════════════════════════════════╗\n"
                    "║                                   ║\n"
                    "║     🕳️  Aucun objet trouvé...     ║\n"
                    "║                                   ║\n"
                    "╚═══════════════════════════════════╝\n"
                    "```\n"
                    "💡 **Astuce:** Utilise `/coffre` pour obtenir des objets !"
                ),
                color=0x9e9e9e
            )
            embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3k5cHh4czBvNnVmYjJ4YWRobTVqZXBrMGdvcG5leXl4cXo0aXMzbiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/hpXxJ78YtpT0s/giphy.gif")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Préparer les objets avec leurs détails
        items_list = []
        total_value = 0
        rarity_counts = {r: 0 for r in Rarity}
        
        for item_id, quantity in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                items_list.append((item, quantity))
                total_value += item.value * quantity
                rarity_counts[item.rarity] += quantity

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
            title=f"🎒 Inventaire de {interaction.user.display_name}",
            color=0x3498db
        )

        # Construire la liste des objets de façon stylisée
        items_text = ""
        for item, quantity in page_items:
            value_total = item.value * quantity
            items_text += f"{item.rarity.emoji} **{item.name}** ×{quantity}\n"
            items_text += f"┗━ 💰 {value_total:,} pièces\n"

        embed.add_field(
            name=f"📦 Objets (Page {page}/{total_pages})",
            value=items_text or "Aucun objet",
            inline=False
        )

        # Statistiques de collection
        rarity_stats = ""
        for rarity in Rarity:
            if rarity_counts[rarity] > 0:
                rarity_stats += f"{rarity.emoji} {rarity.display_name}: **{rarity_counts[rarity]}**\n"

        if rarity_stats:
            embed.add_field(
                name="📊 Collection par Rareté",
                value=rarity_stats,
                inline=True
            )

        # Résumé économique
        summary = (
            f"📦 **Objets uniques:** {len(player.inventory)}\n"
            f"💎 **Valeur totale:** {total_value:,} 💰\n"
            f"💰 **Solde:** {player.coins:,} 💰"
        )
        embed.add_field(
            name="💼 Résumé",
            value=summary,
            inline=True
        )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"📖 Page {page}/{total_pages} • /inventaire page:{page+1 if page < total_pages else 1}")

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE VENDRE ====================

    @app_commands.command(name="vendre", description="💸 Vend un objet de ton inventaire")
    @app_commands.describe(
        objet="Nom de l'objet à vendre",
        quantite="Nombre d'objets à vendre (défaut: 1)"
    )
    async def sell(self, interaction: discord.Interaction, objet: str, quantite: Optional[int] = 1):
        """Vend un objet de l'inventaire avec animation."""
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
                title="❌ Objet Introuvable",
                description=(
                    f"```diff\n"
                    f"- Objet \"{objet}\" non trouvé dans ton inventaire\n"
                    f"```\n"
                    f"💡 Utilise `/inventaire` pour voir tes objets."
                ),
                color=0xFF6B6B
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Vérifier la quantité
        available = player.inventory.get(item.item_id, 0)
        if quantite <= 0 or quantite > available:
            embed = discord.Embed(
                title="❌ Quantité Invalide",
                description=(
                    f"```diff\n"
                    f"- Demandé: {quantite}x {item.name}\n"
                    f"+ Disponible: {available}x {item.name}\n"
                    f"```"
                ),
                color=0xFF6B6B
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Effectuer la vente
        total_coins = item.value * quantite
        old_balance = player.coins
        player.sell_item(item.item_id, item.value, quantite)
        self.data.save_player(player)

        # Créer l'embed de confirmation stylisé
        embed = discord.Embed(
            title="💰 Vente Réussie !",
            color=0x2ECC71
        )

        transaction_box = (
            f"```diff\n"
            f"+ TRANSACTION COMPLÈTE\n"
            f"```\n"
            f"**{item.rarity.emoji} {item.name}** ×{quantite}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 Prix unitaire: **{item.value:,}** 💰\n"
            f"📦 Quantité vendue: **{quantite}**\n"
            f"💎 **Total reçu: +{total_coins:,}** 💰"
        )
        embed.add_field(name="📋 Détails", value=transaction_box, inline=False)

        balance_box = (
            f"```\n"
            f"Avant: {old_balance:,} 💰\n"
            f"Après: {player.coins:,} 💰 (+{total_coins:,})\n"
            f"```"
        )
        embed.add_field(name="💼 Nouveau Solde", value=balance_box, inline=False)

        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcWtxNGN0MjRxYTd4cmZnNjFmMGtvdDQxdjBiZTk1cjdmYzN3d2N6eiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/l0HlNQ03J5JxX6lva/giphy.gif")
        embed.set_footer(text="💡 Continue à vendre pour acheter plus de coffres !")

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE VENDRE TOUT ====================

    @app_commands.command(name="vendretout", description="💸 Vend tous les objets d'une rareté")
    @app_commands.describe(rarete="Rareté des objets à vendre")
    @app_commands.choices(rarete=[
        app_commands.Choice(name="⬜ Normal", value="NORMAL"),
        app_commands.Choice(name="🟦 Rare", value="RARE"),
        app_commands.Choice(name="🟪 Epic", value="EPIC"),
        app_commands.Choice(name="🟨 Légendaire", value="LEGENDARY"),
        app_commands.Choice(name="🟥 Mythique", value="MYTHIC")
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
                title="📦 Aucun Objet à Vendre",
                description=f"Tu n'as aucun objet {target_rarity.emoji} **{target_rarity.display_name}**.",
                color=0xFF6B6B
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
            title="🎉 Vente Massive Réussie !",
            color=self.RARITY_COLORS.get(target_rarity, 0x2ECC71)
        )

        summary_box = (
            f"```diff\n"
            f"+ VENTE EN GROS COMPLÉTÉE\n"
            f"```\n"
            f"{target_rarity.emoji} **{total_items}** objets {target_rarity.display_name} vendus\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 **Total reçu: +{total_coins:,}** 💰"
        )
        embed.add_field(name="📋 Résumé", value=summary_box, inline=False)

        balance_box = (
            f"```\n"
            f"Avant: {old_balance:,} 💰\n"
            f"Après: {player.coins:,} 💰 (+{total_coins:,})\n"
            f"```"
        )
        embed.add_field(name="💼 Nouveau Solde", value=balance_box, inline=False)

        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcWtxNGN0MjRxYTd4cmZnNjFmMGtvdDQxdjBiZTk1cjdmYzN3d2N6eiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/l0HlNQ03J5JxX6lva/giphy.gif")

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE PROFIL ====================

    @app_commands.command(name="profil", description="👤 Affiche ton profil et tes statistiques")
    @app_commands.describe(membre="Membre dont afficher le profil")
    async def profile(self, interaction: discord.Interaction, membre: Optional[discord.Member] = None):
        """Affiche le profil stylisé d'un joueur."""
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

        # Déterminer le rang du joueur
        rank_emoji, rank_name = self._get_player_rank(player.coins + inventory_value)

        embed = discord.Embed(
            title=f"{rank_emoji} Profil de {target.display_name}",
            color=0x3498db
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        # Bannière de rang
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;33m╔══════════════════════════════════╗\u001b[0m\n"
            f"\u001b[1;33m║\u001b[0m      🏆 Rang: \u001b[1;36m{rank_name}\u001b[0m\n"
            f"\u001b[1;33m╚══════════════════════════════════╝\u001b[0m\n"
            f"```"
        )

        # Économie
        economy_box = (
            f"💰 **Solde:** {player.coins:,} pièces\n"
            f"📦 **Valeur inventaire:** {inventory_value:,} pièces\n"
            f"💎 **Richesse totale:** {player.coins + inventory_value:,} pièces"
        )
        embed.add_field(name="💼 Économie", value=economy_box, inline=True)

        # Collection
        collection_box = (
            f"📦 **Objets totaux:** {total_items}\n"
            f"🎯 **Objets uniques:** {unique_items}\n"
            f"🏷️ **Objets vendus:** {player.total_items_sold}"
        )
        embed.add_field(name="🎒 Collection", value=collection_box, inline=True)

        # Coffres
        chests_box = (
            f"🎁 **Aujourd'hui:** {player.daily_chests_opened}/{player.MAX_DAILY_CHESTS}\n"
            f"📊 **Total ouverts:** {player.total_chests_opened}"
        )
        embed.add_field(name="📦 Coffres", value=chests_box, inline=True)

        # Répartition par rareté
        rarity_text = ""
        for rarity in Rarity:
            count = rarity_counts[rarity]
            bar_length = min(10, count // 5) if count > 0 else 0
            bar = "█" * bar_length + "░" * (10 - bar_length)
            rarity_text += f"{rarity.emoji} `{bar}` {count}\n"
        
        embed.add_field(name="📊 Répartition", value=rarity_text, inline=False)

        embed.set_footer(text="🎮 Ouvre des coffres pour améliorer ta collection !")

        await interaction.response.send_message(embed=embed)

    def _get_player_rank(self, total_wealth: int) -> tuple:
        """Détermine le rang du joueur selon sa richesse totale."""
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
            if total_wealth >= threshold:
                return emoji, name
        return "🌱", "Débutant"

    # ==================== COMMANDE CLASSEMENT ====================

    @app_commands.command(name="classement", description="🏆 Affiche le classement des joueurs")
    @app_commands.describe(type="Type de classement")
    @app_commands.choices(type=[
        app_commands.Choice(name="💰 Richesse (pièces)", value="coins"),
        app_commands.Choice(name="📦 Collection (objets uniques)", value="collection")
    ])
    async def leaderboard(self, interaction: discord.Interaction, type: Optional[str] = "coins"):
        """Affiche le classement stylisé des joueurs."""
        if type == "collection":
            players = self.data.get_collection_leaderboard(10)
            title = "🏆 Top Collectionneurs"
        else:
            players = self.data.get_leaderboard(10)
            title = "🏆 Top Richesse"

        embed = discord.Embed(
            title=title,
            color=0xFFD700
        )

        if not players:
            embed.description = "```\nAucun joueur n'a encore joué !\n```"
            await interaction.response.send_message(embed=embed)
            return

        leaderboard_text = "```\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for i, player in enumerate(players):
            try:
                user = await self.bot.fetch_user(player.user_id)
                username = user.display_name[:15]
            except:
                username = f"Joueur #{player.user_id}"[:15]

            medal = medals[i] if i < len(medals) else f"#{i+1}"
            
            if type == "collection":
                value = len(player.inventory)
                leaderboard_text += f"{medal} {username:<15} │ {value:>5} objets\n"
            else:
                leaderboard_text += f"{medal} {username:<15} │ {player.coins:>8,} 💰\n"

        leaderboard_text += "```"
        embed.description = leaderboard_text

        embed.set_footer(text="🎮 Joue pour monter dans le classement !")
        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHRhbGFtdmZ0ZGRwY2Zja2xhNnVwaGdvaTFkbHhzNXl0aGlqeXdpcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/26BRzozg4TCBXv6QU/giphy.gif")

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE TAUX ====================

    @app_commands.command(name="taux", description="📊 Affiche les taux de drop des coffres")
    async def drop_rates(self, interaction: discord.Interaction):
        """Affiche les taux de drop stylisés."""
        embed = discord.Embed(
            title="🎰 Taux de Drop des Coffres",
            description=(
                "```\n"
                "╔═══════════════════════════════════╗\n"
                "║   PROBABILITÉS D'OBTENTION        ║\n"
                "╚═══════════════════════════════════╝\n"
                "```"
            ),
            color=0x9B59B6
        )

        for rarity in Rarity:
            percentage = rarity.drop_rate * 100
            bar_filled = int(percentage / 5)
            bar = "▓" * bar_filled + "░" * (20 - bar_filled)
            
            embed.add_field(
                name=f"{rarity.emoji} {rarity.display_name}",
                value=(
                    f"```\n"
                    f"[{bar}] {percentage:.1f}%\n"
                    f"Valeur: {rarity.base_value:,}+ 💰\n"
                    f"```"
                ),
                inline=False
            )

        embed.add_field(
            name="💡 Info",
            value=(
                f"```\n"
                f"🎁 Coffres gratuits/jour: 50\n"
                f"💎 Coût coffre bonus: 3,500 💰\n"
                f"```"
            ),
            inline=False
        )

        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcHd4OHZwMnRiMHBhMnVxdWVqNjhqYnVhMnQwY3g5dDdqYzBrZ2FqZyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/xUOwGdA2o7E4TPJICQ/giphy.gif")
        embed.set_footer(text="🍀 Bonne chance dans tes tirages !")

        await interaction.response.send_message(embed=embed)

    # ==================== COMMANDE BOUTIQUE ====================

    @app_commands.command(name="boutique", description="🏪 Affiche la boutique")
    async def shop(self, interaction: discord.Interaction):
        """Affiche la boutique."""
        player = self.data.get_player(interaction.user.id)
        
        embed = discord.Embed(
            title="🏪 Boutique",
            description=(
                "```\n"
                "╔═══════════════════════════════════╗\n"
                "║      BIENVENUE À LA BOUTIQUE      ║\n"
                "╚═══════════════════════════════════╝\n"
                "```"
            ),
            color=0xE91E63
        )

        embed.add_field(
            name="🎁 Coffre Bonus",
            value=(
                f"```\n"
                f"Prix: 3,500 💰\n"
                f"Commande: /coffre payer:True\n"
                f"```\n"
                f"Ouvre un coffre supplémentaire !"
            ),
            inline=True
        )

        embed.add_field(
            name="💰 Ton Solde",
            value=f"```\n{player.coins:,} pièces\n```",
            inline=True
        )

        embed.add_field(
            name="💡 Comment gagner des pièces ?",
            value=(
                "• `/coffre` - Ouvre des coffres gratuits\n"
                "• `/vendre` - Vends tes objets\n"
                "• `/vendretout` - Vends en masse"
            ),
            inline=False
        )

        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcWtxNGN0MjRxYTd4cmZnNjFmMGtvdDQxdjBiZTk1cjdmYzN3d2N6eiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/l0HlNQ03J5JxX6lva/giphy.gif")

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
                        name=f"{item.rarity.emoji} {item.name} (×{quantity}) - {item.value:,} 💰",
                        value=item.name
                    )
                )

        return choices[:25]


async def setup(bot: commands.Bot):
    """Setup function pour charger le cog."""
    pass
