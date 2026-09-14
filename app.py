import streamlit as st
from datetime import date
import services as s
import logic

st.set_page_config(page_title='Team Manager', page_icon='⚽', layout='wide')

DEFAULT_PASSWORD = s.DEFAULT_PASSWORD


def init_state():
    defaults = {
        'role': None, 'org_id': None, 'org_name': None,
        'coach_id': None, 'coach_name': None,
        'player_id': None, 'player_name': None,
        'active_team_id': None, 'active_match_id': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_state()


# ---------------- Pitch visualisation ----------------

def render_pitch(formation, lineup, keeper_name, player_names, height=520):
    rows = logic.make_positions_array(formation)  # [defence, midfield(maybe nested), attack]
    flat_rows = []
    for row in rows:
        if len(row) == 0:
            continue
        if isinstance(row[0], list):
            for sub in row:
                flat_rows.append(sub)
        else:
            flat_rows.append(row)
    # attack should render at the top of the pitch, GK at the bottom
    display_rows = [['GK']] + list(reversed(flat_rows))

    # Track how many times each position label has been consumed, so repeated
    # labels (e.g. two 'CM's) each get their own slot from the lineup dict.
    consumed = {}

    def chip(position_name):
        if position_name == 'GK':
            label = keeper_name or '—'
        else:
            idx = consumed.get(position_name, 0)
            consumed[position_name] = idx + 1
            slots = lineup.get(position_name)
            pid = None
            if isinstance(slots, list):
                pid = slots[idx] if idx < len(slots) else None
            else:
                pid = slots if idx == 0 else None
            label = player_names.get(pid, '—') if pid else '—'
        return '''<div style="background:white;border-radius:8px;padding:6px 4px;
                    text-align:center;font-size:12px;font-weight:600;color:#1a1a1a;
                    box-shadow:0 1px 3px rgba(0,0,0,0.3);min-width:64px;">
                    <div style="font-size:9px;color:#666;">{}</div>{}</div>'''.format(position_name, label)

    rows_html = ''
    for row in display_rows:
        cells = ''.join(chip(pos) for pos in row)
        rows_html += '<div style="display:flex;justify-content:space-evenly;align-items:center;padding:14px 0;">{}</div>'.format(cells)

    html = '''
    <div style="background:linear-gradient(180deg,#2d8a4e,#237040);border-radius:12px;
                padding:10px;border:3px solid white;">
      {}
    </div>
    '''.format(rows_html)
    st.markdown(html, unsafe_allow_html=True)


# ---------------- Login / registration ----------------

def login_screen():
    st.title('⚽ Team Manager')
    st.caption('Squad selection, formations and lineups for your team.')

    orgs = s.get_organisations()
    org_names = {name: oid for oid, name in orgs}

    tab_login, tab_register = st.tabs(['Log in', 'Register a new school / club'])

    with tab_register:
        st.subheader('Register your school or club')
        st.caption('Do this once. After that, your coaches and players log in with the accounts you create for them.')
        with st.form('register_org'):
            name = st.text_input('School / club name')
            location = st.text_input('Location')
            manager_name = st.text_input('Your name (as manager/admin)')
            email = st.text_input('Your email')
            password = st.text_input('Choose a password', type='password')
            submitted = st.form_submit_button('Register')
        if submitted:
            if not all([name, location, manager_name, email, password]):
                st.error('Please fill in every field.')
            else:
                org_id, err = s.register_org(name, location, manager_name, email, password)
                if err:
                    st.error(err)
                else:
                    st.success('Registered! Switch to the "Log in" tab and sign in as Manager.')

    with tab_login:
        if not org_names:
            st.info('No schools/clubs registered yet - use the Register tab first.')
            return
        org_choice = st.selectbox('School / club', list(org_names.keys()))
        org_id = org_names[org_choice]
        role = st.radio('I am logging in as...', ['Manager', 'Coach', 'Player'], horizontal=True)
        with st.form('login_form'):
            email = st.text_input('Email')
            password = st.text_input('Password', type='password')
            submitted = st.form_submit_button('Log in')
        if submitted:
            if role == 'Manager':
                if s.login_org(org_id, email, password):
                    st.session_state.role = 'manager'
                    st.session_state.org_id = org_id
                    st.session_state.org_name = org_choice
                    st.rerun()
                else:
                    st.error('Incorrect email or password.')
            elif role == 'Coach':
                coach_id = s.get_coach_id(org_id, email)
                if coach_id and s.login_coach(org_id, email, password):
                    st.session_state.role = 'coach'
                    st.session_state.org_id = org_id
                    st.session_state.org_name = org_choice
                    st.session_state.coach_id = coach_id
                    st.rerun()
                else:
                    st.error('Incorrect email or password.')
            else:
                player_id = s.get_player_id(org_id, email)
                if player_id and s.login_player(org_id, email, password):
                    st.session_state.role = 'player'
                    st.session_state.org_id = org_id
                    st.session_state.org_name = org_choice
                    st.session_state.player_id = player_id
                    st.rerun()
                else:
                    st.error('Incorrect email or password.')
        st.caption('New coach/player accounts start with the password **{}** - you\'ll be asked to change it on first login.'.format(DEFAULT_PASSWORD))


def force_password_reset(table, id_col, entity_id, on_done):
    st.warning('First time logging in - please set a new password.')
    with st.form('reset_pw'):
        p1 = st.text_input('New password', type='password')
        p2 = st.text_input('Confirm new password', type='password')
        submitted = st.form_submit_button('Set password')
    if submitted:
        if len(p1) < 4:
            st.error('Password should be at least 4 characters.')
        elif p1 != p2:
            st.error('Passwords do not match.')
        else:
            s.set_new_password(table, id_col, entity_id, p1)
            st.success('Password updated.')
            on_done()
            st.rerun()
    st.stop()


# ---------------- Manager dashboard ----------------

def manager_dashboard():
    org_id = st.session_state.org_id
    st.sidebar.title('⚽ ' + st.session_state.org_name)
    st.sidebar.caption('Manager')
    if st.sidebar.button('Log out'):
        logout()
        st.rerun()

    tabs = st.tabs(['Teams', 'Coaches', 'Players', 'Org settings'])

    with tabs[0]:
        st.subheader('Teams')
        teams = s.get_all_teams(org_id)
        coaches = s.get_all_coaches(org_id)
        coach_names = {cid: name for cid, name, _ in coaches}
        for team_id, team_name, coach_id in teams:
            with st.expander('{} (coach: {})'.format(team_name, coach_names.get(coach_id, '—'))):
                players = s.get_team_players(team_id)
                st.write(', '.join('#{} {}'.format(p['number'], p['name']) for p in players) or 'No players yet.')

        st.divider()
        st.markdown('##### Register a new team')
        if not coaches:
            st.info('Register a coach first.')
        else:
            all_players = s.get_all_players(org_id)
            with st.form('new_team'):
                team_name = st.text_input('Team name (e.g. "U16 Boys")')
                location = st.text_input('Home location')
                coach_choice = st.selectbox('Main coach', options=[c[0] for c in coaches],
                                             format_func=lambda cid: coach_names[cid])
                privacy = st.checkbox('Privacy mode (hide this team\'s formations/results from opponents\' recommendations)')
                chosen_players = st.multiselect('Initial squad', options=[p[0] for p in all_players],
                                                 format_func=lambda pid: next('#{} {}'.format(n, nm) for i, n, nm in all_players if i == pid))
                submitted = st.form_submit_button('Create team (you can rank positions afterwards)')
            if submitted:
                if not team_name or not chosen_players:
                    st.error('Give the team a name and at least one player.')
                else:
                    team_id = s.register_team(org_id, team_name, location, coach_choice, privacy, [])
                    for pid in chosen_players:
                        s.add_player_to_team(team_id, pid)
                    st.success('Team created. The coach can now rank players by position from their dashboard.')
                    st.rerun()

    with tabs[1]:
        st.subheader('Coaches')
        coaches = s.get_all_coaches(org_id)
        for cid, name, team_name in coaches:
            st.write('**{}** — {}'.format(name, team_name or 'no team yet'))
        st.divider()
        st.markdown('##### Register a new coach')
        with st.form('new_coach'):
            name = st.text_input('Coach name')
            email = st.text_input('Coach email (used to log in)')
            submitted = st.form_submit_button('Register coach')
        if submitted:
            if not name or not email:
                st.error('Name and email required.')
            else:
                s.register_coach(org_id, name, email)
                st.success('Coach registered. They can log in with the default password "{}".'.format(DEFAULT_PASSWORD))
                st.rerun()

    with tabs[2]:
        st.subheader('Players')
        players = s.get_all_players(org_id)
        for pid, number, name in players:
            st.write('#{} {}'.format(number, name))
        st.divider()
        st.markdown('##### Register a new player')
        with st.form('new_player'):
            name = st.text_input('Player name')
            number = st.number_input('Squad number', min_value=1, max_value=99, step=1)
            email = st.text_input('Player email (used to log in) - or a parent/guardian email')
            submitted = st.form_submit_button('Register player')
        if submitted:
            if not name or not email:
                st.error('Name and email required.')
            else:
                pid, err = s.register_player(org_id, name, int(number), email, [])
                if err:
                    st.error(err)
                else:
                    st.success('Player registered. Default password: "{}".'.format(DEFAULT_PASSWORD))
                    st.rerun()

    with tabs[3]:
        org = s.get_org_details(org_id)
        st.subheader('Organisation details')
        st.write('**Name:** {}'.format(org[1]))
        st.write('**Location:** {}'.format(org[2]))
        st.write('**Manager:** {}'.format(org[3]))
        st.write('**Email:** {}'.format(org[4]))


# ---------------- Coach dashboard ----------------

def coach_dashboard():
    org_id = st.session_state.org_id
    coach_id = st.session_state.coach_id

    if s.must_reset_password('Coaches', 'CoachID', coach_id):
        force_password_reset('Coaches', 'CoachID', coach_id, lambda: None)

    teams = s.get_coach_teams(coach_id)
    st.sidebar.title('⚽ ' + st.session_state.org_name)
    st.sidebar.caption('Coach')
    if not teams:
        st.sidebar.warning('No team assigned yet - ask your manager to add you as a team\'s coach.')
        if st.sidebar.button('Log out'):
            logout()
            st.rerun()
        return

    team_names = {tid: name for tid, name in teams}
    if st.session_state.active_team_id not in team_names:
        st.session_state.active_team_id = teams[0][0]
    st.session_state.active_team_id = st.sidebar.selectbox(
        'Team', options=list(team_names.keys()), format_func=lambda t: team_names[t],
        index=list(team_names.keys()).index(st.session_state.active_team_id))
    if st.sidebar.button('Log out'):
        logout()
        st.rerun()

    team_id = st.session_state.active_team_id
    tabs = st.tabs(['Squad & positions', 'Matches', 'Match centre'])

    with tabs[0]:
        squad_and_positions_tab(org_id, team_id)
    with tabs[1]:
        matches_tab(org_id, team_id)
    with tabs[2]:
        match_centre_tab(org_id, team_id)


def squad_and_positions_tab(org_id, team_id):
    st.subheader('Squad')
    players = s.get_team_players(team_id)
    all_org_players = s.get_all_players(org_id)
    current_ids = {p['id'] for p in players}

    cols = st.columns(3)
    for i, p in enumerate(players):
        with cols[i % 3]:
            injured_now = p['injured']
            new_val = st.checkbox('#{} {} - injured'.format(p['number'], p['name']), value=injured_now,
                                   key='inj_{}'.format(p['id']))
            if new_val != injured_now:
                s.set_player_injured(p['id'], new_val)
                st.rerun()

    with st.expander('Add a player to this squad'):
        addable = [(pid, num, name) for pid, num, name in all_org_players if pid not in current_ids]
        if addable:
            choice = st.selectbox('Player', options=[a[0] for a in addable],
                                   format_func=lambda pid: next('#{} {}'.format(n, nm) for i, n, nm in addable if i == pid))
            if st.button('Add to squad'):
                s.add_player_to_team(team_id, choice)
                st.rerun()
        else:
            st.caption('Every registered player is already in this squad.')

    st.divider()
    st.subheader('Position rankings')
    st.caption('Rank 1 (best) to 5 (weakest) for every position a player can play. This drives the automatic lineup suggestions.')
    positions = s.get_team_positions(team_id)
    pos_cols = st.columns(2)
    for i, pos_name in enumerate(logic.positionsList):
        with pos_cols[i % 2]:
            st.markdown('**{}**'.format(pos_name))
            existing = {e['id']: e['rank'] for e in positions[pos_name]}
            for p in players:
                cur_rank = existing.get(p['id'], 0)
                new_rank = st.select_slider(
                    '#{} {}'.format(p['number'], p['name']),
                    options=[0, 1, 2, 3, 4, 5],
                    value=cur_rank,
                    key='rank_{}_{}'.format(pos_name, p['id']),
                    help='0 = does not play this position')
                if new_rank != cur_rank:
                    if new_rank == 0:
                        s.remove_player_position(team_id, p['id'], pos_name)
                    else:
                        s.set_player_position_rank(team_id, p['id'], pos_name, new_rank)


def matches_tab(org_id, team_id):
    st.subheader('Fixtures')
    all_teams = s.get_all_teams(org_id)
    opponent_options = [(tid, name) for tid, name, _ in all_teams if tid != team_id]

    with st.form('new_match'):
        c1, c2, c3 = st.columns(3)
        with c1:
            opp_id = st.selectbox('Opponent', options=[o[0] for o in opponent_options],
                                   format_func=lambda tid: next(n for i, n in opponent_options if i == tid)) if opponent_options else None
            opp_name_manual = None
            if not opponent_options:
                opp_name_manual = st.text_input('Opponent name (not in this system)')
        with c2:
            match_date = st.date_input('Date', value=date.today())
            team_size = st.selectbox('Format', [5, 7, 9, 11], index=3)
        with c3:
            location = st.text_input('Location')
            home_away = st.radio('Home / away', ['Home', 'Away'], horizontal=True)
        submitted = st.form_submit_button('Schedule match')
    if submitted:
        if not opponent_options and not opp_name_manual:
            st.error('Enter an opponent.')
        else:
            if opponent_options:
                final_opp_id = opp_id
            else:
                coaches = s.get_all_coaches(org_id)
                final_opp_id = s.register_team(org_id, opp_name_manual, location,
                                                 coaches[0][0] if coaches else None, True, [])
            match_id = s.create_match(org_id, team_id, final_opp_id, match_date, location, team_size, home_away)
            st.success('Match scheduled.')
            st.session_state.active_match_id = match_id
            st.rerun()

    st.divider()
    upcoming = s.get_all_upcoming_matches(team_id)
    st.markdown('##### Upcoming')
    for home_name, away_name, mdate, mloc, mid, mformation in upcoming:
        c1, c2 = st.columns([4, 1])
        with c1:
            st.write('{} vs {} — {} at {}{}'.format(home_name, away_name, mdate, mloc,
                                                      ' ({})'.format(mformation) if mformation else ''))
        with c2:
            if st.button('Open', key='open_{}'.format(mid)):
                st.session_state.active_match_id = mid
                st.rerun()

    st.markdown('##### Past results')
    past = s.get_team_matches(team_id)
    for row in past:
        home_name, away_name, mdate, mloc, gs, gc, mid = row
        if gs or gc:
            st.write('{} {} - {} {} ({})'.format(home_name, gs, gc, away_name, mdate))


def match_centre_tab(org_id, team_id):
    match_id = st.session_state.active_match_id
    if not match_id:
        st.info('Schedule or open a match from the "Matches" tab first.')
        return
    match = s.get_match(match_id)
    if not match or match[2] != team_id:
        st.info('Open a match for this team from the "Matches" tab.')
        return
    _, _, _, opp_id, gscored, gconceded, mdate, mloc, mformation, home_away = match
    opp_team = s.get_team(opp_id)
    st.subheader('{} vs {} — {}'.format('Your team', opp_team[1] if opp_team else '?', mdate))

    players = s.get_team_players(team_id)
    st.markdown('##### Who is available?')
    cols = st.columns(3)
    available_ids = []
    for i, p in enumerate(players):
        with cols[i % 3]:
            default = not p['injured']
            checked = st.checkbox('#{} {}{}'.format(p['number'], p['name'], ' (injured)' if p['injured'] else ''),
                                   value=default, key='avail_{}_{}'.format(match_id, p['id']))
            if checked:
                available_ids.append(p['id'])

    team_size_guess = 11
    fm = logic.make_positions_list(mformation) if mformation else None

    st.markdown('##### Formation & lineup')
    team_row = s.get_team(team_id)
    privacy = bool(team_row[4])
    if privacy:
        use_opponent_data = st.checkbox('Turn off privacy mode for this match to factor in the opponent\'s known formation?')
    else:
        use_opponent_data = True

    if st.button('Get recommendations'):
        tactic = s.compute_tactic_split(team_id, opp_id, team_size_guess, mdate, use_opponent_data)
        recommended = s.get_recommended_formations(team_size_guess, tactic)
        st.session_state['_recs_{}'.format(match_id)] = recommended
        st.session_state['_tactic_{}'.format(match_id)] = tactic

    recs = st.session_state.get('_recs_{}'.format(match_id), [])
    choice = None
    if recs:
        tactic = st.session_state.get('_tactic_{}'.format(match_id))
        st.caption('Suggested tactical split (defensive / attacking): {:.0%} / {:.0%}'.format(tactic[0], tactic[1]))
        choice = st.radio('Recommended formations', recs, horizontal=True, key='formation_choice_{}'.format(match_id))

    all_formations = [f[0] for f in logic.generate_formations(team_size_guess)]
    manual_formation = st.selectbox('...or pick any formation manually', options=[''] + sorted(set(all_formations)))
    final_formation = manual_formation or choice or mformation

    if final_formation and available_ids:
        lineup, keeper, subs = s.build_lineup_for_formation(team_id, final_formation, available_ids)
        player_names = {p['id']: '#{} {}'.format(p['number'], p['name']) for p in players}
        keeper_name = player_names.get(keeper, '—')

        st.markdown('###### {}'.format(final_formation))
        render_pitch(final_formation, lineup, keeper_name, player_names)

        missing = []
        for pos, pids in lineup.items():
            missing.extend([pos] * pids.count(None))
        if missing or keeper is None:
            st.warning('No suitable ranked player found for: {}'.format(
                ', '.join((['GK'] if keeper is None else []) + missing)))

        st.markdown('**Subs:** ' + (', '.join(player_names[pid] for pid in subs) if subs else 'none'))

        if st.button('Confirm this formation for the match'):
            from db import cur_conn
            import sql as sqlmod
            cur, conn = cur_conn()
            sqlmod.addFormation(cur, conn, match_id, final_formation)
            st.success('Formation saved to the match.')
            st.rerun()

    st.divider()
    st.markdown('##### Result')
    with st.form('result_form'):
        c1, c2 = st.columns(2)
        with c1:
            gs = st.number_input('Goals scored', min_value=0, value=gscored or 0, step=1)
        with c2:
            gc = st.number_input('Goals conceded', min_value=0, value=gconceded or 0, step=1)
        submitted = st.form_submit_button('Save result')
    if submitted:
        s.record_match_result(match_id, int(gs), int(gc))
        st.success('Result saved.')
        st.rerun()


# ---------------- Player dashboard ----------------

def player_dashboard():
    org_id = st.session_state.org_id
    player_id = st.session_state.player_id

    if s.must_reset_password('Players', 'PlayerID', player_id):
        force_password_reset('Players', 'PlayerID', player_id, lambda: None)

    player = s.get_player(player_id)
    st.sidebar.title('⚽ ' + st.session_state.org_name)
    st.sidebar.caption('Player: {}'.format(player[2]))
    if st.sidebar.button('Log out'):
        logout()
        st.rerun()

    st.title('Hi, {}'.format(player[2]))
    injured = bool(player[5])
    new_injured = st.checkbox('I am currently injured / unavailable', value=injured)
    if new_injured != injured:
        s.set_player_injured(player_id, new_injured)
        st.rerun()

    st.divider()
    teams = s.get_player_teams(player_id)
    for team_id, team_name in teams:
        st.subheader(team_name)
        upcoming = s.get_all_upcoming_matches(team_id)
        if upcoming:
            for home_name, away_name, mdate, mloc, mid, mformation in upcoming:
                st.write('{} vs {} — {} at {}'.format(home_name, away_name, mdate, mloc))
        else:
            st.caption('No upcoming matches scheduled.')


# ---------------- Main ----------------

def main():
    init_state()
    if st.session_state.role is None:
        login_screen()
    elif st.session_state.role == 'manager':
        manager_dashboard()
    elif st.session_state.role == 'coach':
        coach_dashboard()
    elif st.session_state.role == 'player':
        player_dashboard()


if __name__ == '__main__':
    main()
