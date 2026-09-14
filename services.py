"""
Service layer. Every function here is stateless (reads/writes SQLite directly)
so it works cleanly with Streamlit's rerun-the-whole-script model. This
replaces the Org/Coach/Player/Team/Match classes from nea_oop.py, which held
state in memory and used input() inside constructors/methods.
"""
import random
from datetime import date
import sql
import logic
from db import cur_conn, hash_password

DEFAULT_PASSWORD = 'Password123'


# ---------- Auth / registration ----------

def register_org(name, location, manager_name, email, password):
    cursor, conn = cur_conn()
    if sql.checkNameInOrganisations(cursor, conn, name) > 0:
        return None, 'A school/club with that name is already registered.'
    org_id = sql.insertOrg(cursor, conn, name, location, manager_name, email, hash_password(password))
    return org_id, None


def get_organisations():
    cursor, conn = cur_conn()
    return sql.getOrganisations(cursor, conn)


def login_org(org_id, email, password):
    cursor, conn = cur_conn()
    return sql.tryLogInOrg(cursor, conn, org_id, email, hash_password(password))


def login_coach(org_id, email, password):
    cursor, conn = cur_conn()
    return sql.tryLogInCoach(cursor, conn, org_id, email, hash_password(password))


def login_player(org_id, email, password):
    cursor, conn = cur_conn()
    return sql.tryLogInPlayer(cursor, conn, org_id, email, hash_password(password))


def get_coach_id(org_id, email):
    cursor, conn = cur_conn()
    row = sql.getCoachID(cursor, conn, org_id, email)
    return row[0] if row else None


def get_player_id(org_id, email):
    cursor, conn = cur_conn()
    row = sql.getPlayerID(cursor, conn, org_id, email)
    return row[0] if row else None


def must_reset_password(table, id_col, entity_id):
    cursor, conn = cur_conn()
    cursor.execute('SELECT MustResetPassword FROM {} WHERE {} = ?'.format(table, id_col), (entity_id,))
    row = cursor.fetchone()
    return bool(row[0]) if row else False


def set_new_password(table, id_col, entity_id, new_password):
    cursor, conn = cur_conn()
    cursor.execute('UPDATE {} SET Password = ?, MustResetPassword = 0 WHERE {} = ?'.format(table, id_col),
                    (hash_password(new_password), entity_id))
    conn.commit()


# ---------- Org-level getters ----------

def get_org_details(org_id):
    cursor, conn = cur_conn()
    cursor.execute('SELECT OrgID, Name, Location, Manager, Email FROM Organisations WHERE OrgID = ?', (org_id,))
    return cursor.fetchone()


def get_all_coaches(org_id):
    cursor, conn = cur_conn()
    return sql.getAllCoaches(cursor, conn, org_id)  # (CoachID, Name, TeamName)


def get_all_players(org_id):
    cursor, conn = cur_conn()
    return sql.getAllPlayers(cursor, conn, org_id)  # (PlayerID, Number, Name)


def get_all_teams(org_id):
    cursor, conn = cur_conn()
    cursor.execute('SELECT TeamID, Name, CoachID FROM Teams WHERE OrgID = ?', (org_id,))
    return cursor.fetchall()


def get_coach_teams(coach_id):
    cursor, conn = cur_conn()
    return sql.getAllTeamsCoach(cursor, conn, coach_id)  # (TeamID, Name)


def get_player_teams(player_id):
    cursor, conn = cur_conn()
    return sql.getAllTeamsPlayer(cursor, conn, player_id)  # (TeamID, Name)


# ---------- Registering coaches / players / teams ----------

def get_coach(coach_id):
    cursor, conn = cur_conn()
    cursor.execute('SELECT CoachID, OrgID, Name, Email FROM Coaches WHERE CoachID = ?', (coach_id,))
    return cursor.fetchone()


def register_coach(org_id, name, email):
    cursor, conn = cur_conn()
    coach_id = sql.insertCoach(cursor, conn, org_id, name, email, hash_password(DEFAULT_PASSWORD))
    return coach_id


def register_player(org_id, name, number, email, positions):
    cursor, conn = cur_conn()
    if sql.checkPlayerNumber(cursor, conn, number) > 0:
        return None, 'That squad number is already taken.'
    player_id = sql.insertPlayer(cursor, conn, org_id, name, number, email, hash_password(DEFAULT_PASSWORD))
    return player_id, None


def get_player(player_id):
    cursor, conn = cur_conn()
    cursor.execute('SELECT PlayerID, OrgID, Name, Number, Email, Injured FROM Players WHERE PlayerID = ?', (player_id,))
    return cursor.fetchone()


