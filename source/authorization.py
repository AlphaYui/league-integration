# This class manages the information required for application authorization
# like e.g. API-tokens, login details, ...
#
# Example JSON-file:
# {
#     "Discord": {
#         "Token": "...",
#         "ClientID": "...",
#         "ClientSecret": "..."
#     },
#     "Toornament": {
#         "Token": "...",
#         "ClientID": "...",
#         "ClientSecret": "...",
#         "AuthKey": "...",
#         "AuthType": "...",
#         "AuthExpiryDate": "31.05.2020, 14:24:46"
#     },
#     "MySQL": {
#         "IP": "...",
#         "User": "...",
#         "Password": "...",
#         "Database": "..."
#     },
#     "Ballchasing": {
#         "Token": "..."
#     }
# }

import json
import datetime

class AuthorizationInfo:

    # Constructor
    # Loads authorization data from given JSON-file, or uses default values if none is given
    # path: Path of the JSON-file containing the authorization information
    def __init__(self, path = None): 
        if path is None:
            self.__initDefaults()
        else:
            self.loadFromJSON(path)

    # Sets all authorization data to default values
    def __initDefaults(self):
        self.discordToken = ""
        self.discordClientID = ""
        self.discordClientSecret = ""

        self.toornamentToken = ""
        self.toornamentClientID = ""
        self.toornamentClientSecret = ""
        self.toornamentAuthKey = ""
        self.toornamentAuthType = ""
        self.toornamentAuthExpiry = datetime.datetime.now()

        self.mysqlIP = ""
        self.mysqlUser = ""
        self.mysqlPassword = ""
        self.mysqlDatabase = ""

        self.ballchasingToken = ""

        self.authPath = None

    # Loads authorization data from a given JSON-file. An example file is in the documentation at the top of this file's documentation
    # path: Path of the JSON-file to be loaded
    def loadFromJSON(self, path):
        with open(path, "r") as f:
            authJSON = json.loads(f.read())

            discordJSON = authJSON["Discord"]
            self.discordToken = discordJSON["Token"]
            self.discordClientID = discordJSON["ClientID"]
            self.discordClientSecret = discordJSON["ClientSecret"]

            toornamentJSON = authJSON["Toornament"]
            self.toornamentToken = toornamentJSON["Token"]
            self.toornamentClientID = toornamentJSON["ClientID"]
            self.toornamentClientSecret = toornamentJSON["ClientSecret"]
            self.toornamentAuthKey = toornamentJSON["AuthKey"]
            self.toornamentAuthType = toornamentJSON["AuthType"]
            self.toornamentAuthExpiry = datetime.datetime.strptime(toornamentJSON["AuthExpiryDate"], "%d.%m.%Y, %H:%M:%S")

            mysqlJSON = authJSON["MySQL"]
            self.mysqlIP = mysqlJSON["IP"]
            self.mysqlUser = mysqlJSON["User"]
            self.mysqlPassword = mysqlJSON["Password"]
            self.mysqlDatabase = mysqlJSON["Database"]

            ballchasingJSON = authJSON["Ballchasing"]
            self.ballchasingToken = ballchasingJSON["Token"]

            self.authPath = path

    # Saves authorization Datei to a given JSON-file.
    # path: Path of the JSON-file to which the data should be saved
    def saveToJSON(self, path):
        authJSON = {
                "Discord": {
                    "Token": self.discordToken,
                    "ClientID": self.discordClientID,
                    "ClientSecret": self.discordClientSecret
                },
                "Toornament": {
                    "Token": self.toornamentToken,
                    "ClientID": self.toornamentClientID,
                    "ClientSecret": self.toornamentClientSecret,
                    "AuthKey": self.toornamentAuthKey,
                    "AuthType": self.toornamentAuthType,
                    "AuthExpiryDate": self.toornamentAuthExpiry.strftime("%d.%m.%Y, %H:%M:%S")
                },
                "MySQL": {
                    "IP": self.mysqlIP,
                    "User": self.mysqlUser,
                    "Password": self.mysqlPassword,
                    "Database": self.mysqlDatabase
                },
                "Ballchasing": {
                    "Token": self.ballchasingToken
                }
            }

        with open(path, "w") as f:
            json.dump(authJSON, f, ensure_ascii=True, indent=4)

    # Returns true if the toornament authorization key expired
    def hasToornamentAuthExpired(self) -> bool:
        # Adds 1 minute to current time to avoid key expiry mid-operation
        # (e.g. this method returns False but 10ms later the token expires before the API call is made)
        if datetime.datetime.now() + datetime.timedelta(minutes = 1) > self.toornamentAuthExpiry:
            return True
        else:
            return False

    # Saves a new toornament OAuth2 key.
    # Tries to overwrite the authorization info JSON-file if it was loaded from one originally.
    # newKeyJSON: Information on the new authorization token as received from the OAuth2 endpoint
    def replaceToornamentAuthKey(self, newKeyJSON):

        newAccessToken = newKeyJSON['access_token']
        expiresInSeconds = newKeyJSON['expires_in']
        newTokenType = newKeyJSON['token_type']
        newTokenScope = newKeyJSON['scope']

        self.toornamentAuthKey = newAccessToken
        self.toornamentAuthType = newTokenType
        self.toornamentAuthExpiry = datetime.datetime.now() + datetime.timedelta(seconds = expiresInSeconds)

        if self.authPath is not None:
            self.saveToJSON(self.authPath)
