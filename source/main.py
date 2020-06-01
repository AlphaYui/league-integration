# Bot main file
# Execute this file to launch the bot.
# Detailed bot documentation will be added at a later stage in development.

from authorization import AuthorizationInfo
from mysqlwrapper import MySQLWrapper
from toornament import ToornamentInterface, PlayerInfo, TeamInfo
from discordhelper import DiscordHelper
from config import BotConfig

import discord
from discord import Colour, Embed
from discord.ext import commands

import traceback

auth = AuthorizationInfo("auth.json")
mysql = MySQLWrapper(auth)
toornament = ToornamentInterface(auth, mysql)

bot = commands.Bot(command_prefix = '.ecc')
discordHelper = DiscordHelper(bot, toornament)
cfg = BotConfig(discordHelper, mysql)

##### COMMANDS #####

# Tries to fetch all teams from toornament, create team roles for them and give them to players.
@bot.command()
async def all(ctx: commands.Context, tournamentID: int):


    try:
        # Gets team role template for this tournament
        teamRoleTemplate = cfg.getTeamRoleTemplate(tournamentID)

        # Gets information of all participating teams
        allTeams = toornament.getAllTeamInfo(tournamentID)
        msg = ""

        for teamInfo in allTeams:
            msg += f"\nTeam '{teamInfo.name}':\n"
            
            # Creates new role for this team
            teamRole = await discordHelper.createRole(tournamentID, teamInfo.name, teamRoleTemplate)

            # Tries to find manager in Discord server
            manager = await discordHelper.getMember(ctx, teamInfo.managerDiscordID)

            if manager is None:
                msg += f"    Manager '{teamInfo.managerDiscordID}' couldn't be found\n"
            else:
                # Converts Manager ID to Discord Developer ID
                msg += f"    Manager '{teamInfo.managerDiscordID}' has been found: {manager.mention} with id {manager.id}\n"
                teamInfo.managerDiscordID = manager.id

                # Gives Manager the new team role
                await manager.add_roles(teamRole, reason = "Manager of team")

            # Iterates over team lineup
            for playerInfo in teamInfo.lineup:
                # Tries to find player in Discord server
                player = await discordHelper.getMember(ctx, playerInfo.discordID)

                if player is None:
                    msg += f"    Player '{playerInfo.discordID}' couldn't be found\n"
                else:
                    # Converts Player ID to Discord Developer ID
                    msg += f"    Player '{playerInfo.discordID}' has been found: {player.mention} with id {player.id}\n"
                    playerInfo.discordID = player.id

                    # Gives Player the new team role
                    await player.add_roles(teamRole, reason = "Player on team")
            
            # Updates team information on toornament with the converted Discord IDs
            toornament.patchTeamInfo(tournamentID, teamInfo)

        await ctx.send(msg)
        exit()
    except Exception as e:
        print(traceback.format_exc())
        exit()

# Creates default configuration for a certain touranment
@bot.command()
async def createdefault(ctx, tournamentID):
    try:
        cfg.createDefaultConfig(tournamentID)
    except Exception as e:
        print(traceback.format_exc())
        exit()

# Adds a new tournament to a Discord
@bot.command()
async def addtournament(ctx, tournamentID):
    toornament.addTournament(tournamentID, ctx.guild.id, "Test")

print("Starting bot...")
bot.run(auth.discordToken)
