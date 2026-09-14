import sqlite3
#conn = sqlite3.connect('nea.db')
#cursor = conn.cursor()

#cursor.execute('PRAGMA foreign_keys = ON')

def dropTable(cursor, conn, tableName): #checked
    cursor.execute('DROP TABLE IF EXISTS {}'.format(tableName))
    conn.commit()

#organisations table and related subroutines:

def createOrgTable(cursor, conn): #checked
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS Organisations (
                OrgID INTEGER PRIMARY KEY AUTOINCREMENT, 
                Name STRING, 
                Location STRING, 
                Manager STRING,
                Email STRING,
                Password STRING
                );
                ''')
    conn.commit()

def updateOrgName(cursor, conn, newName, orgID):
    cursor.execute('''
                UPDATE Organisations
                SET Name = ?
                WHERE OrgID = ?
                    ''', (newName, orgID))
    conn.commit()

def updateOrgLocation(cursor, conn, newLocation, orgID):
    cursor.execute('''
                UPDATE Organisations
                SET Location = ?
                WHERE OrgID = ?
                    ''', (newLocation, orgID))
    conn.commit()

def updateOrgManager(cursor, conn, newManager, orgID):
    cursor.execute('''
                UPDATE Organisations
                SET Manager = ?
                WHERE OrgID = ?
                    ''', (newManager, orgID))
    conn.commit()

def updateOrgEmail(cursor, conn, newEmail, orgID):
    cursor.execute('''
                UPDATE Organisations
                SET Email = ?
                WHERE OrgID = ?
                    ''', (newEmail, orgID))
    conn.commit()

def updateOrgPassword(cursor, conn, newPassword, orgID):
    cursor.execute('''
                UPDATE Organisations
                SET Password = ?
                WHERE OrgID = ?
                    ''', (newPassword, orgID))
    conn.commit()

def getOrganisations(cursor, conn): #checked
    cursor.execute('SELECT OrgID, Name FROM Organisations')
    response = cursor.fetchall() 
    return response


def getOrganisationsDetails(cursor, conn): 
    cursor.execute('SELECT * FROM Organisations')
    response = cursor.fetchall() 
    return response

def checkNameInOrganisations(cursor, conn, orgName): #checked
    cursor.execute('SELECT COUNT(*) FROM Organisations WHERE Name = ?',(orgName,)) 
    return cursor.fetchone()[0]

def checkIDInOrganisations(cursor, conn, orgID): #checked
    cursor.execute('SELECT COUNT(*) FROM Organisations WHERE OrgID = {}'.format(orgID)) 
    return cursor.fetchone()[0]

def tryLogInOrg(cursor, conn, orgID, email, password): #checked
    cursor.execute('SELECT Password FROM Organisations WHERE OrgID = {} AND Email = ?'.format(orgID), (email,))
    truePassword = cursor.fetchone()
    if truePassword != None:
        if truePassword[0] == password:
            return True
        else: 
            return False
    else:
        return False

def insertOrg(cursor, conn, orgName, orgLocation, orgManager, orgEmail, orgPassword):
    cursor.execute('''
                INSERT INTO Organisations (Name, Location, Manager, Email, Password) 
                VALUES (?, ?, ?, ?, ?)
                ''', (orgName, orgLocation, orgManager, orgEmail, orgPassword))
    org_id = cursor.lastrowid
    conn.commit()
    return org_id

def updateOrg(cursor, conn):
    cursor.execute('''
                UPDATE Organisations
                SET OrgID = 1
                WHERE OrgID = 7
                    ''')
    conn.commit()

def OrgUpdatePassword(cursor, conn, orgID, newPassword):
    cursor.execute('''
                UPDATE Organisations
                SET Password = ?
                WHERE OrgID = {}
                   '''.format(orgID), (newPassword,))
    conn.commit()
    

#coaches table and related subroutines:
    
def createCoachesTable(cursor, conn):
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS Coaches (
                CoachID INTEGER PRIMARY KEY AUTOINCREMENT,
                OrgID INTEGER, 
                Name STRING,
                Email STRING,
                Password STRING, 
                FOREIGN KEY (OrgID) REFERENCES Organisations(OrgID)
                )
                    ''')
    conn.commit()

