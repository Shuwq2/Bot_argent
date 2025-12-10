"""
Cog gérant l'équipement et les sets.
Design ultra-moderne avec vues interactives.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Optional

from services import DataManager
from utils import ModernTheme, ModernEmbed, create_progress_bar


# ══════════════════════════════════════════════════════════════════════════════
# 🎨 CONSTANTES DE DESIGN
# ══════════════════════════════════════════════════════════════════════════════

SLOT_DISPLAY = {
    "HELMET": {"emoji": "🪖", "name": "Casque", "icon": "⬡"},
    "CHESTPLATE": {"emoji": "🛡️", "name": "Plastron", "icon": "◈"},
    "LEGGINGS": {"emoji": "👖", "name": "Jambières", "icon": "◇"},
    "BOOTS": {"emoji": "👢", "name": "Bottes", "icon": "◆"},
    "WEAPON": {"emoji": "⚔️", "name": "Arme", "icon": "⚜"},
    "ACCESSORY": {"emoji": "💍", "name": "Accessoire", "icon": "✦"}
}

RARITY_COLORS = {
    "common": 0x95a5a6,
    "uncommon": 0x2ecc71,
    "rare": 0x3498db,
    "epic": 0x9b59b6,
    "legendary": 0xf39c12
}


class SetPageView(discord.ui.View):
    """Vue avec pagination pour les sets."""
    
    def __init__(self, sets_data: list, data_manager, user_id: int):
        super().__init__(timeout=120)
        self.sets = sets_data
        self.data = data_manager
        self.user_id = user_id
        self.current_page = 0
        self.sets_per_page = 2
        self.total_pages = max(1, (len(sets_data) + self.sets_per_page - 1) // self.sets_per_page)
        self._update_buttons()
    
    def _update_buttons(self):
        self.previous_btn.disabled = self.current_page <= 0
        self.next_btn.disabled = self.current_page >= self.total_pages - 1
    
    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="",
            color=ModernTheme.LEGENDARY
        )
        
        # Header moderne
        header = "```ansi\n"
        header += "\u001b[1;33m╔══════════════════════════════════════╗\u001b[0m\n"
        header += "\u001b[1;33m║\u001b[0m     \u001b[1;36m📦 SETS D'ÉQUIPEMENT\u001b[0m           \u001b[1;33m║\u001b[0m\n"
        header += "\u001b[1;33m╚══════════════════════════════════════╝\u001b[0m\n"
        header += "```"
        
        embed.description = header + "\n*Collecte les pièces d'un set pour débloquer des bonus puissants !*\n"
        
        # Afficher les sets de la page courante
        start_idx = self.current_page * self.sets_per_page
        end_idx = min(start_idx + self.sets_per_page, len(self.sets))
        
        player = self.data.get_player(self.user_id)
        equipped_pieces = self.data.get_equipped_set_pieces(player)
        
        for eq_set in self.sets[start_idx:end_idx]:
            owned_count = equipped_pieces.get(eq_set.set_id, 0)
            progress = create_progress_bar(owned_count, 4, 8)
            
            set_text = f"*{eq_set.description}*\n\n"
            set_text += f"**Progression:** {progress} `{owned_count}/4`\n\n"
            
            # Bonus 2 pièces
            bonus_2_status = "✅" if owned_count >= 2 else "⬜"
            set_text += f"{bonus_2_status} **2 Pièces:** {eq_set.bonus_2.get('description', 'Bonus')}\n"
            
            # Bonus 4 pièces
            bonus_4_status = "✅" if owned_count >= 4 else "⬜"
            set_text += f"{bonus_4_status} **4 Pièces:** {eq_set.bonus_4.get('description', 'Bonus complet')}\n\n"
            
            # Pièces du set
            pieces_display = []
            for piece_id in eq_set.pieces:
                item = self.data.get_item(piece_id)
                if item:
                    # Vérifier si équipé
                    is_equipped = any(player.equipment.get(slot) == piece_id for slot in player.equipment)
                    status = "🔹" if is_equipped else "▫️"
                    pieces_display.append(f"{status} {item.rarity.emoji} {item.name}")
            
            set_text += "**Pièces:**\n" + "\n".join(pieces_display)
            
            embed.add_field(
                name=f"✨ {eq_set.name}",
                value=set_text,
                inline=False
            )
        
        embed.set_footer(text=f"📄 Page {self.current_page + 1}/{self.total_pages} • Équipe 4 pièces pour le bonus maximum !")
        
        return embed
    
    @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.secondary)
    async def previous_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce n'est pas ta commande !", ephemeral=True)
        
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce n'est pas ta commande !", ephemeral=True)
        
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)


class EquipmentSlotSelect(discord.ui.Select):
    """Menu déroulant pour sélectionner un slot à déséquiper."""
    
    def __init__(self, player, data_manager):
        self.player = player
        self.data = data_manager
        
        options = []
        for slot, item_id in player.equipment.items():
            if item_id:
                item = data_manager.get_item(item_id)
                slot_info = SLOT_DISPLAY.get(slot, {"emoji": "📦", "name": slot})
                
                label = f"{slot_info['name']}: {item.name if item else 'Inconnu'}"
                options.append(discord.SelectOption(
                    label=label[:100],
                    value=slot,
                    emoji=slot_info['emoji'],
                    description=f"Retirer cet équipement"
                ))
        
        if not options:
            options = [discord.SelectOption(label="Aucun équipement", value="none")]
        
        super().__init__(
            placeholder="🛡️ Sélectionne un slot à vider...",
            options=options,
            min_values=1,
            max_values=1
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("❌ Tu n'as rien d'équipé !", ephemeral=True)
            return
        
        slot = self.values[0]
        old_item_id = self.player.unequip_item(slot)
        
        if old_item_id:
            self.data.save_player(self.player)
            old_item = self.data.get_item(old_item_id)
            slot_info = SLOT_DISPLAY.get(slot, {"name": slot})
            
            embed = discord.Embed(
                title="",
                color=ModernTheme.WARNING
            )
            
            header = "```ansi\n"
            header += "\u001b[1;33m✓ ÉQUIPEMENT RETIRÉ\u001b[0m\n"
            header += "```"
            
            embed.description = header + f"\n\n**{slot_info['name']}** vidé !\n\n"
            embed.description += f"📤 {old_item.rarity.emoji if old_item else '❓'} **{old_item.name if old_item else old_item_id}** retourné dans l'inventaire"
            
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await interaction.response.send_message("❌ Ce slot est déjà vide !", ephemeral=True)


class UnequipView(discord.ui.View):
    """Vue interactive pour déséquiper."""
    
    def __init__(self, player, data_manager, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.add_item(EquipmentSlotSelect(player, data_manager))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ce n'est pas ta commande !", ephemeral=True)
            return False
        return True


class Equipment(commands.Cog):
    """Cog pour l'équipement et les sets - Design Ultra-Moderne."""

    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager

    # ══════════════════════════════════════════════════════════════
    # 🛡️ COMMANDE EQUIPEMENT
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="equipement", description="🛡️ Affiche ton équipement et tes bonus de set")
    async def show_equipment(self, interaction: discord.Interaction):
        """Affiche l'équipement actuel du joueur avec design moderne."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        embed = discord.Embed(title="", color=ModernTheme.PRIMARY)
        
        # Header avec design ANSI
        header = "```ansi\n"
        header += "\u001b[1;34m╔══════════════════════════════════════╗\u001b[0m\n"
        header += "\u001b[1;34m║\u001b[0m      \u001b[1;36m🛡️ TON ÉQUIPEMENT\u001b[0m            \u001b[1;34m║\u001b[0m\n"
        header += "\u001b[1;34m╚══════════════════════════════════════╝\u001b[0m\n"
        header += "```"
        
        embed.description = header
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Affichage des slots avec design moderne
        equipment_lines = []
        slots_order = ["HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS", "WEAPON", "ACCESSORY"]
        
        for slot in slots_order:
            slot_info = SLOT_DISPLAY[slot]
            item_id = player.equipment.get(slot)
            
            if item_id:
                item = self.data.get_item(item_id)
                if item:
                    set_tag = ""
                    if item.set_id:
                        eq_set = self.data.get_set(item.set_id)
                        if eq_set:
                            set_tag = f" `[{eq_set.name}]`"
                    
                    equipment_lines.append(
                        f"{slot_info['icon']} **{slot_info['name']}**\n"
                        f"   └─ {item.rarity.emoji} {item.name}{set_tag}"
                    )
                else:
                    equipment_lines.append(
                        f"{slot_info['icon']} **{slot_info['name']}**\n"
                        f"   └─ ❓ *Item inconnu*"
                    )
            else:
                equipment_lines.append(
                    f"{slot_info['icon']} **{slot_info['name']}**\n"
                    f"   └─ ▫️ *Vide*"
                )
        
        embed.add_field(
            name="📋 Slots d'Équipement",
            value="\n".join(equipment_lines),
            inline=False
        )
        
        # Bonus de sets actifs
        set_bonuses = self.data.get_set_bonuses(player)
        if set_bonuses:
            bonus_lines = []
            for set_id, info in set_bonuses.items():
                progress = create_progress_bar(info['pieces'], 4, 6)
                bonus_lines.append(
                    f"✨ **{info['set_name']}** {progress} `{info['pieces']}/4`\n"
                    f"   └─ {info['bonus'].get('description', 'Bonus actif')}"
                )
            embed.add_field(
                name="🏆 Bonus de Set Actifs",
                value="\n\n".join(bonus_lines),
                inline=False
            )
        
        # Bonus totaux avec barres visuelles
        total_drop = self.data.calculate_total_drop_bonus(player)
        total_coin = self.data.calculate_total_coin_bonus(player)
        
        # Mettre à jour les stats d'équipement
        player.update_equipment_stats(self.data)
        
        # Stats de combat améliorées
        stats_text = "```\n"
        stats_text += f"❤️ PV     +{player.get_max_hp() - player.base_hp:>3}  ({player.get_max_hp()} total)\n"
        stats_text += f"⚔️ ATK    +{player.get_attack() - player.base_attack:>3}  ({player.get_attack()} total)\n"
        stats_text += f"🛡️ DEF    +{player.get_defense() - player.base_defense:>3}  ({player.get_defense()} total)\n"
        stats_text += f"💨 VIT    +{player.get_speed() - player.base_speed:>3}  ({player.get_speed()} total)\n"
        stats_text += "```"
        embed.add_field(name="⚔️ Stats de Combat", value=stats_text, inline=True)
        
        # Bonus économiques
        bonus_text = "```\n"
        if total_drop > 0:
            bonus_text += f"📈 DROP   +{total_drop * 100:.1f}%\n"
        else:
            bonus_text += f"📈 DROP   +0%\n"
        if total_coin > 0:
            bonus_text += f"💰 OR     +{total_coin * 100:.0f}%\n"
        else:
            bonus_text += f"💰 OR     +0%\n"
        xp_bonus = player.get_xp_bonus()
        if xp_bonus > 0:
            bonus_text += f"✨ XP     +{xp_bonus * 100:.0f}%\n"
        else:
            bonus_text += f"✨ XP     +0%\n"
        bonus_text += "```"
        embed.add_field(name="📊 Bonus Économiques", value=bonus_text, inline=True)
        
        embed.set_footer(text="💡 /equiper <item> • /desequiper-rapide • /sets")
        
        await interaction.followup.send(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 🛡️ COMMANDE EQUIPER
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="equiper", description="🛡️ Équipe un objet de ton inventaire")
    @app_commands.describe(nom="Le nom de l'objet à équiper")
    async def equip_item(self, interaction: discord.Interaction, nom: str):
        """Équipe un objet avec animation moderne."""
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
            embed = ModernEmbed.create(
                title="❌ Objet Introuvable",
                description=f"Tu ne possèdes pas d'objet nommé **{nom}**.\n\n*Utilise `/inventaire` pour voir tes objets.*",
                style="error"
            )
            await interaction.followup.send(embed=embed)
            return
        
        if not target_item.is_equipable():
            embed = ModernEmbed.create(
                title="❌ Non Équipable",
                description=(
                    f"**{target_item.name}** ne peut pas être équipé.\n\n"
                    "Seuls ces types sont équipables:\n"
                    "🪖 Casques • 🛡️ Plastrons • 👖 Jambières\n"
                    "👢 Bottes • ⚔️ Armes • 💍 Accessoires"
                ),
                style="error"
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Équiper l'item
        slot = target_item.item_type
        old_item_id = player.equip_item(target_item.item_id, slot)
        self.data.save_player(player)
        
        # Créer l'embed de succès
        rarity_color = RARITY_COLORS.get(target_item.rarity.name.lower(), ModernTheme.SUCCESS)
        embed = discord.Embed(title="", color=rarity_color)
        
        slot_info = SLOT_DISPLAY.get(slot, {"emoji": "📦", "name": slot})
        
        # Header avec animation
        header = "```ansi\n"
        header += "\u001b[1;32m╔══════════════════════════════════════╗\u001b[0m\n"
        header += "\u001b[1;32m║\u001b[0m    \u001b[1;36m✨ ÉQUIPEMENT MODIFIÉ !\u001b[0m          \u001b[1;32m║\u001b[0m\n"
        header += "\u001b[1;32m╚══════════════════════════════════════╝\u001b[0m\n"
        header += "```"
        
        embed.description = header + "\n"
        
        # Afficher le changement
        if old_item_id:
            old_item = self.data.get_item(old_item_id)
            old_display = f"{old_item.rarity.emoji} {old_item.name}" if old_item else old_item_id
            
            embed.description += f"**{slot_info['emoji']} {slot_info['name']}**\n\n"
            embed.description += f"📤 *Ancien:* {old_display}\n"
            embed.description += f"📥 *Nouveau:* {target_item.rarity.emoji} **{target_item.name}**"
        else:
            embed.description += f"**{slot_info['emoji']} {slot_info['name']}**\n\n"
            embed.description += f"📥 {target_item.rarity.emoji} **{target_item.name}** équipé !"
        
        # Bonus de set si applicable
        if target_item.set_id:
            equipment_set = self.data.get_set(target_item.set_id)
            if equipment_set:
                set_pieces = self.data.get_equipped_set_pieces(player)
                count = set_pieces.get(target_item.set_id, 0)
                progress = create_progress_bar(count, 4, 8)
                
                bonus_text = f"\n\n**📦 {equipment_set.name}**\n{progress} `{count}/4 pièces`"
                
                if count >= 2:
                    bonus_text += f"\n✅ *{equipment_set.bonus_2.get('description', 'Bonus 2p')}*"
                if count >= 4:
                    bonus_text += f"\n✅ *{equipment_set.bonus_4.get('description', 'Bonus 4p')}*"
                
                embed.description += bonus_text
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="💡 Utilise /equipement pour voir tout ton équipement")
        
        await interaction.followup.send(embed=embed)

    @equip_item.autocomplete('nom')
    async def equip_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplétion pour les items équipables."""
        player = self.data.get_player(interaction.user.id)
        choices = []
        seen_names = set()
        
        for item_id in player.inventory:
            item = self.data.get_item(item_id)
            if item and item.is_equipable():
                if item.name in seen_names:
                    continue
                if not current or current.lower() in item.name.lower():
                    seen_names.add(item.name)
                    
                    # Indicateur si déjà équipé
                    is_equipped = player.equipment.get(item.item_type) == item.item_id
                    status = " ✓" if is_equipped else ""
                    
                    # Slot info
                    slot_info = SLOT_DISPLAY.get(item.item_type, {"name": ""})
                    
                    choices.append(app_commands.Choice(
                        name=f"{item.rarity.emoji} {item.name} [{slot_info['name']}]{status}"[:100],
                        value=item.name
                    ))
        
        return choices[:25]

    # ══════════════════════════════════════════════════════════════
    # 🛡️ COMMANDE DESEQUIPER
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="desequiper", description="🛡️ Retire un équipement (avec menu)")
    @app_commands.describe(slot="Le slot à vider")
    @app_commands.choices(slot=[
        app_commands.Choice(name="🪖 Casque", value="HELMET"),
        app_commands.Choice(name="🛡️ Plastron", value="CHESTPLATE"),
        app_commands.Choice(name="👖 Jambières", value="LEGGINGS"),
        app_commands.Choice(name="👢 Bottes", value="BOOTS"),
        app_commands.Choice(name="⚔️ Arme", value="WEAPON"),
        app_commands.Choice(name="💍 Accessoire", value="ACCESSORY"),
    ])
    async def unequip_item(self, interaction: discord.Interaction, slot: str):
        """Déséquipe un objet avec feedback moderne."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        slot_info = SLOT_DISPLAY.get(slot, {"emoji": "📦", "name": slot})
        
        old_item_id = player.unequip_item(slot)
        
        if not old_item_id:
            embed = ModernEmbed.create(
                title="❌ Slot Vide",
                description=f"Tu n'as rien d'équipé dans le slot **{slot_info['emoji']} {slot_info['name']}**.",
                style="error"
            )
            await interaction.followup.send(embed=embed)
            return
        
        self.data.save_player(player)
        
        old_item = self.data.get_item(old_item_id)
        
        embed = discord.Embed(title="", color=ModernTheme.WARNING)
        
        header = "```ansi\n"
        header += "\u001b[1;33m╔══════════════════════════════════════╗\u001b[0m\n"
        header += "\u001b[1;33m║\u001b[0m      \u001b[1;36m📤 ÉQUIPEMENT RETIRÉ\u001b[0m           \u001b[1;33m║\u001b[0m\n"
        header += "\u001b[1;33m╚══════════════════════════════════════╝\u001b[0m\n"
        header += "```"
        
        old_display = f"{old_item.rarity.emoji} **{old_item.name}**" if old_item else f"**{old_item_id}**"
        
        embed.description = header + f"\n\n{slot_info['emoji']} **{slot_info['name']}** vidé !\n\n"
        embed.description += f"📤 {old_display} → Inventaire"
        
        embed.set_footer(text="💡 L'objet est retourné dans ton inventaire")
        
        await interaction.followup.send(embed=embed)

    # ══════════════════════════════════════════════════════════════
    # 🛡️ COMMANDE DESEQUIPER RAPIDE (Menu interactif)
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="desequiper-rapide", description="🛡️ Menu rapide pour déséquiper")
    async def quick_unequip(self, interaction: discord.Interaction):
        """Menu interactif pour déséquiper rapidement."""
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        # Vérifier s'il y a des items équipés
        has_equipment = any(item_id for item_id in player.equipment.values() if item_id)
        
        if not has_equipment:
            embed = ModernEmbed.create(
                title="📭 Aucun Équipement",
                description="Tu n'as aucun objet équipé !\n\n*Utilise `/equiper` pour équiper un objet.*",
                style="warning"
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(title="", color=ModernTheme.PRIMARY)
        
        header = "```ansi\n"
        header += "\u001b[1;34m╔══════════════════════════════════════╗\u001b[0m\n"
        header += "\u001b[1;34m║\u001b[0m     \u001b[1;36m🎯 DÉSÉQUIPEMENT RAPIDE\u001b[0m         \u001b[1;34m║\u001b[0m\n"
        header += "\u001b[1;34m╚══════════════════════════════════════╝\u001b[0m\n"
        header += "```"
        
        embed.description = header + "\n*Sélectionne un slot dans le menu pour retirer l'équipement:*\n\n"
        
        # Afficher les slots équipés
        for slot, item_id in player.equipment.items():
            if item_id:
                item = self.data.get_item(item_id)
                slot_info = SLOT_DISPLAY.get(slot, {"emoji": "📦", "name": slot})
                item_display = f"{item.rarity.emoji} {item.name}" if item else item_id
                embed.description += f"{slot_info['emoji']} **{slot_info['name']}**: {item_display}\n"
        
        view = UnequipView(player, self.data, interaction.user.id)
        await interaction.followup.send(embed=embed, view=view)

    # ══════════════════════════════════════════════════════════════
    # 📦 COMMANDE SETS
    # ══════════════════════════════════════════════════════════════

    @app_commands.command(name="sets", description="📦 Affiche tous les sets d'équipement disponibles")
    async def show_sets(self, interaction: discord.Interaction):
        """Affiche la liste des sets avec pagination moderne."""
        await interaction.response.defer()
        
        all_sets = self.data.get_all_sets()
        
        if not all_sets:
            embed = ModernEmbed.create(
                title="📦 Sets d'Équipement",
                description="Aucun set disponible pour le moment.",
                style="warning"
            )
            await interaction.followup.send(embed=embed)
            return
        
        view = SetPageView(all_sets, self.data, interaction.user.id)
        await interaction.followup.send(embed=view.create_embed(), view=view)


async def setup(bot: commands.Bot):
    pass
