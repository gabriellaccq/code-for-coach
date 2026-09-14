# Team Manager (web version)

A web rebuild of the original NEA console program. Same core ideas —
priority-queue position rankings, formation clustering by tactical split,
closest-match lineup suggestions — with a browser interface instead of a
text menu.

## What's in this folder

- `app.py` — the Streamlit screens (login, manager/coach/player dashboards).
- `services.py` — all the business logic (registering teams/players, running
  matches, building lineups). This replaces the old `Org`/`Coach`/`Player`/
  `Team`/`Match` classes.
- `logic.py` — the pure algorithms (priority queue, k-means-style formation
  clustering, formation generation) ported out of the old classes.
- `sql.py` — unchanged database layer from the original project.
- `db.py` — sets up the SQLite database and schema.
- `nea.db` — created automatically the first time you run the app.

## Option A — run it locally (fastest way to try it out)

1. Install Python 3.10+ if you don't have it.
2. Open a terminal in this folder and run:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. It'll open in your browser at `http://localhost:8501`.
4. First screen: register your school/club (one-time setup), then log in as
   Manager to add your coach and players.

Your coach can use it this way too — just share this folder and the two
commands above. No coding knowledge needed after that.

## Option B — host it so your coach just opens a link (recommended)

This uses Streamlit Community Cloud, which is free.

1. Push this folder to a **GitHub repository** (can be the same NEA repo, or
   a new one — a new one is cleaner).
2. Go to https://share.streamlit.io, sign in with GitHub.
3. Click "New app", pick the repository and branch, and set the main file
   to `app.py`.
4. Deploy. You'll get a URL like `https://yourname-teammanager.streamlit.app`.
5. Send that link to your coach — that's it, no installation on their end.

**Note on the database with Option B:** Streamlit Community Cloud's free tier
resets the filesystem on redeploys/sleep, so `nea.db` isn't permanent
storage there. For a one-off school season this is usually fine, but if you
want the data to survive restarts long-term, the cleanest upgrade is
swapping SQLite for a small hosted database (e.g. Turso or Supabase) — happy
to help with that if it becomes a problem.

## Logging in

- **Manager**: the account you create when you first register the
  school/club. Registers coaches, players and teams.
- **Coach**: created by the manager. Default password is `Password123` —
  you'll be forced to change it on first login.
- **Player**: same as coach — created by the manager (or coach), default
  password `Password123`, changed on first login.

## Known limitations / things worth doing next

- **Central defenders are labelled 'CM'** in the original formation-building
  algorithm (a quirk carried over from the original code) — a back-four's
  two central defenders pull from your central-midfield rankings rather
  than a dedicated centre-back pool. Worth fixing before relying on it for
  real matches.
- The "borrow a player from another team" and full "build your own lineup
  by hand" flows from the console version aren't in this build yet — the
  recommended-formation flow is the main path for now.
- Passwords are hashed (the original stored them in plain text), but there's
  no password-reset-by-email flow — if someone forgets their password, the
  manager needs to reset it directly in the database for now.