def initialGetAllCoaches(cursor, conn):
    cursor.execute('SELECT * FROM Coaches')
    return cursor.fetchall()

def insertCoach(cursor, conn, orgID, coachName, coachEmail, coachPassword):
    cursor.execute('''
                INSERT INTO Coaches (OrgID, Name, Email, Password) 
                VALUES (?, ?, ?, ?)
                ''', (orgID, coachName, coachEmail, coachPassword))
    coach_id = cursor.lastrowid
    conn.commit()
    return coach_id

def updateCoachName(cursor, conn, newName, coachID):
    cursor.execute('''
                UPDATE Coaches
                SET Name = ?
                WHERE CoachID = ?
                    ''', (newName, coachID))
    conn.commit()

def updateCoachEmail(cursor, conn, newEmail, coachID):
    cursor.execute('''
                UPDATE Coaches
                SET Email = ?
                WHERE CoachID = ?
                    ''', (newEmail, coachID))
    conn.commit()

def updateCoachPassword(cursor, conn, newPassword, coachID):
    cursor.execute('''
                UPDATE Coaches
                SET Password = ?
                WHERE CoachID = ?
                    ''', (newPassword, coachID))
    conn.commit()

def tryLogInCoach(cursor, conn, orgID, email, password):
    cursor.execute('SELECT Password FROM Coaches WHERE OrgID = {} AND Email = ?'.format(orgID), (email,))
    truePassword = cursor.fetchone()
    if truePassword != None:
        if truePassword[0] == password:
            return True
        else: 
            return False
    else:
        return False
    
def getCoachID(cursor, conn, orgID, email):
    cursor.execute('SELECT CoachID FROM Coaches WHERE OrgID = {} AND Email = ?'.format(orgID), (email,))
    coachID = cursor.fetchone()
    return coachID
    
def getAllCoaches(cursor, conn, orgID):
    cursor.execute('''
                   SELECT Coaches.CoachID, Coaches.Name, Teams.Name
                   FROM Coaches 
                   LEFT JOIN Teams on Coaches.CoachID = Teams.CoachID
                   WHERE Coaches.OrgID = {}'''.format(orgID))
    response = cursor.fetchall()
    conn.commit()
    return response


#teams table and related subroutines:

def createTeamsTable(cursor, conn):
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Teams (
                    TeamID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name STRING,
                    OrgID INTEGER, 
                    CoachID INTEGER, 
                    PrivacyMode BOOLEAN,
                    FOREIGN KEY (OrgID) REFERENCES Organisations(OrgID),
                    FOREIGN KEY (CoachID) REFERENCES Coaches(CoachID)
                    )
                        ''')
    conn.commit()


def initialGetAllTeams(cursor, conn):
    cursor.execute('SELECT TeamID, OrgID, Name, CoachID, PrivacyMode FROM Teams')
    return cursor.fetchall()

def insertTeam(cursor, conn, orgID, teamName, coachID, privacyMode): #checked
    try:
        cursor.execute('''
                    INSERT INTO Teams (OrgID, Name, CoachID, PrivacyMode) 
                    VALUES (?, ?, ?, ?)
                    ''', (orgID, teamName, coachID, privacyMode))
        team_id = cursor.lastrowid
        conn.commit()
        return team_id
    except Exception as e:
        print('Insert team error: ', e)
        return None
    
def updateTeamName(cursor, conn, newName, teamID):
    cursor.execute('''
                UPDATE Teams
                SET Name = ?
                WHERE TeamID = ?
                    ''', (newName, teamID))
    conn.commit()

def updateTeamCoach(cursor, conn, newCoachID, teamID):
    cursor.execute('''
                UPDATE Teams
                SET CoachID = ?
                WHERE TeamID = ?
                    ''', (newCoachID, teamID))
    conn.commit()

def updateTeamPrivacyMode(cursor, conn, privacyMode, teamID):
    cursor.execute('''
                UPDATE Teams
                SET PrivacyMode = ?
                WHERE TeamID = ?
                    ''', (privacyMode, teamID))
    conn.commit()

def getTeamsInOrg(cursor, conn, orgID, teamID):
    cursor.execute('''
                SELECT TeamID, Name
                FROM Teams
                WHERE OrgID = ? AND TeamID != ?
                ''', (orgID, teamID))
    response = cursor.fetchall()
    return response


def createCoachTeamLinkTable(cursor, conn):
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS CoachTeamLink (
                    CoachID INTEGER,
                    TeamID INTEGER, 
                    PRIMARY KEY (CoachID, TeamID),
                    FOREIGN KEY (CoachID) REFERENCES Coaches(CoachID),
                    FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
                    )
                        ''')
    conn.commit()

