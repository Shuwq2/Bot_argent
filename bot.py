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
from cogs.economy import Economy
from cogs.admin import Admin


# Charger les variables d'environnement
load_dotenv()


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

    async def setup_hook(self):
        """Configuration initiale du bot."""
        # Charger les cogs
        await self.add_cog(Economy(self, self.data_manager))
        await self.add_cog(Admin(self, self.data_manager))
        
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
