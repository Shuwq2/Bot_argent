"""
Cog gérant les combats de boss en temps réel avec interface interactive ultra-moderne.
Style tour par tour comme Pokémon avec design moderne.
"""
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict, List
import asyncio
import random
from datetime import datetime, date

from models import Boss, Skill, SkillType, CombatState
from services import DataManager
from utils import COLORS, EMOJIS
from utils.styles import (
    Colors, Emojis, EmbedTheme,
    create_hp_bar, create_xp_bar, create_stat_bar,
    create_header, create_mini_header, create_separator,
    create_box, create_stat_display, create_level_display,
    create_combat_stats_display, create_reward_display,
    create_rarity_indicator, format_number
)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎮 VIEWS MODERNES POUR L'INTERFACE DE COMBAT
# ═══════════════════════════════════════════════════════════════════════════════

class ModernBattleView(discord.ui.View):
    """Interface de combat interactive ultra-moderne avec boutons stylisés."""
    
    def __init__(self, cog, combat: CombatState, player, skills: List[Skill]):
        super().__init__(timeout=120)
        self.cog = cog
        self.combat = combat
        self.player = player
        self.skills = skills
        self.waiting_for_action = True
        self.selected_skill = None
        
        self._create_modern_buttons()
    
    def _create_modern_buttons(self):
        """Crée des boutons modernes pour chaque action."""
        for i, skill in enumerate(self.skills[:4]):
            on_cooldown = self.combat.skill_cooldowns.get(skill.skill_id, 0) > 0
            cooldown_text = f" ⏱{self.combat.skill_cooldowns.get(skill.skill_id, 0)}" if on_cooldown else ""
            
            style = self._get_modern_style(skill.skill_type, on_cooldown)
            
            button = discord.ui.Button(
                label=f"{skill.name}{cooldown_text}",
                emoji=skill.emoji,
                style=style,
                disabled=on_cooldown,
                row=0 if i < 2 else 1,
                custom_id=f"skill_{i}"
            )
            button.callback = self._make_skill_callback(skill)
            self.add_item(button)
        
        # Bouton de fuite stylisé
        flee_button = discord.ui.Button(
            label="Fuir",
            emoji="💨",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        flee_button.callback = self._flee_callback
        self.add_item(flee_button)
    
    def _get_modern_style(self, skill_type: SkillType, on_cooldown: bool) -> discord.ButtonStyle:
        """Style moderne selon le type de skill."""
        if on_cooldown:
            return discord.ButtonStyle.secondary
        
        styles = {
            SkillType.ATTACK: discord.ButtonStyle.danger,
            SkillType.DEFENSE: discord.ButtonStyle.primary,
            SkillType.HEAL: discord.ButtonStyle.success,
            SkillType.SPECIAL: discord.ButtonStyle.primary,
            SkillType.BUFF: discord.ButtonStyle.success,
            SkillType.DEBUFF: discord.ButtonStyle.secondary
        }
        return styles.get(skill_type, discord.ButtonStyle.secondary)
    
    def _make_skill_callback(self, skill: Skill):
        """Callback moderne pour un skill."""
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.combat.player_id:
                embed = discord.Embed(
                    description=f"{Emojis.ERROR} **Ce n'est pas ton combat !**",
                    color=Colors.ERROR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            self.selected_skill = skill
            self.waiting_for_action = False
            self.stop()
            await interaction.response.defer()
        
        return callback
    
    async def _flee_callback(self, interaction: discord.Interaction):
        """Callback de fuite moderne."""
        if interaction.user.id != self.combat.player_id:
            embed = discord.Embed(
                description=f"{Emojis.ERROR} **Ce n'est pas ton combat !**",
                color=Colors.ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        self.selected_skill = None
        self.waiting_for_action = False
        self.stop()
        await interaction.response.defer()


# ═══════════════════════════════════════════════════════════════════════════════
# ⚔️ COG BATTLE - SYSTÈME DE COMBAT MODERNE
# ═══════════════════════════════════════════════════════════════════════════════

class Battle(commands.Cog):
    """Système de combat ultra-moderne avec boss et progression."""
    
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data = data_manager
        self.active_combats: Dict[int, CombatState] = {}
    
    # ───────────────────────────────────────────────────────────────
    # 🔍 AUTOCOMPLETE FUNCTIONS
    # ───────────────────────────────────────────────────────────────
    
    async def boss_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour les noms de boss."""
        player = self.data.get_player(interaction.user.id)
        bosses = self.data.get_all_bosses()
        
        choices = []
        for boss in bosses:
            unlocked = player.level >= boss.level_required
            lock = "" if unlocked else "🔒 "
            display = f"{lock}{boss.emoji} {boss.name} (Niv.{boss.level_required})"
            
            if current.lower() in boss.name.lower() or not current:
                choices.append(app_commands.Choice(name=display[:100], value=boss.name))
        
        return choices[:25]
    
    async def skill_unlock_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour les skills à débloquer."""
        player = self.data.get_player(interaction.user.id)
        all_skills = self.data.get_all_skills()
        
        choices = []
        for skill in all_skills:
            if skill.skill_id in player.skills:
                continue  # Déjà débloqué
            
            unlocked = player.level >= skill.level_required
            lock = "" if unlocked else "🔒 "
            display = f"{lock}{skill.emoji} {skill.name} ({skill.skill_type.value})"
            
            if current.lower() in skill.name.lower() or not current:
                choices.append(app_commands.Choice(name=display[:100], value=skill.name))
        
        return choices[:25]
    
    async def skill_equip_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour les skills à équiper."""
        player = self.data.get_player(interaction.user.id)
        
        choices = []
        for skill_id in player.skills:
            if skill_id in player.equipped_skills:
                continue  # Déjà équipé
            
            skill = self.data.get_skill(skill_id)
            if skill:
                level = player.skills.get(skill_id, 1)
                display = f"{skill.emoji} {skill.name} Niv.{level}"
                
                if current.lower() in skill.name.lower() or not current:
                    choices.append(app_commands.Choice(name=display[:100], value=skill.name))
        
        return choices[:25]
    
    async def skill_unequip_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete pour les skills à déséquiper."""
        player = self.data.get_player(interaction.user.id)
        
        choices = []
        for skill_id in player.equipped_skills:
            skill = self.data.get_skill(skill_id)
            if skill:
                level = player.skills.get(skill_id, 1)
                display = f"{skill.emoji} {skill.name} Niv.{level}"
                
                if current.lower() in skill.name.lower() or not current:
                    choices.append(app_commands.Choice(name=display[:100], value=skill.name))
        
        return choices[:25]
    
    # ───────────────────────────────────────────────────────────────
    # 📊 COMMANDE NIVEAU - AFFICHAGE MODERNE
    # ───────────────────────────────────────────────────────────────
    
    @app_commands.command(name="niveau", description="📊 Affiche ton niveau et tes stats de combat")
    async def show_level(self, interaction: discord.Interaction):
        """Affiche les stats de niveau du joueur avec design moderne."""
        player = self.data.get_player(interaction.user.id)
        
        current_xp, required_xp, percentage = player.get_xp_progress()
        
        embed = discord.Embed(color=Colors.PRIMARY)
        
        # Header moderne
        embed.title = f"{Emojis.STATS} Profil de Combat"
        
        # Niveau avec style
        level_display = create_level_display(player.level, current_xp, required_xp)
        xp_bar = create_xp_bar(current_xp, required_xp, 16)
        
        embed.description = (
            f"```ansi\n"
            f"\u001b[0;37m╔{'═' * 32}╗\u001b[0m\n"
            f"\u001b[0;37m║\u001b[0m  {Emojis.STAR} \u001b[1;33mNIVEAU {player.level}\u001b[0m {level_display:>18}\u001b[0;37m║\u001b[0m\n"
            f"\u001b[0;37m╚{'═' * 32}╝\u001b[0m\n"
            f"```"
        )
        
        # Barre XP moderne
        embed.add_field(
            name=f"{Emojis.XP} Expérience",
            value=f"{xp_bar}\n{Emojis.COIN} **{format_number(current_xp)}** / **{format_number(required_xp)}** XP `({percentage}%)`",
            inline=False
        )
        
        # Stats de combat avec barres visuelles
        max_stat = max(player.get_attack(), player.get_defense(), player.get_speed(), 100)
        
        hp_bar = create_hp_bar(player.current_hp, player.get_max_hp(), 10)
        atk_bar = create_stat_bar(player.get_attack(), max_stat, 8)
        def_bar = create_stat_bar(player.get_defense(), max_stat, 8)
        spd_bar = create_stat_bar(player.get_speed(), max_stat, 8)
        
        stats_text = (
            f"{Emojis.HP} **PV** {hp_bar} `{player.current_hp}/{player.get_max_hp()}`\n"
            f"{Emojis.ATTACK} **ATK** {atk_bar} `{player.get_attack()}`\n"
            f"{Emojis.DEFENSE} **DEF** {def_bar} `{player.get_defense()}`\n"
            f"{Emojis.SPEED} **VIT** {spd_bar} `{player.get_speed()}`"
        )
        embed.add_field(name=f"{Emojis.SWORD} Stats de Combat", value=stats_text, inline=True)
        
        # Compétences
        skills_text = (
            f"{Emojis.SKILL} **Points**: `{player.skill_points}`\n"
            f"📚 **Débloqués**: `{len(player.skills)}`\n"
            f"🎒 **Équipés**: `{len(player.equipped_skills)}/4`"
        )
        embed.add_field(name=f"{Emojis.STAR} Compétences", value=skills_text, inline=True)
        
        # Progression boss
        boss_text = (
            f"👹 **Boss vaincus**: `{player.bosses_defeated}`\n"
            f"{Emojis.TROPHY} **XP total**: `{format_number(player.total_xp)}`"
        )
        embed.add_field(name=f"{Emojis.TROPHY} Progression", value=boss_text, inline=False)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="💡 Utilise /boss pour combattre et gagner de l'XP !", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    # ───────────────────────────────────────────────────────────────
    # 👹 COMMANDE BOSS - LISTE MODERNE
    # ───────────────────────────────────────────────────────────────
    
    @app_commands.command(name="boss", description="👹 Affiche la liste des boss disponibles")
    async def boss_list(self, interaction: discord.Interaction):
        """Affiche les boss avec un design moderne."""
        player = self.data.get_player(interaction.user.id)
        bosses = self.data.get_all_bosses()
        
        # Récupérer l'XP pour l'affichage du niveau
        current_xp, xp_required, _ = player.get_xp_progress()
        
        embed = discord.Embed(
            title=f"👹 Arène des Boss",
            description=(
                f"```ansi\n"
                f"\u001b[1;31m╔{'═' * 36}╗\u001b[0m\n"
                f"\u001b[1;31m║\u001b[0m    ⚔️ CHOISISSEZ VOTRE ADVERSAIRE ⚔️   \u001b[1;31m║\u001b[0m\n"
                f"\u001b[1;31m╚{'═' * 36}╝\u001b[0m\n"
                f"```\n"
                f"Ton niveau: **{player.level}** {create_level_display(player.level, current_xp, xp_required)}"
            ),
            color=Colors.DANGER
        )
        
        for boss in bosses[:9]:  # Max 9 pour éviter le dépassement
            unlocked = player.level >= boss.level_required
            kills = player.bosses_kills.get(boss.boss_id, 0)
            defeated = kills > 0  # Boss déjà battu
            
            # Emoji de statut
            if defeated:
                lock_emoji = "✅"  # Boss vaincu
            elif unlocked:
                lock_emoji = "🔓"  # Débloqué mais pas vaincu
            else:
                lock_emoji = "�"  # Verrouillé
            
            # Nom du boss barré si déjà battu
            boss_name = f"~~{boss.name}~~" if defeated else boss.name
            
            if unlocked:
                boss_info = (
                    f"┌─ {boss.difficulty.emoji} `{boss.difficulty.display_name}`\n"
                    f"├ {Emojis.HP} `{boss.max_hp}` PV │ {Emojis.ATTACK} `{boss.attack}` ATK\n"
                    f"├ {Emojis.XP} `{format_number(boss.xp_reward)}` XP │ {Emojis.COIN} `{format_number(boss.coins_reward)}`\n"
                    f"└ {Emojis.TROPHY} Victoires: `{kills}`"
                )
            else:
                boss_info = (
                    f"```diff\n"
                    f"- Niveau {boss.level_required} requis\n"
                    f"```\n"
                    f"┌─ {boss.difficulty.emoji} `{boss.difficulty.display_name}`\n"
                    f"└ {Emojis.XP} `{format_number(boss.xp_reward)}` XP"
                )
            
            embed.add_field(
                name=f"{lock_emoji} {boss.emoji} {boss_name}",
                value=boss_info,
                inline=True
            )
        
        embed.set_footer(
            text="💡 /combat <boss> pour lancer un combat !",
            icon_url=self.bot.user.display_avatar.url
        )
        await interaction.response.send_message(embed=embed)
    
    # ───────────────────────────────────────────────────────────────
    # ⚔️ COMMANDE COMBAT - SYSTÈME PRINCIPAL MODERNE
    # ───────────────────────────────────────────────────────────────
    
    @app_commands.command(name="combat", description="⚔️ Lance un combat contre un boss")
    @app_commands.describe(boss="Le nom du boss à combattre")
    @app_commands.autocomplete(boss=boss_autocomplete)
    async def start_combat(self, interaction: discord.Interaction, boss: str):
        """Lance un combat avec interface moderne."""
        # Defer immédiatement pour éviter les timeout
        await interaction.response.defer()
        
        player = self.data.get_player(interaction.user.id)
        
        # Vérifications
        if interaction.user.id in self.active_combats:
            await interaction.followup.send(
                embed=self._error_embed("Combat en cours", "Tu es déjà en combat ! Termine-le d'abord."),
                ephemeral=True
            )
            return
        
        target_boss = self.data.get_boss_by_name(boss)
        if not target_boss:
            await interaction.followup.send(
                embed=self._error_embed("Boss introuvable", f"Aucun boss nommé **{boss}**.\nUtilise `/boss` pour voir la liste."),
                ephemeral=True
            )
            return
        
        if player.level < target_boss.level_required:
            await interaction.followup.send(
                embed=self._error_embed(
                    "Niveau insuffisant",
                    f"Tu dois être **niveau {target_boss.level_required}** pour affronter {target_boss.emoji} **{target_boss.name}**.\n"
                    f"Ton niveau: **{player.level}**"
                ),
                ephemeral=True
            )
            return
        
        if player.current_hp <= 0:
            player.heal_full()
            self.data.save_player(player)
        
        # Mettre à jour les stats d'équipement avant le combat
        player.update_equipment_stats(self.data)
        
        # Initialisation du combat avec stats d'équipement
        target_boss.reset_hp()
        combat = CombatState(
            player_id=interaction.user.id,
            boss=target_boss,
            player_hp=player.current_hp,
            player_max_hp=player.get_max_hp(),
            player_attack=player.get_attack(),
            player_defense=player.get_defense()
        )
        
        self.active_combats[interaction.user.id] = combat
        player_skills = self._get_player_combat_skills(player)
        
        # Animation d'apparition moderne
        intro_embed = discord.Embed(
            color=Colors.DANGER
        )
        
        intro_embed.title = f"⚔️ COMBAT ENGAGÉ"
        intro_embed.description = (
            f"```ansi\n"
            f"\u001b[1;31m╔{'═' * 40}╗\u001b[0m\n"
            f"\u001b[1;31m║\u001b[0m{target_boss.emoji:^10}{target_boss.name:^20}{target_boss.emoji:^10}\u001b[1;31m║\u001b[0m\n"
            f"\u001b[1;31m║\u001b[0m{target_boss.difficulty.emoji:^10}{target_boss.difficulty.display_name:^20}{target_boss.difficulty.emoji:^10}\u001b[1;31m║\u001b[0m\n"
            f"\u001b[1;31m╚{'═' * 40}╝\u001b[0m\n"
            f"```\n"
            f"*{target_boss.description}*"
        )
        
        if target_boss.image_url:
            intro_embed.set_image(url=target_boss.image_url)
        
        intro_embed.add_field(
            name="Stats du Boss",
            value=(
                f"{Emojis.HP} **PV**: `{target_boss.max_hp}`\n"
                f"{Emojis.ATTACK} **ATK**: `{target_boss.attack}`\n"
                f"{Emojis.DEFENSE} **DEF**: `{target_boss.defense}`"
            ),
            inline=True
        )
        
        intro_embed.add_field(
            name="Tes Stats",
            value=(
                f"{Emojis.HP} **PV**: `{combat.player_hp}`\n"
                f"{Emojis.ATTACK} **ATK**: `{combat.player_attack}`\n"
                f"{Emojis.DEFENSE} **DEF**: `{combat.player_defense}`"
            ),
            inline=True
        )
        
        message = await interaction.followup.send(embed=intro_embed)
        await asyncio.sleep(2)
        
        # Boucle de combat moderne
        while combat.boss.is_alive() and combat.player_hp > 0:
            combat_embed = self._create_modern_combat_embed(combat, player, interaction.user)
            view = ModernBattleView(self, combat, player, player_skills)
            
            await message.edit(embed=combat_embed, view=view)
            await view.wait()
            
            if view.selected_skill is None:
                # Fuite
                del self.active_combats[interaction.user.id]
                flee_embed = discord.Embed(
                    title="💨 Retraite Stratégique",
                    description=(
                        f"Tu as fui le combat contre {target_boss.emoji} **{target_boss.name}** !\n\n"
                        f"```diff\n- Aucune récompense obtenue\n```"
                    ),
                    color=Colors.SECONDARY
                )
                await message.edit(embed=flee_embed, view=None)
                return
            
            skill = view.selected_skill
            
            # Tour du joueur
            player_result = await self._execute_player_turn(combat, player, skill)
            combat.add_log(player_result)
            
            if skill.cooldown > 0:
                combat.skill_cooldowns[skill.skill_id] = skill.cooldown
            
            if not combat.boss.is_alive():
                break
            
            # Tour du boss
            boss_result = await self._execute_boss_turn(combat, player)
            combat.add_log(boss_result)
            
            # Effets DoT
            dot_damage = combat.apply_dots()
            if dot_damage > 0:
                combat.player_hp -= dot_damage
                combat.add_log(f"🔥 Brûlure: `-{dot_damage}` PV !")
            
            combat.tick_cooldowns()
            combat.tick_buffs()
            combat.turn += 1
            
            await asyncio.sleep(0.5)
        
        # Fin du combat
        del self.active_combats[interaction.user.id]
        
        if combat.player_hp <= 0:
            player.current_hp = 1
            self.data.save_player(player)
            
            defeat_embed = discord.Embed(
                title="💀 DÉFAITE",
                description=(
                    f"```ansi\n"
                    f"\u001b[1;30m╔{'═' * 36}╗\u001b[0m\n"
                    f"\u001b[1;30m║\u001b[0m      💀 TU AS ÉTÉ VAINCU... 💀      \u001b[1;30m║\u001b[0m\n"
                    f"\u001b[1;30m╚{'═' * 36}╝\u001b[0m\n"
                    f"```\n"
                    f"{target_boss.emoji} **{target_boss.name}** t'a écrasé...\n\n"
                    f"```diff\n- Aucune récompense\n```\n"
                    f"💡 *Améliore ton équipement et réessaie !*"
                ),
                color=Colors.SECONDARY
            )
            await message.edit(embed=defeat_embed, view=None)
        else:
            victory_embed = await self._process_victory(combat, player, target_boss, interaction.user)
            await message.edit(embed=victory_embed, view=None)
    
    def _create_modern_combat_embed(self, combat: CombatState, player, user: discord.User) -> discord.Embed:
        """Crée l'embed de combat moderne."""
        boss = combat.boss
        
        embed = discord.Embed(
            title=f"⚔️ Tour {combat.turn}",
            color=Colors.DANGER
        )
        
        # Barres de vie modernes
        boss_hp_bar = create_hp_bar(boss.current_hp, boss.max_hp, 12)
        player_hp_bar = create_hp_bar(combat.player_hp, combat.player_max_hp, 12)
        
        embed.add_field(
            name=f"{boss.emoji} {boss.name}",
            value=f"{boss_hp_bar}\n`{boss.current_hp}/{boss.max_hp}` PV",
            inline=True
        )
        
        embed.add_field(
            name=f"⚡ VS ⚡",
            value="═══════",
            inline=True
        )
        
        embed.add_field(
            name=f"👤 {user.display_name}",
            value=f"{player_hp_bar}\n`{combat.player_hp}/{combat.player_max_hp}` PV",
            inline=True
        )
        
        # Effets actifs
        effects = []
        if combat.player_buffs:
            for buff, turns in combat.player_buffs.items():
                if buff == "attack":
                    effects.append(f"{Emojis.ATTACK} ATK+ `{turns}t`")
                elif buff == "defense":
                    effects.append(f"{Emojis.DEFENSE} DEF+ `{turns}t`")
        
        if combat.player_dots:
            effects.append(f"🔥 Brûlure active")
        
        if combat.boss_debuffs.get("stun", 0) > 0:
            effects.append(f"💫 Boss étourdi")
        
        if effects:
            embed.add_field(
                name="📊 Effets Actifs",
                value=" │ ".join(effects),
                inline=False
            )
        
        # Log de combat
        if combat.combat_log:
            log_entries = combat.combat_log[-3:]
            log_text = "\n".join([f"▸ {entry}" for entry in log_entries])
            embed.add_field(
                name="📜 Actions",
                value=f"```\n{log_text}\n```",
                inline=False
            )
        
        embed.set_footer(text="⚔️ Choisis ton action ci-dessous !")
        
        return embed
    
    async def _execute_player_turn(self, combat: CombatState, player, skill: Skill) -> str:
        """Exécute le tour du joueur."""
        result = f"{skill.emoji} {skill.name}"
        
        if random.randint(1, 100) > skill.accuracy:
            return result + " → RATÉ !"
        
        if skill.base_power > 0:
            level_bonus = player.level // 5
            attack_boost = combat.player_buffs.get("attack", 0) * 0.5
            damage = skill.calculate_damage(combat.player_attack + int(combat.player_attack * attack_boost), level_bonus)
            
            actual_damage = combat.boss.take_damage(damage)
            result += f" → -{actual_damage} PV"
            
            if skill.lifesteal > 0:
                heal = int(actual_damage * skill.lifesteal)
                combat.player_hp = min(combat.player_max_hp, combat.player_hp + heal)
                result += f" (+{heal} vol)"
        
        if skill.heal_percent > 0:
            heal = int(combat.player_max_hp * skill.heal_percent)
            combat.player_hp = min(combat.player_max_hp, combat.player_hp + heal)
            result += f" → +{heal} PV"
        
        if skill.defense_boost > 0:
            combat.player_buffs["defense"] = 3
            result += f" [DEF+]"
        
        if skill.attack_boost > 0:
            combat.player_buffs["attack"] = 2
            result += f" [ATK+]"
        
        if skill.dot_damage > 0:
            combat.boss_debuffs["dot"] = skill.dot_turns
            result += f" [🔥]"
        
        if skill.stun_chance > 0 and random.random() < skill.stun_chance:
            combat.boss_debuffs["stun"] = 1
            result += f" [💫]"
        
        return result
    
    async def _execute_boss_turn(self, combat: CombatState, player) -> str:
        """Exécute le tour du boss."""
        boss = combat.boss
        
        if combat.boss_debuffs.get("stun", 0) > 0:
            return f"{boss.emoji} {boss.name} est étourdi !"
        
        attack = boss.choose_attack()
        result = f"{attack.emoji} {boss.name}: {attack.name}"
        
        defense_boost = combat.player_buffs.get("defense", 0) * 0.5
        effective_defense = combat.player_defense + int(combat.player_defense * defense_boost)
        damage = max(1, attack.damage - effective_defense // 2)
        
        combat.player_hp = max(0, combat.player_hp - damage)
        result += f" → -{damage} PV"
        
        if attack.special_effect == "dot":
            combat.player_dots.append((int(attack.effect_value), 3))
            result += " [🔥]"
        elif attack.special_effect == "lifesteal":
            heal = int(damage * attack.effect_value)
            boss.current_hp = min(boss.max_hp, boss.current_hp + heal)
            result += f" (+{heal})"
        elif attack.special_effect == "heal":
            heal = int(boss.max_hp * attack.effect_value)
            boss.current_hp = min(boss.max_hp, boss.current_hp + heal)
            result += f" [Soin +{heal}]"
        
        return result
    
    async def _process_victory(self, combat: CombatState, player, boss: Boss, user: discord.User) -> discord.Embed:
        """Traite la victoire avec design moderne."""
        # Mettre à jour les stats d'équipement
        player.update_equipment_stats(self.data)
        
        # Calculer les récompenses avec bonus d'équipement
        base_xp = boss.xp_reward
        base_coins = boss.coins_reward
        
        xp_bonus = player.get_xp_bonus()
        coin_bonus = player.get_coin_bonus()
        
        xp_gained = int(base_xp * (1 + xp_bonus))
        coins_gained = int(base_coins * (1 + coin_bonus))
        
        # Texte bonus si applicable
        bonus_text = ""
        if xp_bonus > 0 or coin_bonus > 0:
            bonus_text = f"\n*Bonus équipement: +{int(xp_bonus*100)}% XP, +{int(coin_bonus*100)}% 💰*"
        
        levels_gained = player.add_xp(xp_gained)
        player.add_coins(coins_gained)
        player.bosses_defeated += 1
        player.bosses_kills[boss.boss_id] = player.bosses_kills.get(boss.boss_id, 0) + 1
        player.current_hp = combat.player_hp
        
        drops = []
        for item_id in boss.guaranteed_drops:
            player.add_item(item_id, 1)
            item = self.data.get_item(item_id)
            if item:
                drops.append(f"{item.rarity.emoji} **{item.name}**")
        
        for item_id, chance in boss.drop_items.items():
            if random.random() < chance:
                player.add_item(item_id, 1)
                item = self.data.get_item(item_id)
                if item:
                    drops.append(f"{item.rarity.emoji} **{item.name}**")
        
        self.data.save_player(player)
        
        embed = discord.Embed(color=Colors.SUCCESS)
        
        embed.title = f"🎉 VICTOIRE !"
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;32m╔{'═' * 36}╗\u001b[0m\n"
            f"\u001b[1;32m║\u001b[0m       🏆 BOSS ÉLIMINÉ ! 🏆          \u001b[1;32m║\u001b[0m\n"
            f"\u001b[1;32m╚{'═' * 36}╝\u001b[0m\n"
            f"```\n"
            f"Tu as vaincu {boss.emoji} **{boss.name}** !{bonus_text}"
        )
        
        # Récompenses
        rewards = create_reward_display(xp_gained, coins_gained)
        embed.add_field(name=f"{Emojis.GIFT} Récompenses", value=rewards, inline=True)
        
        if drops:
            embed.add_field(
                name="📦 Butin",
                value="\n".join(drops),
                inline=True
            )
        
        if levels_gained:
            if len(levels_gained) > 1:
                level_text = (
                    f"```diff\n"
                    f"+ MULTI LEVEL UP ! (+{len(levels_gained)})\n"
                    f"```\n"
                    f"⭐ Niveau **{player.level}**\n"
                    f"{Emojis.SKILL} +{len(levels_gained)} points de compétence !"
                )
            else:
                level_text = (
                    f"```diff\n"
                    f"+ LEVEL UP !\n"
                    f"```\n"
                    f"⭐ Niveau **{player.level}**\n"
                    f"{Emojis.SKILL} +1 point de compétence !"
                )
            embed.add_field(name=f"{Emojis.LEVEL_UP} Progression", value=level_text, inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"❤️ PV restants: {combat.player_hp}/{combat.player_max_hp}")
        
        return embed
    
    def _get_player_combat_skills(self, player) -> List[Skill]:
        """Récupère les skills de combat du joueur."""
        skills = []
        
        basic_attack = self.data.get_skill("basic_attack")
        if basic_attack:
            skills.append(basic_attack)
        
        heal_skill = self.data.get_skill("heal")
        if heal_skill and player.level >= heal_skill.level_required:
            skills.append(heal_skill)
        
        for skill_id in player.equipped_skills:
            skill = self.data.get_skill(skill_id)
            if skill and skill not in skills:
                skills.append(skill)
        
        return skills[:4]
    
    # ───────────────────────────────────────────────────────────────
    # ✨ COMMANDES SKILLS MODERNES
    # ───────────────────────────────────────────────────────────────
    
    @app_commands.command(name="skills", description="✨ Affiche et gère tes compétences")
    async def show_skills(self, interaction: discord.Interaction):
        """Affiche les skills avec design moderne."""
        player = self.data.get_player(interaction.user.id)
        all_skills = self.data.get_all_skills()
        
        embed = discord.Embed(
            title=f"{Emojis.SKILL} Compétences",
            color=Colors.SPECIAL
        )
        
        embed.description = (
            f"```ansi\n"
            f"\u001b[1;35m╔{'═' * 30}╗\u001b[0m\n"
            f"\u001b[1;35m║\u001b[0m  {Emojis.SKILL} Points: {player.skill_points:^15} \u001b[1;35m║\u001b[0m\n"
            f"\u001b[1;35m╚{'═' * 30}╝\u001b[0m\n"
            f"```"
        )
        
        # Skills équipés
        equipped_text = ""
        for i, skill_id in enumerate(player.equipped_skills):
            skill = self.data.get_skill(skill_id)
            if skill:
                level = player.skills.get(skill_id, 1)
                equipped_text += f"`{i+1}.` {skill.emoji} **{skill.name}** `Niv.{level}`\n"
        
        if not equipped_text:
            equipped_text = "*Aucun skill équipé*\n💡 Utilise `/equiper-skill` !"
        
        embed.add_field(name="🎒 Équipés (4 max)", value=equipped_text, inline=False)
        
        # Skills débloqués
        unlocked_text = ""
        for skill_id, level in player.skills.items():
            skill = self.data.get_skill(skill_id)
            if skill:
                equipped = " ✓" if skill_id in player.equipped_skills else ""
                unlocked_text += f"{skill.emoji} **{skill.name}** `Niv.{level}`{equipped}\n"
        
        if unlocked_text:
            embed.add_field(name="📚 Débloqués", value=unlocked_text[:1000], inline=True)
        
        # Skills disponibles
        available_text = ""
        for skill in all_skills:
            if skill.skill_id not in player.skills and player.level >= skill.level_required:
                available_text += f"{skill.emoji} **{skill.name}** `{skill.skill_type.value}`\n"
        
        if available_text:
            embed.add_field(name="🔓 Disponibles", value=available_text[:1000], inline=True)
        
        embed.set_footer(
            text="💡 /debloquer-skill • /equiper-skill • /desequiper-skill",
            icon_url=self.bot.user.display_avatar.url
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="debloquer-skill", description="🔓 Débloque une nouvelle compétence")
    @app_commands.describe(nom="Nom de la compétence à débloquer")
    @app_commands.autocomplete(nom=skill_unlock_autocomplete)
    async def unlock_skill(self, interaction: discord.Interaction, nom: str):
        """Débloque un skill avec feedback moderne."""
        player = self.data.get_player(interaction.user.id)
        skill = self.data.get_skill_by_name(nom)
        
        if not skill:
            await interaction.response.send_message(
                embed=self._error_embed("Skill introuvable", f"Aucun skill nommé **{nom}**."),
                ephemeral=True
            )
            return
        
        if player.level < skill.level_required:
            await interaction.response.send_message(
                embed=self._error_embed("Niveau insuffisant", f"Tu dois être niveau **{skill.level_required}** pour ce skill."),
                ephemeral=True
            )
            return
        
        if player.skill_points <= 0:
            await interaction.response.send_message(
                embed=self._error_embed("Pas de points", "Tu n'as pas de points de compétence.\nMonte de niveau !"),
                ephemeral=True
            )
            return
        
        already_unlocked = skill.skill_id in player.skills
        player.unlock_skill(skill.skill_id)
        self.data.save_player(player)
        
        if already_unlocked:
            embed = discord.Embed(
                title=f"⬆️ Skill Amélioré !",
                description=(
                    f"```diff\n+ {skill.name} → Niveau {player.skills[skill.skill_id]}\n```\n"
                    f"{skill.emoji} **{skill.name}** est maintenant plus puissant !"
                ),
                color=Colors.PRIMARY
            )
        else:
            embed = discord.Embed(
                title=f"🔓 Nouveau Skill !",
                description=(
                    f"```diff\n+ {skill.name} débloqué !\n```\n"
                    f"{skill.emoji} **{skill.name}**\n"
                    f"*{skill.description}*"
                ),
                color=Colors.SUCCESS
            )
        
        embed.set_footer(text=f"🎯 Points restants: {player.skill_points}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="equiper-skill", description="🎒 Équipe une compétence pour le combat")
    @app_commands.describe(nom="Nom de la compétence à équiper")
    @app_commands.autocomplete(nom=skill_equip_autocomplete)
    async def equip_skill(self, interaction: discord.Interaction, nom: str):
        """Équipe un skill avec feedback moderne."""
        player = self.data.get_player(interaction.user.id)
        skill = self.data.get_skill_by_name(nom)
        
        if not skill:
            await interaction.response.send_message(
                embed=self._error_embed("Skill introuvable", f"Aucun skill nommé **{nom}**."),
                ephemeral=True
            )
            return
        
        if skill.skill_id not in player.skills:
            await interaction.response.send_message(
                embed=self._error_embed("Non débloqué", "Débloque ce skill avec `/debloquer-skill` d'abord."),
                ephemeral=True
            )
            return
        
        if skill.skill_id in player.equipped_skills:
            await interaction.response.send_message(
                embed=self._error_embed("Déjà équipé", "Ce skill est déjà équipé !"),
                ephemeral=True
            )
            return
        
        if len(player.equipped_skills) >= 4:
            await interaction.response.send_message(
                embed=self._error_embed("Limite atteinte", "Tu as déjà 4 skills équipés !\nUtilise `/desequiper-skill` d'abord."),
                ephemeral=True
            )
            return
        
        player.equip_skill(skill.skill_id)
        self.data.save_player(player)
        
        embed = discord.Embed(
            title=f"🎒 Skill Équipé !",
            description=(
                f"```diff\n+ {skill.name} équipé\n```\n"
                f"{skill.emoji} **{skill.name}** est prêt au combat !"
            ),
            color=Colors.SUCCESS
        )
        embed.set_footer(text=f"🎒 {len(player.equipped_skills)}/4 skills équipés")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="desequiper-skill", description="🎒 Retire une compétence équipée")
    @app_commands.describe(nom="Nom de la compétence à retirer")
    @app_commands.autocomplete(nom=skill_unequip_autocomplete)
    async def unequip_skill(self, interaction: discord.Interaction, nom: str):
        """Déséquipe un skill avec feedback moderne."""
        player = self.data.get_player(interaction.user.id)
        skill = self.data.get_skill_by_name(nom)
        
        if not skill:
            await interaction.response.send_message(
                embed=self._error_embed("Skill introuvable", f"Aucun skill nommé **{nom}**."),
                ephemeral=True
            )
            return
        
        if skill.skill_id not in player.equipped_skills:
            await interaction.response.send_message(
                embed=self._error_embed("Non équipé", "Ce skill n'est pas équipé !"),
                ephemeral=True
            )
            return
        
        player.unequip_skill(skill.skill_id)
        self.data.save_player(player)
        
        embed = discord.Embed(
            title=f"🎒 Skill Retiré",
            description=f"{skill.emoji} **{skill.name}** a été déséquipé.",
            color=Colors.SECONDARY
        )
        embed.set_footer(text=f"🎒 {len(player.equipped_skills)}/4 skills équipés")
        await interaction.response.send_message(embed=embed)
    
    # ───────────────────────────────────────────────────────────────
    # 💚 COMMANDE SOIN MODERNE
    # ───────────────────────────────────────────────────────────────
    
    @app_commands.command(name="soin", description="💚 Restaure tes PV (coûte des pièces)")
    async def heal(self, interaction: discord.Interaction):
        """Soigne le joueur avec design moderne."""
        player = self.data.get_player(interaction.user.id)
        
        if player.current_hp >= player.get_max_hp():
            await interaction.response.send_message(
                embed=self._error_embed("PV au max", "Tu as déjà tous tes PV !"),
                ephemeral=True
            )
            return
        
        heal_cost = (player.get_max_hp() - player.current_hp) * 2
        
        if player.coins < heal_cost:
            await interaction.response.send_message(
                embed=self._error_embed(
                    "Pas assez de pièces",
                    f"Le soin coûte **{format_number(heal_cost)}** pièces.\nTu as **{format_number(player.coins)}** pièces."
                ),
                ephemeral=True
            )
            return
        
        old_hp = player.current_hp
        player.coins -= heal_cost
        player.heal_full()
        self.data.save_player(player)
        
        old_bar = create_hp_bar(old_hp, player.get_max_hp(), 10)
        new_bar = create_hp_bar(player.current_hp, player.get_max_hp(), 10)
        
        embed = discord.Embed(
            title=f"💚 Soin Complet !",
            description=(
                f"```diff\n+ Récupération totale !\n```\n"
                f"**Avant**: {old_bar} `{old_hp}`\n"
                f"**Après**: {new_bar} `{player.current_hp}`\n\n"
                f"{Emojis.COIN} Coût: **{format_number(heal_cost)}** pièces"
            ),
            color=Colors.SUCCESS
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
