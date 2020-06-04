# The Toornament interface is used to fetch information on players, teams and tournaments easily.
# To associate Discord users, roles and emotes with Toornament data, a local MySQL database is used.
# It contains the following tables:
#
# Teams
# Participant: Toornament participant ID of the team
# RoleID: Unique ID of the Discord role associated with the team
# EmoteID: Unique ID of the Discord emote associated with the team
# Name: Name of the team on Toornament and in Discord
# TournamentID: Toornament ID of the tournament the team plays in
#
# Tournaments
# TournamentID: Toornament ID of the tournament
# GuildID: Unique ID of the Discord server the tournament is hosted by
# Name: Name of the tournament on Toornament and Discord

from authorization import AuthorizationInfo
from mysqlwrapper import MySQLWrapper
from utility import toStr
import json
import requests
import datetime
import pause
import parse
from typing import List

# This class contains all relevant player information from toornament
class PlayerInfo:

    def __init__(self):
        self.name = ""

    @classmethod
    def fromJSON(cls, playerJSON):
        info = cls()
        info.name = playerJSON['name']
        info.userID = playerJSON['user_id']
        info.email = playerJSON['email']
        
        customJSON = playerJSON['custom_fields']
        info.discordID = toStr(customJSON['discord_id'])
        info.country = customJSON['country']
        info.steamID = customJSON['steam_id']
        info.psnID = customJSON['psn_id']
        info.xboxID = customJSON['xbox_live_gamertag']
        info.nintendoID = customJSON['nintendo_network_id']
        info.trackerLink = customJSON['rltracker_link']
        info.trackerLinkAlt = customJSON['rltracker_link_alt_account_']

        return info

    def toJSON(self):
        return {
            "name": self.name,
            "user_id": self.userID,
            "email": self.email,
            "custom_fields": {
                "discord_id": f"{self.discordID}",
                "country": self.country,
                "steam_id": self.steamID,
                "psn_id": self.psnID,
                "xbox_live_gamertag": self.xboxID,
                "nintendo_network_id": self.nintendoID,
                "rltracker_link": self.trackerLink,
                "rltracker_link_alt_account_": self.trackerLinkAlt
            }
        }


# This class contains all relevant team information from toornament and Discord
class TeamInfo:

    def __init__(self):
        self.name = ""
        self.roleID = 0
        self.emoteID = 0

    @classmethod
    def fromJSON(cls, teamJSON):
        info = cls()
        info.name = teamJSON['name']
        info.id = teamJSON['id']
        info.email = teamJSON['email']

        customJSON = teamJSON['custom_fields']
        info.shortName = customJSON['short_name']
        info.previousName = customJSON['previous_team_name']
        info.twitterURL = customJSON['twitter']
        info.twitchURL = customJSON['twitch']
        info.managerDiscordID = toStr(customJSON['manager_discord_id'])

        info.lineup = []

        for memberJSON in teamJSON['lineup']:
            memberInfo = PlayerInfo.fromJSON(memberJSON)
            info.lineup += [memberInfo]

        return info

    def toJSON(self):

        # Gets JSON for every team member and combines them into a list
        lineupJSON = []

        for playerInfo in self.lineup:
            lineupJSON += [playerInfo.toJSON()]

        # Generates team JSON
        return {
            "name": self.name,
            "id": self.id,
            "email": self.email,
            "custom_fields": {
                "short_name": self.shortName,
                "previous_team_name": self.previousName,
                "twitter": self.twitterURL,
                "twitch": self.twitchURL,
                "manager_discord_id": f"{self.managerDiscordID}"
            },
            "lineup": lineupJSON
        }

    # Returns information about player with a certain Discord ID from the team lineup
    # discordID: Unique Discord Developer ID of the player
    def getPlayerInfo(self, discordID):
        for player in self.lineup:
            if player.discordID == discordID:
                return player
        
        return None


# This class associates a tournament ID with a guild and optionally a name
class TournamentInfo:

    def __init__(self, name = None, guildID = None, tournamentID = None):
        self.name = name
        self.guildID = guildID
        self.tournamentID = tournamentID


# This class contains all relevant information for a toornament signup.
# For this the TeamInfo class is reused. The ID stored by RegistrationInfo
# is a unique registration identifier, while the participant ID is stored by
# the TeamInfo object.
class RegistrationInfo:

    def __init__(self):
        self.id = ""

    @classmethod
    def fromJSON(cls, regJSON):
        self.team = TeamInfo.fromJSON(regJSON)
        self.team.id = regJSON['participant_id']
        self.id = regJSON['id']

    def toJSON(self):
        teamJSON = self.team.toJSON()
        teamJSON['id'] = self.id
        teamJSON['participant_id'] = self.team.id
        return teamJSON


