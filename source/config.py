from mysqlwrapper import MySQLWrapper
from discordhelper import DiscordHelper
from utility import tryToInt

class BotConfig:

    def __init__(self, discordHelper: DiscordHelper, mysqlWrapper: MySQLWrapper, overwrite: bool = False):
        self.discordHelper = discordHelper
        self.mysql = mysqlWrapper
        self.__initConfigTable(overwrite)

    def __initConfigTable(self, overwrite: bool = False):
        self.mysql.createTable("BotConfig", (
            "ConfigID INT AUTO_INCREMENT, "
            "TournamentID BIGINT NOT NULL, "
            "Name VARCHAR(63) NOT NULL, "
            "Value VARCHAR(1023), "
            "PRIMARY KEY(ConfigID)"
        ), overwrite = overwrite)

    @staticmethod
    def __getDefaultValues():
        return [
            ("team_role_template", "716961342069669909")
        ]
    
    def createDefaultConfig(self, tournamentID):
        defaultValues = BotConfig.__getDefaultValues()

        for (configName, defaultValue) in defaultValues:
            self.addValue(tournamentID, configName, defaultValue)

    def addValue(self, tournamentID, name, value = None):
        if value is None:
            self.mysql.query("INSERT INTO BotConfig (TournamentID, Name) VALUES (%s, %s);", (tournamentID, name,))
        else:
            self.mysql.query("INSERT INTO BotConfig (TournamentID, Name, Value) VALUES (%s, %s, %s);", (tournamentID, name, value,))

        self.mysql.db.commit()

    def getValue(self, tournamentID, name):
        self.mysql.query("SELECT Value FROM BotConfig WHERE TournamentID=%s AND Name=%s;", (tournamentID, name,))
        results = self.mysql.fetchResults()

        if results is None:
            return None
        else:
            return results[0][0]

    def setValue(self, tournamentID, name, value):
        self.mysql.query("UPDATE BotConfig SET Value=%s WHERE TournamentID=%s AND Name=%s;", (value, tournamentID, name,))
        self.mysql.db.commit()


    def getTeamRoleTemplate(self, tournamentID):
        templateRoleID = tryToInt(self.getValue(tournamentID, "team_role_template"))
        templateRole = self.discordHelper.getRole(tournamentID, templateRoleID)

        if templateRole is None:
            raise ValueError(f"Team template role '{templateRoleID}' doesn't exist or is not configured correctly")
        else:
            return templateRole
        