import discord
from discord.ext import commands
from discord import app_commands

class Moderation(commands.Cog):

    # au chargement du bot -> cog
    def init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        
        # anti insulte
        word_blacklist = ["insulte1", "insulte2", "insulte3"]
    
        for mot in word_blacklist:
            if mot in message.content.lower():
                await message.delete()
                await message.channel.send(f'{message.author.mention}, ce genre de langage est interdit ici !')
                break

        # preparer une fonction setup qui va enregister le cog dans le bot
        async def setup(client):
            await client.add_cog(Moderation(client))

        @app_commands.command(name="ciao", description="casse toi de là")
        async def ciao_commands(interaction: discord.Interaction, member: discord.Member):
            await member.send('Ciao, tu as été expulsé du serveur.')
            await member.kick(reason="Ciao")
            await interaction.response.send_message(f'Ciao {member.mention}, casse toi de là !')







async def setup(client):
    await client.add_cog(Moderation(client))