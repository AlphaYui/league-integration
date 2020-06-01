import discord
from discord.ext import commands

from toornament import *

class DiscordHelper:

    def __init__(self, bot, toornament: ToornamentInterface):
        self.bot = bot
        self.toornament = toornament
        self.memberConverter = commands.MemberConverter()
        self.guildCache = {}

    def getGuild(self, tournamentID):
        try:
            return self.guildCache[tournamentID]
        except:
            tournament = self.toornament.getTournamentInfo(tournamentID = tournamentID)
            guild = self.bot.get_guild(tournament.guildID)
            self.guildCache[tournament.tournamentID] = guild
            return guild

    async def getMember(self, ctx, discordID):
        try:
            member = await self.memberConverter.convert(ctx, discordID)
            return member

        except commands.errors.BadArgument as err:
            return None

    def getRole(self, tournamentID, roleID):
        try:
            guild = self.getGuild(tournamentID)
            return guild.get_role(roleID)
        except Exception as err:
            return None

    async def createRole(self, tournamentID, name, roleTemplate: discord.Role = None):
        
        guild = self.getGuild(tournamentID)

        if roleTemplate is None:
            return await guild.create_role(name = name)
        else:
            return await guild.create_role(
                name = name,
                permissions = roleTemplate.permissions,
                colour = roleTemplate.colour,
                hoist = roleTemplate.hoist,
                mentionable = roleTemplate.mentionable
            )
    