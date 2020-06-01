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

# Commands go here
@bot.command()
async def all(ctx: commands.Context, tournamentID: int):

    teamRoleTemplate = cfg.getTeamRoleTemplate(tournamentID)

    try:
        allTeams = toornament.getAllTeamInfo(tournamentID)
        msg = ""

        for teamInfo in allTeams:
            msg += f"\nTeam '{teamInfo.name}':\n"
            
            teamRole = await discordHelper.createRole(tournamentID, teamInfo.name, teamRoleTemplate)

            manager = await discordHelper.getMember(ctx, teamInfo.managerDiscordID)

            if manager is None:
                msg += f"    Manager '{teamInfo.managerDiscordID}' couldn't be found\n"
            else:
                msg += f"    Manager '{teamInfo.managerDiscordID}' has been found: {manager.mention} with id {manager.id}\n"
                teamInfo.managerDiscordID = manager.id
                await manager.add_roles(teamRole, reason = "Manager of team")

            for playerInfo in teamInfo.lineup:
                player = await discordHelper.getMember(ctx, playerInfo.discordID)

                if player is None:
                    msg += f"    Player '{playerInfo.discordID}' couldn't be found\n"
                else:
                    msg += f"    Player '{playerInfo.discordID}' has been found: {player.mention} with id {player.id}\n"
                    playerInfo.discordID = player.id
                    await player.add_roles(teamRole, reason = "Player on team")
            
            toornament.patchTeamInfo(tournamentID, teamInfo)

        
        await ctx.send(msg)
        exit()
    except Exception as e:
        print(traceback.format_exc())
        exit()

@bot.command()
async def createdefault(ctx, tournamentID):
    try:
        cfg.createDefaultConfig(tournamentID)
    except Exception as e:
        print(traceback.format_exc())
        exit()

@bot.command()
async def addtournament(ctx, tournamentID):
    toornament.addTournament(tournamentID, ctx.guild.id, "Test")

print("Starting bot...")
bot.run(auth.discordToken)
