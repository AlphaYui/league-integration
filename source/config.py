# The class BotConfig is a wrapper for a configuration database table.
# It offers methods to retrieve configuration values by name or through more dedicated wrapper methods.
# To convert the results to the needed types, an instance of the DiscordHelper class is needed

from mysqlwrapper import MySQLWrapper
from discordhelper import DiscordHelper
from utility import tryToInt

class BotConfig:

    # Constructor:
    # discordHelper: DiscordHelper instance
    # mysqlWrapper: MySQLWrapper instance
    # overwrite: If True, the configuration table will be with startup
    def __init__(self, discordHelper: DiscordHelper, mysqlWrapper: MySQLWrapper, overwrite: bool = False):
        self.discordHelper = discordHelper
        self.mysql = mysqlWrapper
        self.__initConfigTable(overwrite)

    # Creates the required MySQL configuration table.
    # overwrite: If True, the config table will be dropped and overwritten if it already exists
    def __initConfigTable(self, overwrite: bool = False):
        self.mysql.createTable("BotConfig", (
            "ConfigID INT AUTO_INCREMENT, "
            "TournamentID BIGINT NOT NULL, "
            "Name VARCHAR(63) NOT NULL, "
            "Value VARCHAR(1023), "
            "PRIMARY KEY(ConfigID)"
        ), overwrite = overwrite)

    # Returns a map containing the default configuration.
    # Used to initialize new tournament configurations.
    @staticmethod
    def __getDefaultValues():
        return {
            "team_role_template": "716961342069669909"
        }
    
    # Adds a default configuration for a tournament.
    # tournamentID: Toornament ID of the tournament to create default config for
    def createDefaultConfig(self, tournamentID):
        defaultValues = BotConfig.__getDefaultValues()

        for configName in defaultValues:
            self.addValue(tournamentID, configName, defaultValues[configName])

    # Adds a new configuration value for the given tournament.
    # tournamentID: Toornament ID of the tournament to add a configuration for
    # name: Name of the new configuration attribute
    # value: Value of the new configuration attribute
    def addValue(self, tournamentID, name, value = None):
        if value is None:
            self.mysql.query("INSERT INTO BotConfig (TournamentID, Name) VALUES (%s, %s);", (tournamentID, name,))
        else:
            self.mysql.query("INSERT INTO BotConfig (TournamentID, Name, Value) VALUES (%s, %s, %s);", (tournamentID, name, value,))

        self.mysql.db.commit()

    # Returns the value of a configuration attribute for the given tournament.
    # tournamentID: Toornament ID of the tournament to get the configuration value for
    # name: Name of the configuration attribute to retrieve
    def getValue(self, tournamentID, name):
        self.mysql.query("SELECT Value FROM BotConfig WHERE TournamentID=%s AND Name=%s;", (tournamentID, name,))
        results = self.mysql.fetchResults()

        if results is None:
            return None
        else:
            return results[0][0]

    # Updates the value of a configuration attribute for the given tournament.
    # tournamentID: Toornament ID of the toornament to update the configuration value for.
    # name: Name of the configuration attribute to update
    # value: New value of the configuration attribute
    def setValue(self, tournamentID, name, value):
        self.mysql.query("UPDATE BotConfig SET Value=%s WHERE TournamentID=%s AND Name=%s;", (value, tournamentID, name,))
        self.mysql.db.commit()

    # Returns the team role template as a Discord role object for the given tournament.
    # tournamentID: Toornament ID of the tournament to get the team role template for.
    def getTeamRoleTemplate(self, tournamentID):
        templateRoleID = tryToInt(self.getValue(tournamentID, "team_role_template"))
        templateRole = self.discordHelper.getRole(tournamentID, templateRoleID)

        if templateRole is None:
            raise ValueError(f"Team template role '{templateRoleID}' doesn't exist or is not configured correctly")
        else:
            return templateRole
        