def addCoachToTeam(cursor, conn, coachID, teamID):
    cursor.execute('''
                INSERT INTO CoachTeamLink  
                VALUES (?, ?)
                ''', (coachID, teamID))
    conn.commit()

def removeCoachFromTeam(cursor, conn, coachID, teamID):
    cursor.execute('''
                DELETE FROM CoachTeamLink
                WHERE CoachID = ? and TeamID = ?
                ''', (coachID, teamID))
    conn.commit()

def getAllTeamsCoach(cursor, conn, coachID):
    cursor.execute('''
                SELECT CoachTeamLink.TeamID, Teams.Name
                FROM CoachTeamLink 
                JOIN Teams on CoachTeamLink.TeamID = Teams.TeamID
                WHERE CoachTeamLink.CoachID = ?''', (coachID,))
    response = cursor.fetchall()
    return response

def getAllMainTeamsCoach(cursor, conn, coachID):
    cursor.execute('''
                SELECT TeamID, Name
                FROM Teams
                WHERE CoachID = ?''', (coachID,))
    response = cursor.fetchall()
    return response

#players table and related subroutines:

def createPlayersTable(cursor, conn):
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Players (
                    PlayerID INTEGER PRIMARY KEY AUTOINCREMENT,
                    OrgID INTEGER, 
                    Name STRING, 
                    Number INTEGER,
                    Email STRING,
                    Password STRING,
                    FOREIGN KEY (OrgID) REFERENCES Organisations(OrgID)
                    )
                        ''')
    conn.commit()

def initialGetAllPlayers(cursor, conn):
    cursor.execute('SELECT * FROM Players')
    return cursor.fetchall()

def updatePlayerName(cursor, conn, newName, playerID):
    cursor.execute('''
                UPDATE Players
                SET Name = ?
                WHERE PlayerID = ?
                    ''', (newName, playerID))
    conn.commit()
    
def updatePlayerNumber(cursor, conn, newNumber, playerID):
    cursor.execute('''
                UPDATE Players
                SET Number = ?
                WHERE PlayerID = ?
                    ''', (newNumber, playerID))
    conn.commit()

def updatePlayerEmail(cursor, conn, newEmail, playerID):
    cursor.execute('''
                UPDATE Players
                SET Email = ?
                WHERE PlayerID = ?
                    ''', (newEmail, playerID))
    conn.commit()

def updatePlayerPassword(cursor, conn, newPassword, playerID):
    cursor.execute('''
                UPDATE Players
                SET Password = ?
                WHERE PlayerID = ?
                    ''', (newPassword, playerID))
    conn.commit()

def checkPlayerNumber(cursor, conn, number):
    cursor.execute('SELECT COUNT (*) FROM Players WHERE Number = ?', (number,))
    return cursor.fetchone()[0]

def insertPlayer(cursor, conn, OrgID, playerName, playerNumber, playerEmail, playerPassword):
    cursor.execute('''
                INSERT INTO Players (OrgID, Name, Number, Email, Password) 
                VALUES (?, ?, ?, ?, ?)
                ''', (OrgID, playerName, playerNumber, playerEmail, playerPassword))
    player_id = cursor.lastrowid
    conn.commit()
    return player_id

def getAllPlayers(cursor, conn, orgID):
    cursor.execute('SELECT PlayerID, Number, Name FROM Players WHERE OrgID = {}'.format(orgID))
    response = cursor.fetchall()
    return response

def tryLogInPlayer(cursor, conn, orgID, email, password):
    cursor.execute('SELECT Password FROM Players WHERE OrgID = {} AND Email = ?'.format(orgID), (email,))
    truePassword = cursor.fetchone()
    if truePassword != None:
        if truePassword[0] == password:
            return True
        else: 
            return False
    else:
        return False
    
def getPlayerID(cursor, conn, orgID, email):
    cursor.execute('SELECT PlayerID FROM Players WHERE OrgID = {} AND Email = ?'.format(orgID), (email,))
    playerID = cursor.fetchone()
    return playerID


def createPlayerTeamLinkTable(cursor, conn):
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS PlayerTeamLink (
                    PlayerID INTEGER,
                    TeamID INTEGER, 
                    PRIMARY KEY (PlayerID, TeamID),
                    FOREIGN KEY (PlayerID) REFERENCES Players(PlayerID),
                    FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
                    )
                        ''')
    conn.commit()