# Provides various methods to retrieve team and player information from toornament.
class ToornamentInterface:

    # Constructor
    # authorization: Authorization self object
    # mysql: MySQL wrapper object
    # overwrite: If set to True, existing tables will be dropped and overwritten
    def __init__(self, authorization: AuthorizationInfo, mysqlWrapper: MySQLWrapper, overwrite: bool = False):
        self.auth = authorization
        self.mysql = mysqlWrapper
        self.endpointCooldown = datetime.datetime.now()

        self.__initAllTables()


    # Creates all SQL tables that don't exist yet
    # overwrite: If set to True, existing tables will be dropped and overwritten
    def __initAllTables(self, overwrite: bool = False):
        self.mysql.createTable("Teams", (
            "ParticipantID BIGINT NOT NULL, "
            "RoleID BIGINT NOT NULL, "
            "EmoteID VARCHAR(255) NOT NULL, "
            "Name VARCHAR(63) NOT NULL, "
            "TournamentID BIGINT NOT NULL, "
            "PRIMARY KEY(ParticipantID)"
        ), overwrite = overwrite)

        self.mysql.createTable("Tournaments", (
            "TournamentID BIGINT NOT NULL, "
            "GuildID BIGINT NOT NULL, "
            "Name VARCHAR(63) NOT NULL, "
            "PRIMARY KEY(TournamentID)"
        ), overwrite = overwrite)

        self.mysql.createTable("RegistrationIssues", (
            "IssueID INT AUTO_INCREMENT, "
            "RegistrationID BIGINT NOT NULL, "
            "Description VARCHAR(1023) NOT NULL, "
            "PRIMARY KEY (IssueID)"
        ), overwrite = overwrite)


    # Checks if the authorization token has expired. If it has, tries to get a new one.
    def __checkAuthorizationToken(self):
        if self.auth.hasToornamentAuthExpired():

            # Requests new authorization token from OAuth2 endpoint
            # See: https://developer.toornament.com/v2/doc/security_oauth2#post:oauthv2token
            requestURL = "https://api.toornament.com/oauth/v2/token"

            requestHeaders = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            requestData = {
                "grant_type": "client_credentials",
                "scope": "organizer:participant",
                "client_id": self.auth.toornamentClientID,
                "client_secret": self.auth.toornamentClientSecret
            }

            response = self.__requestPost(url = requestURL, data = requestData, headers = requestHeaders, authorization=False)
            self.auth.replaceToornamentAuthKey(response)


    # Checks the time since the last endpoint call and cools down if necessary.
    # Currently a rate limit of 3 calls/second is used. (This is implemented as a 0.333sec minimum cooldown)
    def __respectRateLimits(self):
        if datetime.datetime.now() < self.endpointCooldown:
            pause.until(self.endpointCooldown)
        
        self.endpointCooldown = datetime.datetime.now() + datetime.timedelta(milliseconds=333)


    # Sends a GET request to a toornament API endpoint. Takes care of authorization&API tokens, rate limits and response validation.
    # url: The API endpoint URL
    # headers: The additional headers to be provided to the API. Authorization and API-Token are added automatically by this method and must not be given to it manually!
    # authorization: If this is True, the method will refresh the OAuth2 authorization token and add it to the request header
    def __requestGet(self, url: str, headers = {}, authorization: bool = False):
        # Updates OAuth2 authorization and adds the token to the headers
        if authorization:
            self.__checkAuthorizationToken()
            headers['Authorization'] = self.auth.toornamentAuthKey
        
        # Adds API-token to header
        headers['X-Api-Key'] = self.auth.toornamentToken
        
        # Respects rate limits
        self.__respectRateLimits()

        # Sends GET request
        response = requests.get(url = url, headers = headers)

        # Returns response as JSON if it is OK
        if response.ok:
            return response.json()
        else:
            raise response.raise_for_status()


    # Sends a POST request to a toornament API endpoint. Takes care of authorization&API tokens, rate limits and response validation.
    # url: The API endpoint URL
    # data: The data to be sent with the request
    # headers: The additional headers to be provided to the API. Authorization and API-Token are added automatically by this method and must not be given to it manually!
    # authorization: If this is True, the method will refresh the OAuth2 authorization token and add it to the request header
    def __requestPost(self, url: str, data = None, headers = {}, authorization: bool = False):
        
        # Updates OAuth2 authorization and adds the token to the headers
        if authorization:
            self.__checkAuthorizationToken()
            headers['Authorization'] = self.auth.toornamentAuthKey
        
        # Adds API-token to header
        headers['X-Api-Key'] = self.auth.toornamentToken
        
        # Respects rate limits
        self.__respectRateLimits()

        # Sends POST request
        response = requests.post(url = url, data = data, headers = headers)

        # Returns response as JSON if it is OK
        if response.ok:
            return response.json()
        else:
            raise response.raise_for_status()


    # Sends a PATCH request to a toornament API endpoint. Takes care of authorization&API tokens, rate limits and response validation.
    # url: The API endpoint URL
    # data: The data to be sent with the request
    # headers: The additional headers to be provided to the API. Authorization and API-Token are added automatically by this method and must not be given to it manually!
    # authorization: If this is True, the method will refresh the OAuth2 authorization token and add it to the request header
    def __requestPatch(self, url: str, data = None, headers = {}, authorization: bool = False):

        # Updates OAuth2 authorization and adds the token to the headers
        if authorization:
            self.__checkAuthorizationToken()
            headers['Authorization'] = self.auth.toornamentAuthKey
        
        # Adds API-token to header
        headers['X-Api-Key'] = self.auth.toornamentToken
        
        # Respects rate limits
        self.__respectRateLimits()

        # Sends POST request
        response = requests.patch(url = url, data = json.dumps(data), headers = headers)

        # Returns response as JSON if it is OK
        if response.ok:
            return response.json()
        else:
            raise response.raise_for_status()


    # Retrieves multiple pages of content via GET-requests and returns them as one result.
    # More infos about pagination: https://developer.toornament.com/v2/overview/pagination
    # url: The API endpoint URL
    # headers: The additional headers to be provided to the API. Authorization, API-token and range are added automatically and must not be given manually!
    # authorization: If this is True, the method will refresh the OAuth2 authorization token and add it to the request header
    # unit: The unit in which the paginated content is counted (e.g. tournaments, items, participants, etc)
    # itemsPerRequest: How many items can be requested per page. Consult toornament API documentation to get the right number for your API endpoint.
    def __requestPaginatedContent(self, url: str, headers = {}, authorization: bool =  False, unit: str = "items", itemsPerRequest: int = 50):
    
        # Updates OAuth2 authorization and adds the token to the headers
        if authorization:
            self.__checkAuthorizationToken()
            headers['Authorization'] = self.auth.toornamentAuthKey
        
        # Adds API-token to header
        headers['X-Api-Key'] = self.auth.toornamentToken

        # Defines Content-Range return format used to determine if the last page is reached
        contentRangeFormat = f"{unit} {{:d}}-{{:d}}/{{:d}}"
        pageStart = 0
        totalPageNumber = 1
        pageCollection = []

        while pageStart < totalPageNumber:
            # Adds updated range to header
            pageEnd = pageStart + itemsPerRequest - 1
            headers['Range'] = f"{unit}={pageStart}-{pageEnd}"

            # Respect rate limit
            self.__respectRateLimits()

            # Request next set of pages
            response = requests.get(url = url, headers = headers)

            if response.ok:
                # Adds new pages to the full collection
                pageCollection += response.json()

                # Retrieve information on how many pages are left from response headers
                contentRangeStr = response.headers['Content-Range']
                parsedContentRange = parse.parse(contentRangeFormat, contentRangeStr)
                lastPageIndex = parsedContentRange[1]
                totalPageNumber = parsedContentRange[2]

                # Calculates which is the next page to be retrieved
                pageStart = lastPageIndex + 1
            else:
                response.raise_for_status()

        return pageCollection


    # Fetches all information on a team signed up for a certain tournament on toornament.
    # Either roleID or name must be supplied or a ValueError will be raised.
    # tournamentID: Toornament ID of the tournament the team signed up for
    # roleID: Discord ID of the role used to tag the team
    # name: Name of the team used in the Discord and on Toornament
    def getTeamInfo(self, tournamentID, roleID = None, name: str = None) -> TeamInfo:
        # Fetches the toornament participant ID associated with the team
        if roleID is not None:
            self.mysql.query("SELECT ParticipantID, RoleID, EmoteID FROM Teams WHERE RoleID=%s AND TournamentID=%s;", (roleID, tournamentID,))
        elif name is not None:
            self.mysql.query("SELECT ParticipantID, RoleID, EmoteID FROM Teams WHERE Name=%s AND TournamentID=%s;", (name, tournamentID,))
        else:
            raise ValueError("Either a role id or a team name must be provided")

        results = self.mysql.fetchResults()

        if results is None:
            raise Exception(f"Team with roleID '{roleID}' or name '{name}' doesn't exist for tournament {tournamentID}")
        else:
            participantID = results[0][0]
            roleID = results[0][1]
            emoteID = results[0][2]

            # Requests user information from toornament participant endpoint
            # See: https://developer.toornament.com/v2/doc/organizer_participants#get:tournaments:tournament_id:participants:id
            requestURL = f"https://api.toornament.com/organizer/v2/tournaments/{tournamentID}/participants/{participantID}"
            response = self.__requestGet(url = requestURL, authorization=True)

            # Converts reponse and adds Discord-related information
            info = TeamInfo.fromJSON(response.json())
            info.roleID = roleID
            info.emoteID = emoteID
            return info
    

    # Fetch all information on all teams signed up for a certain tournament on toornament.
    # tournamentID: Toornament ID of the tournament the team signed up for
    def getAllTeamInfo(self, tournamentID) -> List[TeamInfo]:
        # Fetches all participants from the tournament
        requestURL = f"https://api.toornament.com/organizer/v2/tournaments/{tournamentID}/participants"
        response = self.__requestPaginatedContent(url = requestURL, authorization = True, unit = "participants", itemsPerRequest=50)

        # Converts all participants and adds them to a list
        allTeamInfo = []

        for teamJSON in response:
            allTeamInfo += [TeamInfo.fromJSON(teamJSON)]

        return allTeamInfo


    # Updates team information on toornament with the team object that is given.
    # See: https://developer.toornament.com/v2/doc/organizer_participants#patch:tournaments:tournament_id:participants:id
    # Additionally updates the MySQL database with the team role&emote.
    # tournamentID: Toornament ID of the tournament the team signed up for
    # teamInfo: TeamInfo-object containing the new team data to be patched on Toornament
    def patchTeamInfo(self, tournamentID, teamInfo: TeamInfo):
        requestURL = f"https://api.toornament.com/organizer/v2/tournaments/{tournamentID}/participants/{teamInfo.id}"
        requestData = teamInfo.toJSON()
        self.__requestPatch(url = requestURL, data = requestData, authorization=True)

        self.mysql.query(
            (
                "INSERT INTO Teams (ParticipantID, RoleID, EmoteID, Name, TournamentID) "
                "VALUES (%(participantID)s, %(roleID)s, %(emoteID)s, %(name)s, %(tournamentID)s) "
                "ON DUPLICATE KEY UPDATE RoleID=%(roleID)s, EmoteID=%(emoteID)s, Name=%(name)s;"
            ),
            {
                "participantID": teamInfo.id,
                "roleID": teamInfo.roleID,
                "emoteID": teamInfo.emoteID,
                "name": teamInfo.name,
                "tournamentID": tournamentID
            }
        )

        self.mysql.db.commit()


    # Returns an object containing basic information on a certain tournament on Toornament.
    # Either a toornament ID, or both a guildID and name must be given.
    # tournamentID: Toornament ID of the tournament
    # guildID: ID of the Discord guild the tournament is hosted in
    # name: Name of the tournament used on Discord or Toornament
    def getTournamentInfo(self, tournamentID = None, guildID = None, name = None) -> TournamentInfo:
        # Returns information for given tournament id
        if tournamentID is not None:
            self.mysql.query("SELECT GuildID, Name FROM Tournaments WHERE TournamentID=%s;", (tournamentID,))
            results = self.mysql.fetchResults()

            if results is None:
                raise Exception(f"Tournament '{tournamentID}' couldn't be found")
            else:
                guildID = results[0][0]
                name = results[0][1]
                return TournamentInfo(name, guildID, tournamentID)

        # Returns information for given guild id and tournament name
        elif guildID is not None and name is not None:
            self.mysql.query("SELECT TournamentID FROM Tournaments WHERE Name=%s AND GuildID=%s;", (name, guildID,))
            results = self.mysql.fetchResults()

            if results is None:
                raise Exception(f"No tournament '{name}' could be found for guild {guildID}")
            else:
                tournamentID = results[0][0]
                return TournamentInfo(name, guildID, tournamentID)
        
        # Invalid input
        else:
            raise ValueError("Either a tournament ID, or a tournament name and guild ID must be supplied")


    # Adds a tournament from toornament to a discord guild.
    # tournamentID: Toornament ID of the tournament
    # guildID: ID of the Discord guild the tournament is hosted in
    # name: Name of the tournament used on Discord or Toornament
    def addTournament(self, tournamentID, guildID, name = None):
        if name is None:
            self.mysql.query("INSERT INTO Tournaments (TournamentID, GuildID) VALUES (%s, %s);", (tournamentID, guildID,))
        else:
            self.mysql.query("INSERT INTO Tournaments (TournamentID, GuildID, Name) VALUES (%s, %s, %s);", (tournamentID, guildID, name,))
        self.mysql.db.commit()
