# This class is a wrapper for MySQL-database operations.
# Its main purpose it to automatically renew the database connection if it expired.
# Additionally it provides various helper methods to simply recurring operations.

from authorization import AuthorizationInfo
import MySQLdb

class MySQLWrapper:

    # Constructor
    # Initiates a database connection using the provided authorization information
    # authorization: Authorization info object
    def __init__(self, authorization: AuthorizationInfo):
        self.auth = authorization
        self.__connectToDatabase()

    # Tries to connect to the database using the saved authorization information
    def __connectToDatabase(self):
        self.db = MySQLdb.connect(
            host = self.auth.mysqlIP,
            user = self.auth.mysqlUser,
            passwd = self.auth.mysqlPassword,
            db = self.auth.mysqlDatabase
        )

        self.cursor = self.db.cursor()

    # Tries to execute a given operation. Restarts the database connection if it timed out.
    # operation: SQL-command to be executed
    # params: Parameters to be sanitized and inserted into the SQL-command
    def query(self, operation: str, params = None):
        try:
            self.cursor.execute(operation, params)

        except MySQLdb.OperationalError as opErr:
            # Checks for error 2006: "MySQL database has gone away"
            if opErr.errno == 2006:
                self.__connectToDatabase()
                self.cursor.execute(operation, params)

            # Raises other kinds of errors
            else:
                raise opErr

    # Returns the results of the last query. If they are invalid, None is returned.
    def fetchResults(self):
        results = self.cursor.fetchall()

        if results is not None and results[0][0] is None:
            return None
        else:
            return results

    # Returns True if a table with the given name exists in the selected database.
    # name: The name of the table to be checked for
    def doesTableExist(self, name: str) -> bool:
        self.cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name=%s LIMIT 1;", (self.auth.mysqlDatabase, name,))
        result = self.cursor.fetchall()
        return result[0][0] > 0

    # Creates a new table.
    # name: The name of the table to be created
    # columns: The SQL string providing the names of all columns to be created
    def createTable(self, name: str, columns: str, overwrite: bool = False):

        # Checks if table exists, if overwrite is True deletes it, otherwise leaves method
        if self.doesTableExist(name):
            if overwrite:
                self.cursor.execute(f"DROP TABLE %s;", (name,))
            else:
                return

        # Creates new table
        self.cursor.execute(f"CREATE TABLE {name} ({columns});", ())