def set_player_injured(player_id, injured: bool):
    cursor, conn = cur_conn()
    cursor.execute('UPDATE Players SET Injured = ? WHERE PlayerID = ?', (1 if injured else 0, player_id))
    conn.commit()


def register_team(org_id, name, location, main_coach_id, privacy_mode, player_ranks):
    """player_ranks: list of (player_id, position_name, rank) for the initial squad."""
    cursor, conn = cur_conn()
    team_id = sql.insertTeam(cursor, conn, org_id, name, main_coach_id, privacy_mode)
    sql.addCoachToTeam(cursor, conn, main_coach_id, team_id)
    added_players = set()
    for player_id, position_name, rank in player_ranks:
        if player_id not in added_players:
            sql.addPlayerToTeam(cursor, conn, player_id, team_id)
            added_players.add(player_id)
        sql.addPlayerPosition(cursor, conn, position_name, player_id, team_id, rank)
    return team_id


def get_team(team_id):
    cursor, conn = cur_conn()
    cursor.execute('SELECT TeamID, Name, OrgID, CoachID, PrivacyMode FROM Teams WHERE TeamID = ?', (team_id,))
    return cursor.fetchone()


def get_team_players(team_id):
    cursor, conn = cur_conn()
    rows = sql.getAllPlayersTeam(cursor, conn, team_id)  # (PlayerID, Number, Name)
    result = []
    for player_id, number, name in rows:
        p = get_player(player_id)
        result.append({'id': player_id, 'number': number, 'name': name, 'injured': bool(p[5]) if p else False})
    return result


def get_team_coaches(team_id):
    cursor, conn = cur_conn()
    cursor.execute('''SELECT Coaches.CoachID, Coaches.Name FROM CoachTeamLink
                       JOIN Coaches ON CoachTeamLink.CoachID = Coaches.CoachID
                       WHERE CoachTeamLink.TeamID = ?''', (team_id,))
    return cursor.fetchall()


def add_player_to_team(team_id, player_id):
    cursor, conn = cur_conn()
    cursor.execute('SELECT COUNT(*) FROM PlayerTeamLink WHERE PlayerID = ? AND TeamID = ?', (player_id, team_id))
    if cursor.fetchone()[0] == 0:
        sql.addPlayerToTeam(cursor, conn, player_id, team_id)


def remove_player_from_team(team_id, player_id):
    cursor, conn = cur_conn()
    sql.removePlayerFromTeam(cursor, conn, player_id, team_id)
    for position_name in logic.positionsList:
        sql.removePlayerPosition(cursor, conn, position_name, player_id, team_id)


# ---------- Position rankings ----------

def get_team_positions(team_id):
    """dict: position_name -> list of (player_id, name, number, rank), sorted by rank ascending."""
    cursor, conn = cur_conn()
    result = {}
    for position_name in logic.positionsList:
        rows = sql.initialGetAllPositions(cursor, conn, position_name, team_id)  # (PlayerID, Rank)
        entries = []
        for player_id, rank in rows:
            p = get_player(player_id)
            if p:
                entries.append({'id': player_id, 'name': p[2], 'number': p[3], 'rank': rank})
        entries.sort(key=lambda e: e['rank'])
        result[position_name] = entries
    return result


def set_player_position_rank(team_id, player_id, position_name, rank):
    cursor, conn = cur_conn()
    cursor.execute('SELECT COUNT(*) FROM {}table WHERE PlayerID = ? AND TeamID = ?'.format(position_name),
                    (player_id, team_id))
    exists = cursor.fetchone()[0] > 0
    if exists:
        cursor.execute('UPDATE {}table SET Rank = ? WHERE PlayerID = ? AND TeamID = ?'.format(position_name),
                        (rank, player_id, team_id))
        conn.commit()
    else:
        sql.addPlayerPosition(cursor, conn, position_name, player_id, team_id, rank)


def remove_player_position(team_id, player_id, position_name):
    cursor, conn = cur_conn()
    sql.removePlayerPosition(cursor, conn, position_name, player_id, team_id)


def _priority_queue_for(team_id, position_name):
    cursor, conn = cur_conn()
    rows = sql.initialGetAllPositions(cursor, conn, position_name, team_id)
    pq = []
    for player_id, rank in rows:
        logic.add_to_priority_queue([rank, player_id], pq)
    return pq


def get_player_positions_queue(team_id, player_id):
    """All positions this player is registered for on this team, with their similar positions."""
    positions = get_team_positions(team_id)
    result = []
    for pos_name, entries in positions.items():
        for e in entries:
            if e['id'] == player_id:
                result.append(pos_name)
    return result


