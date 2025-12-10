"""
Bot Discord d'économie et de collection d'objets.
Système de gacha avec coffres, inventaire et monnaie.
"""
import os
import asyncio

from dotenv import load_dotenv
import discord
from discord.ext import commands

from services import DataManager
from cogs.admin import Admin
from cogs.chests import Chests
from cogs.inventory import Inventory
from cogs.profile import Profile
from cogs.trading import Trading
from cogs.pets import Pets
from cogs.equipment import Equipment
from cogs.battle import Battle


# Charger les variables d'environnement
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# 📋 CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

TUTORIAL_CHANNEL_ID = 1448261036858806403  # Salon pour le tutoriel
VIP_USER_ID = 238326044988276738  # Utilisateur VIP à accueillir


class EconomyBot(commands.Bot):
    """Bot Discord avec système d'économie."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            description="Bot d'économie et de collection"
        )

        # Initialiser le gestionnaire de données
        self.data_manager = DataManager(data_folder="data")
        self.tutorial_sent = False  # Pour éviter de renvoyer le tutoriel

    async def setup_hook(self):
        """Configuration initiale du bot."""
        # Charger tous les cogs
        await self.add_cog(Admin(self, self.data_manager))
        await self.add_cog(Chests(self, self.data_manager))
        await self.add_cog(Inventory(self, self.data_manager))
        await self.add_cog(Profile(self, self.data_manager))
        await self.add_cog(Trading(self, self.data_manager))
        await self.add_cog(Pets(self, self.data_manager))
        await self.add_cog(Equipment(self, self.data_manager))
        await self.add_cog(Battle(self, self.data_manager))
        
        # Synchroniser les commandes slash
        await self.tree.sync()
        print("✅ Commandes synchronisées")

    async def on_ready(self):
        """Événement déclenché quand le bot est prêt."""
        print(f"{'='*50}")
        print(f"🤖 Bot connecté : {self.user.name}")
        print(f"📊 Serveurs : {len(self.guilds)}")
        print(f"📦 Objets chargés : {len(self.data_manager.get_all_items())}")
        print(f"{'='*50}")

        # Définir le statut du bot
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="/coffre pour jouer !"
        )
        await self.change_presence(activity=activity)
        
        # Envoyer le tutoriel au démarrage
        if not self.tutorial_sent:
            await self.send_tutorial()
            self.tutorial_sent = True

    async def send_tutorial(self):
        """Envoie le message de tutoriel dans le salon dédié."""
        await asyncio.sleep(2)  # Attendre que tout soit chargé
        
        channel = self.get_channel(TUTORIAL_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Salon tutoriel {TUTORIAL_CHANNEL_ID} introuvable")
            return
        
        # Supprimer les anciens messages du bot dans ce salon
        try:
            async for message in channel.history(limit=50):
                if message.author == self.user:
                    await message.delete()
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # 📜 EMBED 1: INTRODUCTION / HISTOIRE
        # ═══════════════════════════════════════════════════════════════════════
        
        intro_embed = discord.Embed(
            title="",
            color=0xFFD700
        )
        
        intro_embed.description = (
            "```ansi\n"
            "\u001b[1;33m╔══════════════════════════════════════════════════════════╗\u001b[0m\n"
            "\u001b[1;33m║\u001b[0m         ⚔️ \u001b[1;36mBIENVENUE, AVENTURIER !\u001b[0m ⚔️                   \u001b[1;33m║\u001b[0m\n"
            "\u001b[1;33m╚══════════════════════════════════════════════════════════╝\u001b[0m\n"
            "```\n\n"
            "🌍 **L'Histoire**\n\n"
            "*Dans un monde où la richesse détermine le pouvoir, tu débarques en tant qu'aventurier anonyme.*\n\n"
            "*Armé de ton courage et de ta chance, tu devras ouvrir des **coffres mystérieux**, "
            "collectionner des **objets rares**, affronter des **boss légendaires** et élever des **compagnons uniques**.*\n\n"
            "*Ton objectif ? Devenir l'**Empereur Légendaire** - le joueur le plus riche et le plus puissant du royaume !*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        
        intro_embed.add_field(
            name="🎯 Tes Objectifs",
            value=(
                "```\n"
                "💰 Amasser 1,000,000+ pièces\n"
                "📦 Collectionner tous les objets Mythiques\n"
                "👹 Vaincre l'Empereur du Néant (Boss final)\n"
                "🐾 Capturer tous les pets légendaires\n"
                "```"
            ),
            inline=False
        )
        
        intro_embed.set_thumbnail(url=self.user.display_avatar.url)
        
        await channel.send(embed=intro_embed)
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════════════════════════════════════
        # 📜 EMBED 2: COMMANDES ÉCONOMIE
        # ═══════════════════════════════════════════════════════════════════════
        
        economy_embed = discord.Embed(
            title="💰 Économie & Collection",
            color=0x2ECC71
        )
        
        economy_embed.description = (
            "*Gagne des pièces et collectionne des objets rares !*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        economy_embed.add_field(
            name="🎁 Coffres",
            value=(
                "`/coffre` - Ouvre un coffre gratuit (50/jour)\n"
                "`/coffre payer:True` - Coffre bonus (3,500 💰)\n"
                "`/coffres [nombre]` - Ouvre plusieurs coffres\n"
                "`/taux` - Affiche les taux de drop"
            ),
            inline=False
        )
        
        economy_embed.add_field(
            name="🎒 Inventaire",
            value=(
                "`/inventaire` - Voir ta collection\n"
                "`/inventaire rarete:Mythique` - Filtrer par rareté\n"
                "`/vendre [objet]` - Vendre un objet\n"
                "`/vendretout [rareté]` - Vendre en masse"
            ),
            inline=False
        )
        
        economy_embed.add_field(
            name="🔄 Échanges",
            value=(
                "`/trade [joueur] [objet]` - Proposer un échange\n"
                "`/cadeau [joueur] [objet]` - Offrir un objet\n"
                "`/donner [joueur] [montant]` - Donner des pièces"
            ),
            inline=False
        )
        
        economy_embed.add_field(
            name="📊 Raretés",
            value=(
                "```\n"
                "⬜ Normal    │ 50%   │ Commun\n"
                "🟦 Rare      │ 30%   │ Peu commun\n"
                "🟪 Épique    │ 15%   │ Rare\n"
                "🟨 Légendaire│  4%   │ Très rare\n"
                "🟥 Mythique  │  1%   │ Ultra rare !\n"
                "```"
            ),
            inline=False
        )
        
        await channel.send(embed=economy_embed)
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════════════════════════════════════
        # 📜 EMBED 3: COMBAT & BOSS
        # ═══════════════════════════════════════════════════════════════════════
        
        combat_embed = discord.Embed(
            title="⚔️ Combat & Boss",
            color=0xE74C3C
        )
        
        combat_embed.description = (
            "*Affronte des boss puissants et monte en niveau !*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        combat_embed.add_field(
            name="👹 Commandes de Combat",
            value=(
                "`/combat [boss]` - Affronter un boss\n"
                "`/boss` - Liste des boss disponibles\n"
                "`/stats-combat` - Tes stats de combat"
            ),
            inline=False
        )
        
        combat_embed.add_field(
            name="✨ Compétences",
            value=(
                "`/skills` - Voir tes compétences\n"
                "`/debloquer-skill [skill]` - Débloquer une skill\n"
                "`/equiper-skill [skill]` - Équiper une skill"
            ),
            inline=False
        )
        
        combat_embed.add_field(
            name="📈 Système de Niveau",
            value=(
                "```\n"
                "• Gagne de l'XP en battant des boss\n"
                "• +10 PV par niveau\n"
                "• +2 ATK par niveau\n"
                "• Débloque des skills en montant de niveau\n"
                "• 10 boss à vaincre !\n"
                "```"
            ),
            inline=False
        )
        
        combat_embed.add_field(
            name="🏆 Boss Disponibles",
            value=(
                "🟢 **Roi Slime** (Niv.1) - *Facile*\n"
                "👺 **Chef Gobelin** (Niv.3) - *Facile*\n"
                "💀 **Seigneur Squelette** (Niv.5) - *Moyen*\n"
                "🔥 **Élémentaire de Feu** (Niv.8) - *Moyen*\n"
                "🐉 **Dragon de Glace** (Niv.12) - *Difficile*\n"
                "*...et 5 autres boss légendaires !*"
            ),
            inline=False
        )
        
        await channel.send(embed=combat_embed)
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════════════════════════════════════
        # 📜 EMBED 4: PETS & ÉQUIPEMENT
        # ═══════════════════════════════════════════════════════════════════════
        
        pets_embed = discord.Embed(
            title="🐾 Pets & Équipement",
            color=0xE91E63
        )
        
        pets_embed.description = (
            "*Adopte des compagnons et équipe-toi pour devenir plus fort !*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        pets_embed.add_field(
            name="🥚 Pets (Compagnons)",
            value=(
                "`/oeuf` - Ouvre un œuf mystérieux (5,000 💰)\n"
                "`/pets` - Voir ta collection de pets\n"
                "`/equiper-pet [nom]` - Équiper un pet\n"
                "`/oeufs-info` - Taux de drop des œufs\n\n"
                "*Les pets augmentent ton taux de drop !*"
            ),
            inline=False
        )
        
        pets_embed.add_field(
            name="🛡️ Équipement",
            value=(
                "`/equipement` - Voir ton équipement\n"
                "`/equiper [objet]` - Équiper un objet\n"
                "`/desequiper [slot]` - Retirer un équipement\n"
                "`/sets` - Voir les sets disponibles"
            ),
            inline=False
        )
        
        pets_embed.add_field(
            name="📦 Slots d'Équipement",
            value=(
                "```\n"
                "🪖 Casque    │ 🛡️ Plastron\n"
                "👖 Jambières │ 👢 Bottes\n"
                "⚔️ Arme      │ 💍 Accessoire\n"
                "```"
            ),
            inline=False
        )
        
        pets_embed.add_field(
            name="✨ Bonus de Set",
            value=(
                "*Équipe 4 pièces du même set pour des bonus spéciaux !*\n"
                "• **2 pièces**: Petit bonus\n"
                "• **4 pièces**: Bonus complet"
            ),
            inline=False
        )
        
        await channel.send(embed=pets_embed)
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════════════════════════════════════
        # 📜 EMBED 5: PROFIL & CLASSEMENT
        # ═══════════════════════════════════════════════════════════════════════
        
        profile_embed = discord.Embed(
            title="👤 Profil & Classement",
            color=0x9B59B6
        )
        
        profile_embed.description = (
            "*Consulte tes stats et compare-toi aux autres !*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        profile_embed.add_field(
            name="📋 Commandes",
            value=(
                "`/profil` - Voir ton profil\n"
                "`/profil [joueur]` - Voir le profil d'un joueur\n"
                "`/classement` - Top des joueurs\n"
                "`/classement type:Niveau` - Classement par niveau\n"
                "`/stats` - Statistiques du serveur\n"
                "`/boutique` - Voir la boutique"
            ),
            inline=False
        )
        
        profile_embed.add_field(
            name="🏅 Rangs de Richesse",
            value=(
                "```\n"
                "🌱 Débutant        │     0+ 💰\n"
                "🌟 Apprenti        │ 5,000+ 💰\n"
                "⭐ Étoile          │ 10,000+ 💰\n"
                "🥉 Bronze          │ 25,000+ 💰\n"
                "🥈 Argent          │ 50,000+ 💰\n"
                "🥇 Or              │ 100,000+ 💰\n"
                "💎 Diamant         │ 250,000+ 💰\n"
                "🏆 Grand Maître    │ 500,000+ 💰\n"
                "👑 Empereur        │ 1,000,000+ 💰\n"
                "```"
            ),
            inline=False
        )
        
        await channel.send(embed=profile_embed)
        await asyncio.sleep(1)
        
        # ═══════════════════════════════════════════════════════════════════════
        # 📜 EMBED 6: CONSEILS
        # ═══════════════════════════════════════════════════════════════════════
        
        tips_embed = discord.Embed(
            title="💡 Conseils de Pro",
            color=0xF39C12
        )
        
        tips_embed.description = (
            "```ansi\n"
            "\u001b[1;33m━━━━━━ STRATÉGIES GAGNANTES ━━━━━━\u001b[0m\n"
            "```"
        )
        
        tips_embed.add_field(
            name="🚀 Démarrage",
            value=(
                "1️⃣ Ouvre tes **50 coffres gratuits** chaque jour\n"
                "2️⃣ Vends les objets **Normaux** pour des pièces\n"
                "3️⃣ Garde les objets **Épiques+** pour les sets\n"
                "4️⃣ Achète un **pet** dès que possible (+drop%)"
            ),
            inline=False
        )
        
        tips_embed.add_field(
            name="⚔️ Combat",
            value=(
                "1️⃣ Commence par le **Roi Slime** (facile)\n"
                "2️⃣ Monte de niveau avant d'affronter les boss difficiles\n"
                "3️⃣ Équipe des **skills de soin** pour survivre\n"
                "4️⃣ Les boss donnent beaucoup d'**XP et pièces** !"
            ),
            inline=False
        )
        
        tips_embed.add_field(
            name="💰 Économie",
            value=(
                "1️⃣ `/vendretout Normal` pour vendre en masse\n"
                "2️⃣ Échange avec les autres joueurs\n"
                "3️⃣ Complète les **sets** pour les bonus de vente\n"
                "4️⃣ Les pets boostent le drop = plus de pièces !"
            ),
            inline=False
        )
        
        tips_embed.add_field(
            name="🎮 Raccourcis Utiles",
            value=(
                "• Les commandes ont l'**autocomplete** - tape juste le début !\n"
                "• Utilise `/inventaire rarete:X` pour filtrer\n"
                "• `/desequiper-rapide` pour un menu interactif"
            ),
            inline=False
        )
        
        tips_embed.set_footer(text="🎮 Bonne chance, Aventurier ! Que la RNG soit avec toi !")
        
        await channel.send(embed=tips_embed)
        
        print(f"✅ Tutoriel envoyé dans #{channel.name}")

    async def on_member_join(self, member: discord.Member):
        """Événement quand un membre rejoint le serveur."""
        # Vérifier si c'est l'utilisateur VIP
        if member.id == VIP_USER_ID:
            await self.welcome_vip_user(member)

    async def welcome_vip_user(self, member: discord.Member):
        """Accueille l'utilisateur VIP et restreint l'accès aux salons."""
        guild = member.guild
        
        # Trouver ou créer un rôle VIP
        vip_role = discord.utils.get(guild.roles, name="VIP Bot Master")
        
        if not vip_role:
            try:
                # Créer le rôle avec permissions limitées (pas d'admin)
                vip_role = await guild.create_role(
                    name="VIP Bot Master",
                    color=discord.Color.gold(),
                    hoist=True,  # Affiché séparément
                    permissions=discord.Permissions.none(),  # Pas de permissions par défaut
                    reason="Rôle VIP pour accès au bot uniquement"
                )
                print(f"✅ Rôle 'VIP Bot Master' créé")
            except Exception as e:
                print(f"❌ Erreur création rôle: {e}")
                return
        
        # Donner le rôle à l'utilisateur
        try:
            await member.add_roles(vip_role, reason="Utilisateur VIP")
            print(f"✅ Rôle VIP donné à {member.display_name}")
        except Exception as e:
            print(f"❌ Erreur attribution rôle: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🔒 CACHER TOUS LES SALONS SAUF LE SALON TUTORIEL
        # ═══════════════════════════════════════════════════════════════
        
        tutorial_channel = self.get_channel(TUTORIAL_CHANNEL_ID)
        
        # Parcourir tous les salons et les cacher pour cet utilisateur
        for channel in guild.channels:
            try:
                if channel.id == TUTORIAL_CHANNEL_ID:
                    # Donner accès UNIQUEMENT au salon tutoriel
                    await channel.set_permissions(
                        member,
                        view_channel=True,
                        read_messages=True,
                        send_messages=True,
                        read_message_history=True,
                        use_application_commands=True  # Peut utiliser les commandes slash
                    )
                    print(f"✅ Accès donné à #{channel.name}")
                else:
                    # Cacher tous les autres salons
                    await channel.set_permissions(
                        member,
                        view_channel=False,
                        read_messages=False
                    )
            except Exception as e:
                print(f"⚠️ Erreur sur {channel.name}: {e}")
        
        print(f"🔒 Accès restreint configuré pour {member.display_name}")
        
        # Envoyer un message de bienvenue
        try:
            welcome_embed = discord.Embed(
                title="👑 Bienvenue, VIP !",
                color=discord.Color.gold()
            )
            
            welcome_embed.description = (
                f"```ansi\n"
                f"\u001b[1;33m╔══════════════════════════════════════╗\u001b[0m\n"
                f"\u001b[1;33m║\u001b[0m   👑 ACCÈS VIP ACTIVÉ ! 👑           \u001b[1;33m║\u001b[0m\n"
                f"\u001b[1;33m╚══════════════════════════════════════╝\u001b[0m\n"
                f"```\n\n"
                f"Salut **{member.display_name}** ! 🎉\n\n"
                f"Tu as accès au salon **#graven-controle** pour jouer au bot !\n\n"
                f"**Commandes disponibles:**\n"
                f"• `/coffre` - Ouvrir des coffres\n"
                f"• `/inventaire` - Voir ta collection\n"
                f"• `/profil` - Ton profil\n"
                f"• `/boss` - Combattre des boss\n"
                f"• `/pets` - Tes compagnons\n\n"
                f"📖 Tout est expliqué dans le salon !"
            )
            
            welcome_embed.set_thumbnail(url=member.display_avatar.url)
            welcome_embed.set_footer(text="🎮 Amuse-toi bien !")
            
            # Envoyer en DM
            await member.send(embed=welcome_embed)
            print(f"✅ Message de bienvenue envoyé à {member.display_name}")
        except discord.Forbidden:
            print(f"⚠️ Impossible d'envoyer un DM à {member.display_name}")
        except Exception as e:
            print(f"❌ Erreur message bienvenue: {e}")


def main():
    """Point d'entrée du bot."""
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ Erreur: DISCORD_TOKEN non trouvé dans le fichier .env")
        print("Créez un fichier .env avec: DISCORD_TOKEN=votre_token")
        return

    bot = EconomyBot()
    bot.run(token)


if __name__ == "__main__":
    main()
