# TutorLearning

A web app where teachers run online courses and students enroll, read course posts, and submit assignments.

This was a class project and is not under active development.

> **Unfinished, not ready for real users.** The API now checks who is calling, but it has no login rate limit or email verification, and this access control has only run locally. See [Status and limits](#status-and-limits).

![Course dashboard showing three enrolled courses](docs/assets/screenshot.png)

*Dashboard from a local run with fictional data.*

## Highlights

- **One account, both roles.** A teacher can run courses and also enroll in other teachers' courses.
- **Server-side sessions.** Login sets an HttpOnly cookie, the API takes the caller's identity only from that session, and each route checks who may use it. See [Access rules](#access-rules).
- **A single feed per course.** Posts, assignments with due dates, and files appear together, with the student list one tab away.
- **Welcome emails that survive a failed send.** Database triggers queue registration and enrollment emails, and each one is marked sent or failed with the error kept.
- **A documented schema.** The [database diagram](backend/uml/database_model.svg) covers every table.

## Run it locally

You need Docker, Python 3.11, and Node.js. The app was first tested with MySQL 8.4 and Node 22. The access control was tested with MariaDB 11.8 only.

**1. Start a database.** Give it about 20 seconds to come up.

```bash
docker run -d --name tutor-db -e MYSQL_ROOT_PASSWORD=change-me \
  -e MYSQL_DATABASE=tutorlearning -p 127.0.0.1:3306:3306 mysql:8.4
```

**2. Start the backend.** It creates the tables and triggers on startup.

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DB_HOST=127.0.0.1 DB_USER=root DB_PASSWORD=change-me DB_NAME=tutorlearning
export SESSION_COOKIE_SECURE=false
uvicorn main:app --port 8000
```

`DB_HOST` is required: without it, the backend stops at startup with an error. `SESSION_COOKIE_SECURE=false` is for local runs over plain http only.

**3. Start the frontend.** It calls `http://localhost:8000` by default.

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:3000>. Use `localhost`, not `127.0.0.1`: the browser treats them as different sites, so login would not stick.

**4. Create the first admin.** Sign up in the browser. Then, in a second terminal with the virtual environment active and the same `DB_*` values exported, run this.

```bash
cd backend
python manage_admins.py grant you@example.com
```

Admins give other people the teacher role. No API route can grant the admin role, so it always takes this command. `revoke` removes it.

### Optional sample data

Run this in a second terminal, with the virtual environment active and the same `export` line set.

```bash
cd backend
python seed_data.py
```

> **This drops every table** in the database that the `DB_*` variables select. Run it only against your local database.

It then adds 20 invented users at `example.com` and 25 courses, and prints test accounts with their password. The first teacher is also an admin. The password is random on each run, unless you set `SEED_USER_PASSWORD`. Seeding queues no email.

## Usage

In the browser:

1. Sign up. Every new account starts as a student.
2. As an admin, open the **Users** tab and choose **Make teacher** for anyone who will run courses. They see the change after a page reload.
3. As a teacher, open the **Teaching** tab and choose **Create New Class**. New classes start as drafts, so edit the course to publish it.
4. As a student, open **Discover**, enroll in a public course, then open it to read the feed.

Or call the API directly. Interactive docs are at <http://localhost:8000/docs>. Keep the cookie, and send the `csrf_token` from the login response with every `POST`, `PUT`, `PATCH`, and `DELETE`.

```bash
curl -X POST http://localhost:8000/users/ -H 'Content-Type: application/json' \
  -d '{"first_name":"Sam","last_name":"Rivera","email":"sam@example.com","password":"change-me"}'

curl -X POST http://localhost:8000/login/ -H 'Content-Type: application/json' -c cookies.txt \
  -d '{"email":"sam@example.com","password":"change-me"}'

curl http://localhost:8000/enrollments/me -b cookies.txt

curl -X POST http://localhost:8000/logout/ -b cookies.txt -H 'X-CSRF-Token: <csrf_token from login>'
```

## Access rules

The caller is always the user of the session cookie. A request body with a field its route does not accept, such as `user_id`, `teacher_id`, `is_teacher`, `is_admin`, or `grade`, gets a 422 error.

| Who | Can do |
|-----|--------|
| Anyone | `GET /`, sign up, log in, read the API docs at `/docs` |
| Any logged-in user | Own profile and session, log out, upload a file, see visible courses, enroll in a visible and open course, leave a course |
| Enrolled student | Read the course's posts, assignments, files, and student list without emails. Submit and delete their own work |
| The course's teacher | Read the same course content, plus see student emails. Edit or delete the course, and manage its posts, assignments, and files. This stays true if the teacher role is later revoked |
| Teacher | Create courses |
| Admin | List and view users, grant or revoke the teacher role. Admins get no extra access to course content |

Without a valid session, a request gets a 401 error. With a session but no permission, it gets a 403 error. Every state-changing request also needs the session's `X-CSRF-Token` header, or it gets a 403 error. Sessions expire after `SESSION_TTL_HOURS`.

The **Discover** tab offers only **Enroll**: a course's content opens after you join. An existing database keeps its `is_teacher` values, including any that people gave themselves before this change, so review them in the **Users** tab.

## Configuration

The backend reads these environment variables, or a `backend/.env` file.

| Variables | Purpose | Without them |
|-----------|---------|--------------|
| `DB_HOST` | MySQL host | Startup fails, unless `INSTANCE_UNIX_SOCKET` is set |
| `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL connection | Defaults in `backend/database.py`, with an empty password |
| `INSTANCE_UNIX_SOCKET` | Cloud SQL socket, used on Cloud Run instead of TCP | TCP connection through `DB_HOST` |
| `GCS_BUCKET_NAME` | Bucket for uploads | Uploads return a 500 error |
| `GCP_PROJECT_ID`, `GCP_PRIVATE_KEY`, `GCP_CLIENT_EMAIL` | Service account for the bucket | Application Default Credentials |
| `GMAIL_SENDER_EMAIL`, `GMAIL_APP_PASSWORD` | Sends queued email through Gmail SMTP | Emails are marked failed, and nothing is sent |
| `SEED_USER_PASSWORD` | Password for seeded accounts | Random password for each seed run |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins. `*` stops startup | Only `http://localhost:3000` |
| `SESSION_COOKIE_SECURE` | Set to `false` for local runs over plain http | The cookie is `Secure`, so browsers may not send it over http |
| `SESSION_COOKIE_SAMESITE` | `lax`, `strict`, or `none`. `none` needs a `Secure` cookie | `lax` |
| `SESSION_TTL_HOURS` | How long a session lasts | 12 hours |

The frontend reads one variable at build time. Set `VITE_API_URL`, with no trailing slash, when you build for a deployed backend: `VITE_API_URL=https://api.example.com npm run build`. Without it, the build calls `http://localhost:8000`.

For a deployed setup, serve the frontend and API from the same site, such as `app.example.com` and `api.example.com`, and list the frontend in `CORS_ALLOWED_ORIGINS`. On different sites, the default `SameSite=Lax` cookie is not sent.

## Tests

```bash
cd backend
pip install -r tests/requirements.txt
pytest tests
```

The tests never use your `DB_*` settings. `tests/test_access_control.py` checks every route as an anonymous caller, the wrong user, and the right user, and fails if a new route is missing from its table. Four seeding tests need real MySQL triggers and skip by default. To run them, set `TEST_DB_NAME`, `TEST_DB_PORT`, `TEST_DB_USER`, and `TEST_DB_PASSWORD` for a local, disposable database whose name contains `test`. They drop every table in it.

## Status and limits

This is unfinished work. The backend tests cover access control and recent fixes, not every behavior, and the frontend has no tests. `npm run build` passes, and `npm run lint` reports 4 errors.

**Security: do not put real users on this yet.** Access control is in place, as described in [Access rules](#access-rules). It has only run locally, and these gaps remain:

- **No login protection.** Nothing limits login attempts, email addresses are not verified, and sign-up errors and login timing reveal whether an email is registered.
- **Weak password rules.** Passwords are stored as bcrypt hashes, but there is no minimum length, and bcrypt ignores everything after 72 bytes.
- **Uploaded files have direct links.** Submission links, and the `gcs_url` that course file responses include, point straight at the bucket. If the bucket is public, anyone with a link can open the file without a session.
- **Uploads have no limits.** Any logged-in user can upload a file of any type or size, and the server reads an upload's body before it checks the session.
- **Sessions end one at a time.** Logging out ends only the current session, so other devices stay logged in until they expire.
- **Cover images are not checked per course.** Any logged-in user can load a cover through `/proxy-image`, including one from a draft course, if they know its URL.

**What needs Google Cloud.** These features were not tested with a real bucket, because the local runs had none:

- course file uploads, cover images, and assignment submissions, which all upload a file first
- cover images on seeded courses, which do not load unless the bucket holds them

**Known bugs and gaps.**

- Deleting a course removes its database rows but leaves its uploaded files in the bucket.
- The triggers use MySQL syntax, so other databases such as SQLite will not work.
- A `Dockerfile` for Cloud Run is included, but that deployment path was not tested.
- Students can submit work, but teachers cannot see submissions or grade them. The API has no route for either.
- There is no password change or reset.
