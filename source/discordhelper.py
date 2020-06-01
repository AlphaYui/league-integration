# Help class that eases access to Discord-related ressources, e.g.:
#  - Getting Member objects
#  - Creating roles
#  - ...
#
# As the class must be able to associate tournament IDs with certain guilds,
# a ToornamentInterface must be provided to access this information.

import discord
from discord.ext import commands

from toornament import *

class DiscordHelper:

    # Constructor
    # bot: Discord bot instance
    # toornament: Toornament interface instance
    def __init__(self, bot, toornament: ToornamentInterface):
        self.bot = bot
        self.toornament = toornament
        self.memberConverter = commands.MemberConverter()
        self.guildCache = {}


    # Returns Discord guild object for the guild that runs the tournament with the given id.
    # Caches guild objects in a map to avoid redundant SQL and API calls.
    # tournamentID: Toornament ID of the tournament for which the organizing guild is retrieved
    def getGuild(self, tournamentID):
        try:
            # First tries to find the guild in the cache
            return self.guildCache[tournamentID]
        except:
            # If unsuccessful: Gets guild id from MySQL database
            tournament = self.toornament.getTournamentInfo(tournamentID = tournamentID)

            # Fetches guild object from bot
            guild = self.bot.get_guild(tournament.guildID)

            # Adds guild object to cache
            self.guildCache[tournament.tournamentID] = guild
            return guild


    # Returns Discord member object for given ID and context.
    # Used if implicit conversion to member object isn't possible.
    # Returns None if member can't be found.
    # ctx: Discord context object
    # discordID: Discord ID of member
    async def getMember(self, ctx, discordID):
        try:
            member = await self.memberConverter.convert(ctx, discordID)
            return member

        except commands.errors.BadArgument as err:
            return None


    # Returns Discord role object for given tournament and role id.
    # Returns None if role can't be found.
    # tournamentID: Toornament ID of the tournament the role belongs to
    # roleID: ID of the requested role
    def getRole(self, tournamentID, roleID):
        try:
            guild = self.getGuild(tournamentID)
            return guild.get_role(roleID)
        except Exception as err:
            return None


    # Creates a new Discord role for a tournament.
    # tournamentID: Toornament ID of tournament the role belongs to
    # name: Name of the role
    # roleTemplate: Optional role object. If provided, all settings of the template are copied to the new role.
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
    