# ---------- Editing / deleting accounts ----------

def update_org_details(org_id, name, location, manager_name, email):
    cursor, conn = cur_conn()
    if sql.checkNameInOrganisations(cursor, conn, name) > 0 and name != get_org_details(org_id)[1]:
        return 'A school/club with that name is already registered.'
    sql.updateOrgName(cursor, conn, name, org_id)
    sql.updateOrgLocation(cursor, conn, location, org_id)
    sql.updateOrgManager(cursor, conn, manager_name, org_id)
    sql.updateOrgEmail(cursor, conn, email, org_id)
    return None


def change_org_password(org_id, new_password):
    cursor, conn = cur_conn()
    sql.updateOrgPassword(cursor, conn, hash_password(new_password), org_id)


def delete_org(org_id):
    """Deletes the whole school/club and everything under it. Irreversible."""
    cursor, conn = cur_conn()
    cursor.execute('SELECT TeamID FROM Teams WHERE OrgID = ?', (org_id,))
    team_ids = [r[0] for r in cursor.fetchall()]
    for team_id in team_ids:
        delete_team(team_id)
    cursor.execute('SELECT PlayerID FROM Players WHERE OrgID = ?', (org_id,))
    for (player_id,) in cursor.fetchall():
        delete_player(player_id)
    cursor.execute('SELECT CoachID FROM Coaches WHERE OrgID = ?', (org_id,))
    for (coach_id,) in cursor.fetchall():
        cursor.execute('DELETE FROM CoachTeamLink WHERE CoachID = ?', (coach_id,))
        cursor.execute('DELETE FROM Coaches WHERE CoachID = ?', (coach_id,))
    cursor.execute('DELETE FROM Organisations WHERE OrgID = ?', (org_id,))
    conn.commit()


def update_coach(coach_id, name, email):
    cursor, conn = cur_conn()
    sql.updateCoachName(cursor, conn, name, coach_id)
    sql.updateCoachEmail(cursor, conn, email, coach_id)


def change_coach_password(coach_id, new_password):
    cursor, conn = cur_conn()
    sql.updateCoachPassword(cursor, conn, hash_password(new_password), coach_id)


def delete_coach(coach_id):
    """Returns an error string if the coach is the sole/main coach of a team
    (reassign that team's main coach first), otherwise deletes the coach."""
    cursor, conn = cur_conn()
    cursor.execute('SELECT TeamID, Name FROM Teams WHERE CoachID = ?', (coach_id,))
    main_of = cursor.fetchall()
    if main_of:
        names = ', '.join(t[1] for t in main_of)
        return 'This coach is the main coach of: {}. Reassign the main coach for that team first.'.format(names)
    cursor.execute('DELETE FROM CoachTeamLink WHERE CoachID = ?', (coach_id,))
    cursor.execute('DELETE FROM Coaches WHERE CoachID = ?', (coach_id,))
    conn.commit()
    return None


def update_player(player_id, name, number, email):
    cursor, conn = cur_conn()
    cursor.execute('SELECT COUNT(*) FROM Players WHERE Number = ? AND PlayerID != ?', (number, player_id))
    if cursor.fetchone()[0] > 0:
        return 'That squad number is already taken by another player.'
    sql.updatePlayerName(cursor, conn, name, player_id)
    sql.updatePlayerNumber(cursor, conn, number, player_id)
    sql.updatePlayerEmail(cursor, conn, email, player_id)
    return None


def change_player_password(player_id, new_password):
    cursor, conn = cur_conn()
    sql.updatePlayerPassword(cursor, conn, hash_password(new_password), player_id)


def delete_player(player_id):
    cursor, conn = cur_conn()
    cursor.execute('DELETE FROM PlayerTeamLink WHERE PlayerID = ?', (player_id,))
    for position_name in logic.positionsList:
        cursor.execute('DELETE FROM {}table WHERE PlayerID = ?'.format(position_name), (player_id,))
    cursor.execute('DELETE FROM Players WHERE PlayerID = ?', (player_id,))
    conn.commit()


def update_team(team_id, name, coach_id, privacy_mode):
    cursor, conn = cur_conn()
    sql.updateTeamName(cursor, conn, name, team_id)
    sql.updateTeamCoach(cursor, conn, coach_id, team_id)
    sql.updateTeamPrivacyMode(cursor, conn, privacy_mode, team_id)
    cursor.execute('SELECT COUNT(*) FROM CoachTeamLink WHERE CoachID = ? AND TeamID = ?', (coach_id, team_id))
    if cursor.fetchone()[0] == 0:
        sql.addCoachToTeam(cursor, conn, coach_id, team_id)