def addPlayerToTeam(cursor, conn, playerID, teamID):
    cursor.execute('''
                INSERT INTO PlayerTeamLink  
                VALUES (?, ?)
                ''', (playerID, teamID))
    conn.commit()

def removePlayerFromTeam(cursor, conn, playerID, teamID):
    cursor.execute('''
                DELETE FROM PlayerTeamLink
                WHERE PlayerID = ? and TeamID = ?
                ''', (playerID, teamID))
    conn.commit()

def getAllPlayersTeam(cursor, conn, teamID):
    cursor.execute('''
                SELECT PlayerTeamLink.PlayerID, Players.Number, Players.Name
                FROM PlayerTeamLink 
                JOIN Players on PlayerTeamLink.PlayerID = Players.PlayerID
                WHERE PlayerTeamLink.TeamID = ?''', (teamID,))
    response = cursor.fetchall()
    return response

def getAllTeamsPlayer(cursor, conn, playerID):
    cursor.execute('''
                SELECT PlayerTeamLink.TeamID, Teams.Name
                FROM PlayerTeamLink 
                JOIN Teams on PlayerTeamLink.TeamID = Teams.TeamID
                WHERE PlayerTeamLink.PlayerID = ?''', (playerID,))
    response = cursor.fetchall()
    return response


#matches table and related subroutines:

def createMatchesTable(cursor, conn):
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Matches (
                    MatchID INTEGER PRIMARY KEY AUTOINCREMENT, 
                    OrgID INTEGER,
                    TeamID INTEGER,
                    OpponentID INTEGER, 
                    GoalsScored INTEGER,
                    GoalsConceded INTEGER,
                    Date DATE, 
                    Location STRING,
                    Formation STRING, 
                    FOREIGN KEY (OpponentID) REFERENCES Teams(TeamID)
                    FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
                    FOREIGN KEY (OrgID) REFERENCES Organisations(OrgID)
                    )
                        ''')
    conn.commit()
    
def updateMatchTeam(cursor, conn, newTeamID, matchID):
    cursor.execute('''
                UPDATE Matches
                SET TeamID = ?
                WHERE MatchID = ?
                    ''', (newTeamID, matchID))
    conn.commit()

def updateMatchOpponent(cursor, conn, newOpponentID, matchID):
    cursor.execute('''
                UPDATE Matches
                SET OpponentID = ?
                WHERE MatchID = ?
                    ''', (newOpponentID, matchID))
    conn.commit()

def updateMatchDate(cursor, conn, newDate, matchID):
    cursor.execute('''
                UPDATE Matches
                SET Date = ?
                WHERE MatchID = ?
                    ''', (newDate, matchID))
    conn.commit()

def updateMatchLocation(cursor, conn, newLocation, matchID):
    cursor.execute('''
                UPDATE Matches
                SET Location = ?
                WHERE MatchID = ?
                    ''', (newLocation, matchID))
    conn.commit()


def insertMatch(cursor, conn, orgID, teamID, opponentID, goalsScored, goalsConceded, matchDate, matchLocation, formation):
    cursor.execute('''
                INSERT INTO Matches (OrgID, TeamID, OpponentID, GoalsScored, GoalsConceded, Date, Location, Formation) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (orgID, teamID, opponentID, goalsScored, goalsConceded, matchDate, matchLocation, formation))
    match_id = cursor.lastrowid
    conn.commit()
    return match_id

