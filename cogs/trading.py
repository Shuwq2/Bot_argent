"""
Cog gérant les échanges et les cadeaux avec design ultra-moderne.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from datetime import datetime
import asyncio

from services import DataManager
from utils import GIFS, COLORS, EMOJIS
from utils.styles import Colors, Emojis, format_number, create_rarity_indicator


# ═══════════════════════════════════════════════════════════════════════════════
# 🔄 VIEWS MODERNES POUR LES ÉCHANGES
# ═══════════════════════════════════════════════════════════════════════════════

class ModernTradeView(discord.ui.View):
    """Interface moderne pour accepter/refuser un trade."""

    def __init__(self, cog, trade_id: int, receiver_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.trade_id = trade_id
        self.receiver_id = receiver_id

    @discord.ui.button(label="Accepter", emoji="✅", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.receiver_id:
            embed = discord.Embed(
                description=f"{Emojis.ERROR} **Seul le destinataire peut accepter !**",
                color=Colors.ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await self.cog.execute_trade(self.trade_id, True, interaction)

    @discord.ui.button(label="Refuser", emoji="❌", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.receiver_id:
            embed = discord.Embed(
                description=f"{Emojis.ERROR} **Seul le destinataire peut refuser !**",
                color=Colors.ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await self.cog.execute_trade(self.trade_id, False, interaction)


# ═══════════════════════════════════════════════════════════════════════════════
# 🔄 COG TRADING - SYSTÈME D'ÉCHANGE MODERNE
# ═══════════════════════════════════════════════════════════════════════════════

class Trading(commands.Cog):
    """Système d'échanges et cadeaux ultra-moderne."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager
        self.pending_trades = {}

    # ───────────────────────────────────────────────────────────────
    # 🔍 AUTOCOMPLETE FUNCTIONS
    # ───────────────────────────────────────────────────────────────

    async def own_item_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour les items du joueur."""
        player = self.data.get_player(interaction.user.id)
        choices = []
        
        for item_id, qty in player.inventory.items():
            item = self.data.get_item(item_id)
            if item:
                if current.lower() in item.name.lower() or not current:
                    display = f"{item.rarity.emoji} {item.name} (×{qty})"
                    choices.append(app_commands.Choice(name=display[:100], value=item.name))
        
        return choices[:25]

    # ───────────────────────────────────────────────────────────────
    # 🔄 COMMANDE TRADE MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="trade", description="🔄 Proposer un échange à un joueur")
    @app_commands.describe(
        joueur="Joueur avec qui échanger",
        ton_objet="Objet que tu donnes",
        quantite_donnee="Quantité que tu donnes",
        objet_demande="Objet que tu veux (optionnel)",
        quantite_demandee="Quantité demandée",
        pieces="Pièces à échanger (positif = tu donnes, négatif = tu demandes)"
    )
    @app_commands.autocomplete(ton_objet=own_item_autocomplete)
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
        """Propose un échange avec interface moderne."""
        
        # Vérifications de base
        if joueur.id == interaction.user.id:
            await interaction.response.send_message(
                embed=self._error_embed("Erreur", "Tu ne peux pas échanger avec toi-même !"),
                ephemeral=True
            )
            return

        if joueur.bot:
            await interaction.response.send_message(
                embed=self._error_embed("Erreur", "Tu ne peux pas échanger avec un bot !"),
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
                embed=self._error_embed("Objet Introuvable", f"Tu n'as pas **{ton_objet}** dans ton inventaire."),
                ephemeral=True
            )
            return

        if player.inventory.get(given_item.item_id, 0) < quantite_donnee:
            await interaction.response.send_message(
                embed=self._error_embed("Quantité Insuffisante", f"Tu n'as que ×{player.inventory.get(given_item.item_id, 0)} {given_item.name}."),
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
                    embed=self._error_embed("Objet Introuvable", f"**{joueur.display_name}** n'a pas **{objet_demande}**."),
                    ephemeral=True
                )
                return

            if target_player.inventory.get(requested_item.item_id, 0) < quantite_demandee:
                await interaction.response.send_message(
                    embed=self._error_embed("Quantité Insuffisante", f"**{joueur.display_name}** n'a pas assez de {requested_item.name}."),
                    ephemeral=True
                )
                return

        # Vérifier les pièces
        if pieces > 0 and player.coins < pieces:
            await interaction.response.send_message(
                embed=self._error_embed("Fonds Insuffisants", f"Tu n'as que {format_number(player.coins)} pièces."),
                ephemeral=True
            )
            return

        if pieces < 0 and target_player.coins < abs(pieces):
            await interaction.response.send_message(
                embed=self._error_embed("Fonds Insuffisants", f"**{joueur.display_name}** n'a pas assez de pièces."),
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

        # Créer l'embed moderne
        embed = discord.Embed(
            title=f"🔄 Proposition d'Échange",
            color=Colors.WARNING
        )

        embed.description = (
            f"```ansi\n"
            f"\u001b[1;33m╔{'═' * 36}╗\u001b[0m\n"
            f"\u001b[1;33m║\u001b[0m     🔄 ÉCHANGE EN ATTENTE 🔄        \u001b[1;33m║\u001b[0m\n"
            f"\u001b[1;33m╚{'═' * 36}╝\u001b[0m\n"
            f"```\n"
            f"**{interaction.user.display_name}** ↔️ **{joueur.display_name}**"
        )

        # Ce que donne l'initiateur
        give_text = f"{given_item.rarity.emoji} **{given_item.name}** `×{quantite_donnee}`"
        if pieces > 0:
            give_text += f"\n{Emojis.COIN} `{format_number(pieces)}` pièces"
        embed.add_field(
            name=f"📤 {interaction.user.display_name} donne",
            value=give_text,
            inline=True
        )

        # Ce que reçoit l'initiateur
        receive_text = ""
        if requested_item:
            receive_text = f"{requested_item.rarity.emoji} **{requested_item.name}** `×{quantite_demandee}`"
        if pieces < 0:
            if receive_text:
                receive_text += "\n"
            receive_text += f"{Emojis.COIN} `{format_number(abs(pieces))}` pièces"
        if not receive_text:
            receive_text = "*Rien (cadeau)*"
        embed.add_field(
            name=f"📥 {interaction.user.display_name} reçoit",
            value=receive_text,
            inline=True
        )

        embed.add_field(
            name="⏳ En attente de réponse",
            value=f"**{joueur.mention}**, utilise les boutons ci-dessous !",
            inline=False
        )

        embed.set_thumbnail(url=joueur.display_avatar.url)
        embed.set_footer(text="⏰ Cette offre expire dans 60 secondes")

        # Créer les boutons modernes
        view = ModernTradeView(self, trade_id, joueur.id)
        await interaction.response.send_message(embed=embed, view=view)

        # Timeout après 60 secondes
        await asyncio.sleep(60)
        if trade_id in self.pending_trades:
            del self.pending_trades[trade_id]
            try:
                timeout_embed = discord.Embed(
                    title=f"⏰ Échange Expiré",
                    description=(
                        f"```diff\n"
                        f"- L'offre n'a pas été acceptée à temps\n"
                        f"```"
                    ),
                    color=Colors.SECONDARY
                )
                await interaction.edit_original_response(embed=timeout_embed, view=None)
            except:
                pass

    async def execute_trade(self, trade_id: int, accepted: bool, interaction: discord.Interaction):
        """Exécute ou annule un trade avec feedback moderne."""
        if trade_id not in self.pending_trades:
            embed = self._error_embed("Erreur", "Cet échange n'existe plus.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        trade = self.pending_trades[trade_id]
        
        if interaction.user.id != trade["receiver"]:
            embed = self._error_embed("Erreur", "Seul le destinataire peut répondre.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        del self.pending_trades[trade_id]

        if not accepted:
            embed = discord.Embed(
                title=f"❌ Échange Refusé",
                description=(
                    f"```diff\n"
                    f"- {interaction.user.display_name} a refusé l'échange\n"
                    f"```"
                ),
                color=Colors.ERROR
            )
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

        # Message de succès moderne
        try:
            sender_user = await self.bot.fetch_user(trade["sender"])
            sender_name = sender_user.display_name
        except:
            sender_name = "Joueur"

        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} Échange Réussi !",
            color=Colors.SUCCESS
        )

        embed.description = (
            f"```ansi\n"
            f"\u001b[1;32m╔{'═' * 32}╗\u001b[0m\n"
            f"\u001b[1;32m║\u001b[0m     ✅ ÉCHANGE COMPLÉTÉ ✅       \u001b[1;32m║\u001b[0m\n"
            f"\u001b[1;32m╚{'═' * 32}╝\u001b[0m\n"
            f"```"
        )

        # Résumé
        summary = f"**{sender_name}** a donné:\n"
        summary += f"└─ {trade['given_item'].rarity.emoji} **{trade['given_item'].name}** `×{trade['given_qty']}`\n"
        if trade["coins"] > 0:
            summary += f"└─ {Emojis.COIN} `{format_number(trade['coins'])}`\n"

        summary += f"\n**{interaction.user.display_name}** a donné:\n"
        if trade["requested_item"]:
            summary += f"└─ {trade['requested_item'].rarity.emoji} **{trade['requested_item'].name}** `×{trade['requested_qty']}`\n"
        if trade["coins"] < 0:
            summary += f"└─ {Emojis.COIN} `{format_number(abs(trade['coins']))}`\n"
        if not trade["requested_item"] and trade["coins"] >= 0:
            summary += "└─ *Rien (cadeau reçu)*\n"

        embed.add_field(name="📋 Résumé", value=summary, inline=False)
        embed.set_footer(text="💡 Les objets ont été transférés avec succès")

        await interaction.response.edit_message(embed=embed, view=None)

    # ───────────────────────────────────────────────────────────────
    # 🎁 COMMANDE CADEAU MODERNE
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="cadeau", description="🎁 Offrir un objet gratuitement à un joueur")
    @app_commands.describe(
        joueur="Joueur à qui offrir",
        objet="Objet à offrir",
        quantite="Quantité à offrir"
    )
    @app_commands.autocomplete(objet=own_item_autocomplete)
    async def gift(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member, 
        objet: str, 
        quantite: Optional[int] = 1
    ):
        """Offre un objet avec animation moderne."""
        if joueur.id == interaction.user.id:
            await interaction.response.send_message(
                embed=self._error_embed("Erreur", "Tu ne peux pas t'offrir un cadeau !"),
                ephemeral=True
            )
            return

        if joueur.bot:
            await interaction.response.send_message(
                embed=self._error_embed("Erreur", "Tu ne peux pas offrir de cadeau à un bot !"),
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
                embed=self._error_embed("Introuvable", f"Tu n'as pas **{objet}** dans ton inventaire."),
                ephemeral=True
            )
            return

        if player.inventory.get(item.item_id, 0) < quantite:
            await interaction.response.send_message(
                embed=self._error_embed("Insuffisant", f"Tu n'as que ×{player.inventory.get(item.item_id, 0)} {item.name}."),
                ephemeral=True
            )
            return

        # Transférer
        player.remove_item(item.item_id, quantite)
        target.add_item(item.item_id, quantite)
        self.data.save_player(player)
        self.data.save_player(target)

        # Embed moderne
        rarity_indicator = create_rarity_indicator(item.rarity.name)
        
        embed = discord.Embed(
            title="🎁 Cadeau Envoyé !",
            color=Colors.SUCCESS
        )

        embed.description = (
            f"```ansi\n"
            f"\u001b[1;35m╔{'═' * 30}╗\u001b[0m\n"
            f"\u001b[1;35m║\u001b[0m      🎁 CADEAU OFFERT ! 🎁      \u001b[1;35m║\u001b[0m\n"
            f"\u001b[1;35m╚{'═' * 30}╝\u001b[0m\n"
            f"```\n"
            f"{rarity_indicator}\n\n"
            f"**{interaction.user.display_name}** ➜ **{joueur.display_name}**"
        )

        embed.add_field(
            name="📦 Objet Offert",
            value=(
                f"{item.rarity.emoji} **{item.name}** `×{quantite}`\n"
                f"└─ {Emojis.COIN} Valeur: `{format_number(item.value * quantite)}`"
            ),
            inline=False
        )

        embed.set_thumbnail(url=joueur.display_avatar.url)
        embed.set_footer(
            text=f"💝 Généreux ! • {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

    # ───────────────────────────────────────────────────────────────
    # 💸 COMMANDE DONNER PIÈCES
    # ───────────────────────────────────────────────────────────────

    @app_commands.command(name="donner", description="💸 Donne des pièces à un joueur")
    @app_commands.describe(
        joueur="Joueur à qui donner",
        montant="Montant à donner"
    )
    async def give_coins(
        self, 
        interaction: discord.Interaction, 
        joueur: discord.Member, 
        montant: int
    ):
        """Donne des pièces à un joueur."""
        if joueur.id == interaction.user.id:
            await interaction.response.send_message(
                embed=self._error_embed("Erreur", "Tu ne peux pas te donner des pièces !"),
                ephemeral=True
            )
            return

        if joueur.bot:
            await interaction.response.send_message(
                embed=self._error_embed("Erreur", "Tu ne peux pas donner de pièces à un bot !"),
                ephemeral=True
            )
            return

        if montant <= 0:
            await interaction.response.send_message(
                embed=self._error_embed("Montant Invalide", "Le montant doit être positif."),
                ephemeral=True
            )
            return

        player = self.data.get_player(interaction.user.id)
        target = self.data.get_player(joueur.id)

        if player.coins < montant:
            await interaction.response.send_message(
                embed=self._error_embed(
                    "Fonds Insuffisants",
                    f"Tu n'as que `{format_number(player.coins)}` pièces."
                ),
                ephemeral=True
            )
            return

        # Transférer
        player.coins -= montant
        target.coins += montant
        self.data.save_player(player)
        self.data.save_player(target)

        embed = discord.Embed(
            title=f"{Emojis.COIN} Transfert Réussi !",
            color=Colors.SUCCESS
        )

        embed.description = (
            f"```diff\n"
            f"+ {format_number(montant)} pièces transférées\n"
            f"```\n"
            f"**{interaction.user.display_name}** ➜ **{joueur.display_name}**"
        )

        embed.add_field(
            name="💼 Ton nouveau solde",
            value=f"`{format_number(player.coins)}` pièces",
            inline=True
        )

        embed.add_field(
            name=f"💼 Solde de {joueur.display_name}",
            value=f"`{format_number(target.coins)}` pièces",
            inline=True
        )

        embed.set_thumbnail(url=joueur.display_avatar.url)

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