def delete_team(team_id):
    cursor, conn = cur_conn()
    cursor.execute('DELETE FROM PlayerTeamLink WHERE TeamID = ?', (team_id,))
    cursor.execute('DELETE FROM CoachTeamLink WHERE TeamID = ?', (team_id,))
    for position_name in logic.positionsList:
        cursor.execute('DELETE FROM {}table WHERE TeamID = ?'.format(position_name), (team_id,))
    cursor.execute('DELETE FROM Matches WHERE TeamID = ? OR OpponentID = ?', (team_id, team_id))
    cursor.execute('DELETE FROM Teams WHERE TeamID = ?', (team_id,))
    conn.commit()


# ---------- Matches ----------

def create_match(org_id, team_id, opponent_team_id, match_date, location, team_size, home_away):
    cursor, conn = cur_conn()
    match_id = sql.insertMatch(cursor, conn, org_id, team_id, opponent_team_id, 0, 0,
                                str(match_date), location, '')
    cursor.execute('UPDATE Matches SET HomeAway = ? WHERE MatchID = ?', (home_away, match_id))
    conn.commit()
    return match_id


def get_match(match_id):
    cursor, conn = cur_conn()
    cursor.execute('''SELECT MatchID, OrgID, TeamID, OpponentID, GoalsScored, GoalsConceded, Date, Location,
                              Formation, HomeAway
                       FROM Matches WHERE MatchID = ?''', (match_id,))
    return cursor.fetchone()


def get_team_matches(team_id):
    cursor, conn = cur_conn()
    return sql.getAllTeamMatches(cursor, conn, team_id, str(logic.get_season_start_date()))


def get_all_upcoming_matches(team_id):
    cursor, conn = cur_conn()
    cursor.execute('''SELECT T1.Name, T2.Name, Matches.Date, Matches.Location, Matches.MatchID, Matches.Formation
                       FROM Matches
                       JOIN Teams T1 ON Matches.TeamID = T1.TeamID
                       JOIN Teams T2 ON Matches.OpponentID = T2.TeamID
                       WHERE Matches.TeamID = ? AND Matches.Date >= ?
                       ORDER BY Matches.Date ASC''', (team_id, str(date.today())))
    return cursor.fetchall()


def record_match_result(match_id, goals_scored, goals_conceded):
    cursor, conn = cur_conn()
    sql.addScore(cursor, conn, match_id, goals_scored, goals_conceded)


def compute_tactic_split(team_id, opponent_id, team_size, match_date, use_opponent_data):
    """Ported from Match.chooseTacticSplit, minus the interactive privacy prompt
    (the web UI asks the coach up front instead)."""
    cursor, conn = cur_conn()
    tactic_split = None
    if use_opponent_data:
        opponent_formation = sql.getFormation(cursor, conn, get_team(team_id)[2], opponent_id, team_id, str(match_date))
        if opponent_formation is None:
            opponent_formation = sql.getFormationOfLastMatch(cursor, conn, get_team(team_id)[2], opponent_id)
        if opponent_formation is not None and opponent_formation[0]:
            opp_split = sql.getFormationSplit(cursor, conn, opponent_formation[0], team_size)
            if opp_split is not None:
                if abs(opp_split[0] - opp_split[1]) > 1:
                    tactic_split = [opp_split[1], opp_split[0]]
    org_id = get_team(team_id)[2]
    season_start = str(logic.get_season_start_date())
    opponent_results = sql.getTeamResults(cursor, conn, org_id, opponent_id, season_start)
    team_results = sql.getTeamResults(cursor, conn, org_id, team_id, season_start)
    if opponent_results > team_results:
        base = [0.6, 0.4]
    elif opponent_results < team_results:
        base = [0.4, 0.6]
    else:
        base = [0.5, 0.5]
    if tactic_split is None:
        tactic_split = base
    else:
        tactic_split = [(tactic_split[0] + base[0]) / 2, (tactic_split[1] + base[1]) / 2]
    return tactic_split