def removeMatch(cursor, conn, matchID):
    cursor.execute(''' 
                DELETE FROM Matches
                WHERE MatchID = ?
                ''', (matchID,))
    conn.commit()

def addScore(cursor, conn, matchID, goalsScored, goalsConceded):
    cursor.execute('''
                UPDATE Matches
                SET GoalsScored = ?, GoalsConceded = ?
                WHERE MatchID = ?
                   ''', (goalsScored, goalsConceded, matchID))
    conn.commit()
    
def addFormation(cursor, conn, matchID, formation):
    cursor.execute('''
                UPDATE Matches
                SET Formation = ?
                WHERE MatchID = ?
                    ''', (formation, matchID))
    conn.commit()
    
def getFormation(cursor, conn, orgID, teamID, opponentID, date):
    cursor.execute('''
                SELECT Formation FROM Matches
                WHERE OrgID = ? AND TeamID = ? AND OpponentID = ? and Date = ?
                    ''', (orgID, teamID, opponentID, date))
    response = cursor.fetchone()
    return response

def getFormationOfLastMatch(cursor, conn, orgID, teamID):
    cursor.execute('''
                    SELECT Formation FROM Matches
                    WHERE OrgID = ? AND TeamID = ? 
                    ORDER BY Date DESC LIMIT 1
                        ''', (orgID, teamID))
    response = cursor.fetchone()
    return response

def getTeamResults(cursor, conn, orgID, teamID, seasonStartDate):
    cursor.execute('''
                    SELECT COUNT(*) FROM Matches
                    WHERE OrgID = ? AND TeamID = ? AND Date >= ? AND GoalsScored > GoalsConceded
                   ''', (orgID, teamID, seasonStartDate))
    wins = cursor.fetchone()
    cursor.execute('''
                    SELECT COUNT(*) FROM Matches
                    WHERE OrgID = ? AND TeamID = ? AND Date >= ? AND GoalsScored = GoalsConceded
                   ''', (orgID, teamID, seasonStartDate))
    draws = cursor.fetchone()
    cursor.execute('''
                    SELECT COUNT(*) FROM Matches
                    WHERE OrgID = ? AND TeamID = ? AND Date >= ? 
                   ''', (orgID, teamID, seasonStartDate))
    totalMatches = cursor.fetchone()
    if totalMatches[0] == 0:
        return 0
    else:
        return (wins[0]*3 + draws[0])/totalMatches[0]

def getMatch(cursor, conn, matchID):
    cursor.execute('''
                SELECT T1.Name, T2.Name, Matches.Date, Matches.Location, Matches.GoalsScored, Matches.GoalsConceded, Matches.MatchID
                FROM Matches
                JOIN Teams T1 ON Matches.TeamID = T1.TeamID
                JOIN Teams T2 ON Matches.OpponentID = T2.TeamID
                WHERE Matches.MatchID = ? 
                ''', (matchID,))
    response = cursor.fetchone()
    return response