def get_recommended_formations(team_size, tactic_split):
    """Ported from Match.getRecommendedFormations - clusters known formations for this
    team size and returns the cluster closest to the desired tactic split."""
    cursor, conn = cur_conn()
    # Same table-naming scheme used by sql.getFormationSplit/checkIfInFormations
    # (the original console app used two different, inconsistent names here -
    # unified to one so lookups actually match what gets written).
    table_name = 'Formations{}side'.format(team_size)
    sql.createFormationsTable(cursor, conn, table_name)
    cursor.execute('SELECT * FROM {}'.format(table_name))
    records = cursor.fetchall()
    if len(records) < 3:
        # Not enough history yet - seed with the theoretically generated formations
        generated = logic.generate_formations(team_size)
        for name, deff, off in generated:
            if sql.checkIfInFormations(cursor, conn, name, team_size) == 0:
                sql.insertFormation(cursor, conn, table_name, name, deff, off)
        cursor.execute('SELECT * FROM {}'.format(table_name))
        records = cursor.fetchall()
    if len(records) == 0:
        return []
    centroids, clusters = logic.cluster(records, team_size)
    if len(centroids) == 0:
        return []
    best_dist = float('inf')
    best_idx = -1
    for i, centroid in enumerate(centroids):
        d = (centroid[0] - tactic_split[0]) ** 2 + (centroid[1] - tactic_split[1]) ** 2
        if d < best_dist:
            best_dist = d
            best_idx = i
    chosen_cluster = clusters[best_idx]
    return [row[1] for row in chosen_cluster]  # formation names


def get_closest_past_match(team_id, team_size, exclude_match_id, tactic_split):
    cursor, conn = cur_conn()
    matches = sql.getAllTeamMatches(cursor, conn, team_id, str(logic.get_season_start_date()))
    # matches: (TeamName, OpponentName, Date, Location, GoalsScored, GoalsConceded, MatchID)
    best = None
    best_dist = float('inf')
    for m in matches:
        if m[6] == exclude_match_id:
            continue
        row = get_match(m[6])
        if row is None or not row[8]:  # no formation recorded
            continue
        split = sql.getFormationSplit(cursor, conn, row[8], team_size)
        if split is None:
            continue
        d = (split[0] - tactic_split[0]) ** 2 + (split[1] - tactic_split[1]) ** 2
        if d < best_dist:
            best_dist = d
            best = row
    return best  # match row or None


def build_lineup_for_formation(team_id, formation, available_player_ids):
    """Ported from Match.makeLineupWithPriorityQueue. Returns
    {position_name: player_id or None} plus leftover subs (available players not used)."""
    positions = get_team_positions(team_id)
    formation_positions = logic.make_positions_list(formation)  # flat list, e.g. ['LB','CM',...,'ST']
    slots = list(formation_positions)  # position name per outfield slot, index-aligned
    assigned = [None] * len(slots)
    keeper = None
    available = set(available_player_ids)

    # Exact-position candidates for a slot, sorted best rank first.
    def exact_candidates(position_name):
        pool = [(e['rank'], e['id']) for e in positions.get(position_name, []) if e['id'] in available]
        pool.sort(key=lambda x: x[0])
        return pool

    # Fallback candidates from positions that can deputise, sorted best rank first.
    def similar_candidates(position_name):
        pool = []
        for name in logic.similar_positions(position_name):
            if name == position_name:
                continue
            for entry in positions.get(name, []):
                if entry['id'] in available:
                    pool.append((entry['rank'], entry['id']))
        pool.sort(key=lambda x: x[0])
        return pool

    # Goalkeeper first - only exact GK position counts.
    gk_pool = exact_candidates('GK')
    if gk_pool:
        keeper = gk_pool[0][1]
        available.discard(keeper)

    # Pass 1: fill every slot from players ranked in that EXACT position first,
    # so (e.g.) a ranked centre-back always gets first claim on a CB slot before
    # a full-back slot is allowed to poach them via the "similar position" fallback.
    remaining_slots = list(range(len(slots)))
    changed = True
    while changed and remaining_slots:
        changed = False
        for idx in list(remaining_slots):
            pool = exact_candidates(slots[idx])
            if pool:
                chosen = pool[0][1]
                assigned[idx] = chosen
                available.discard(chosen)
                remaining_slots.remove(idx)
                changed = True

    # Pass 2: only now fall back to similar positions for whatever's left unfilled.
    changed = True
    while changed and remaining_slots:
        changed = False
        for idx in list(remaining_slots):
            pool = similar_candidates(slots[idx])
            if pool:
                chosen = pool[0][1]
                assigned[idx] = chosen
                available.discard(chosen)
                remaining_slots.remove(idx)
                changed = True

    subs = [pid for pid in available_player_ids if pid in available]
    # A formation can repeat a position name (e.g. two CMs), so group into
    # lists rather than a flat dict, which would silently drop duplicates.
    lineup = {}
    for i in range(len(slots)):
        lineup.setdefault(slots[i], []).append(assigned[i])
    return lineup, keeper, subs