def getAllTeamMatches(cursor, conn, teamID, seasonStartDate):
    cursor.execute('''
                SELECT T1.Name, T2.Name, Matches.Date, Matches.Location, Matches.GoalsScored, Matches.GoalsConceded, Matches.MatchID
                FROM Matches
                JOIN Teams T1 ON Matches.TeamID = T1.TeamID
                JOIN Teams T2 ON Matches.OpponentID = T2.TeamID
                WHERE Matches.TeamID = ? AND Matches.Date >= ?
                ORDER BY Matches.Date DESC
                    ''', (teamID, seasonStartDate))
    response = cursor.fetchall()
    return response



#formations tables and related subroutines:

def createFormationsTable(cursor, conn, tableName):
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS {} (
                    FormationID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Formation STRING,
                    Defensive INTEGER,
                    Offensive INTEGER
                    )
                        '''.format(tableName))
    conn.commit()

def insertFormation(cursor, conn, tableName, formationName, defensive, offensive):
    query = 'INSERT INTO {} (Formation, Defensive, Offensive) VALUES (?, ?, ?)'.format(tableName)
    cursor.execute(query, (formationName, defensive, offensive))
    conn.commit()

def getAllFormations(cursor, conn, tableName):
    query = 'SELECT * FROM {}'.format(tableName)
    cursor.execute(query)
    response = cursor.fetchall()
    return response

def updateFormation(cursor, conn, tableName, formationName, newDefensive, newOffensive):
    query1 = 'SELECT Defensive From {} WHERE Formation = ?'.format(tableName)
    cursor.execute(query1, (formationName,))
    oldDefensive = cursor.fetchone()[0]
    updateDeff = (oldDefensive + newDefensive)/2
    query2 = 'SELECT Offensive From {} WHERE Formation = ?'.format(tableName)
    cursor.execute(query2, (formationName,))
    oldOffensive = cursor.fetchone()[0]
    updateOff = (oldOffensive  + newOffensive)/2
    query3 = '''
                UPDATE {} 
                SET Offensive = ? , Defensive = ?
                WHERE Formation = ?
                '''.format(tableName)
    cursor.execute(query3, (updateOff, updateDeff, formationName))
    conn.commit()

def getFormationSplit(cursor, conn, formationName, teamNum):
    tableName = 'Formations{}side'.format(teamNum)
    cursor.execute('SELECT Defensive, Offensive FROM {} WHERE Formation = ?'.format(tableName) ,(formationName,))
    response = cursor.fetchone()
    return response

def checkIfInFormations(cursor, conn, formationName, teamNum):
    tableName = 'Formations{}side'.format(teamNum)
    cursor.execute('SELECT COUNT(*) FROM {} WHERE Formation = ?'.format(tableName), (formationName,))
    response = cursor.fetchone()[0]
    return response

def createPositionTable(cursor, conn, positionName):
    tableName = '{}table'.format(positionName)
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS {} (
                    PlayerID INTEGER,
                    TeamID INTEGER,
                    Rank INTEGER,
                    PRIMARY KEY (PlayerID, TeamID),
                    FOREIGN KEY (PlayerID) REFERENCES Players(PlayerID)
                    FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
                    )
                        '''.format(tableName))
    conn.commit()    

def initialGetAllPositions(cursor, conn, positionName, teamID):
    tableName = '{}table'.format(positionName)
    cursor.execute('SELECT PlayerID, Rank FROM {} WHERE TeamID = ?'.format(tableName), (teamID,))
    return cursor.fetchall()

def addPlayerPosition(cursor, conn, positionName, playerID, teamID, rank):
    tableName = '{}table'.format(positionName)
    cursor.execute('''
                INSERT INTO {}
                VALUES (?, ?, ?)
                '''.format(tableName), (playerID, teamID, rank))
    conn.commit()

def removePlayerPosition(cursor, conn, positionName, playerID, teamID):
    tableName = '{}table'.format(positionName)
    cursor.execute('''
                DELETE FROM {}
                WHERE PlayerID = ? AND TeamID = ?
                '''.format(tableName), (playerID, teamID))
    conn.commit()


#conn.commit()

#conn.close()