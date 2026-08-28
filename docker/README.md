# Local Spark cluster + Postgres (Docker)

Local development infrastructure for the pipeline: a minimal Spark
standalone cluster (one master + one worker, via
`apache/spark:4.2.0-python3`, matching the `pyspark==4.2.0` pin in
`requirements.txt`) plus a Postgres container (`postgres:18`) that's the
pipeline's persistent data store.

The official `apache/spark` image is used so the driver (host) and cluster
(containers) run the exact same Spark version.

Sized for a 6GB-RAM-capped WSL2 environment: the Spark worker is capped at
2GB / 2 cores, the master at 1GB / 1 core, and Postgres at 512MB / 1 core
(all enforced by Docker via `mem_limit`/`cpus`), leaving headroom for the
OS, VS Code server, and a local Jupyter kernel/PySpark driver process
running alongside the cluster.

## One-time setup

Before first run, create a `docker/.env` file (gitignored -- every clone
sets its own) from the `.env.example` template in this directory:

```bash
cp .env.example .env
```

Then, from this `docker/` directory, fill in `PROJECT_ROOT`/`UID`/`GID`
automatically:

```bash
printf 'PROJECT_ROOT=%s\nUID=%s\nGID=%s\n' "$(cd .. && pwd)" "$(id -u)" "$(id -g)" >> .env
```

(That appends to the `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` lines
already copied from `.env.example` -- edit `.env` directly afterward if you
want different Postgres credentials than the template's defaults.)

See `.env.example` for what each value means:

- `PROJECT_ROOT` has to match what `src/pipeline.py` (and `src/extract.py`)
  compute for themselves at runtime (`Path(__file__).resolve().parent.parent`)
  -- see the comment block at the top of `docker-compose.yml` for why that
  matters.
- `UID`/`GID` run the Spark containers as *you*, so files the driver
  (host) and executors (containers) create under `data/` don't clash on
  ownership/permissions -- see the comment block at the top of
  `docker-compose.yml` for the specific failure this avoids. This is why
  there's no separate `chmod -R o+w data/processed` step here anymore:
  once the containers run as your uid, they already have the same write
  access to `data/` that you do.
- `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` are the credentials the
  official `postgres` image uses to create the database/user on first
  startup -- see the Postgres section below.

The pipeline itself (not Docker Compose) also needs its own `.env`, at the
**project root** (not this `docker/` directory) -- see the project root's
`.env.example`. `POSTGRES_DB`/`USER`/`PASSWORD` there must match
`docker/.env`'s values exactly, since that's what the container was
actually initialized with:

```bash
cp ../.env.example ../.env
```

**Also required, one-time, host-level (not captured in any repo file):**
add a `/etc/hosts` entry mapping `postgres` to your own loopback address:

```bash
echo '127.0.0.1 postgres' | sudo tee -a /etc/hosts
```

Why this is needed: `src/load.py`'s Postgres write uses the hostname
`postgres` (matching `POSTGRES_HOST` in `.env.example`) so it resolves
correctly from *inside* the Docker network, where the actual per-partition
JDBC inserts run (in the `spark-worker` container -- see that file's
docstring for why). But Spark's driver process runs locally on your host
(client deploy mode, same as everywhere else in this project) and ALSO
needs a working connection to Postgres itself, for a table-existence/
truncate check that happens before any executor work starts. Bare host
processes don't get Docker's internal DNS, so `postgres` doesn't resolve
there by default -- the `/etc/hosts` entry above makes it resolve to your
own loopback instead, which reaches Postgres via the container's published
port (`5432:5432`). Every clone of this repo needs to add this once; it
can't be automated via any file this project controls.

## Start the cluster

From this `docker/` directory (matters both so the `../data` bind-mount
source resolves correctly and so Docker Compose picks up the `.env` file
above, which it only auto-loads from the current working directory):

```bash
docker compose up -d
```

`-d` runs it in the background. Omit it to watch the logs in your terminal
(useful the first time, to confirm both containers start cleanly).

## Confirm it's running

Open the Spark Master web UI: **http://localhost:8080**

You should see:
- **Status: ALIVE** near the top
- One entry under **Workers** (State: ALIVE), with ~2.0 GB memory and 2 cores
  listed as available

You can also check container status directly:

```bash
docker compose ps
```

All three containers should show as running, and `postgres` specifically
should report `(healthy)` once its startup checks (`pg_isready`, configured
in `docker-compose.yml`) pass.

Once a job is running (e.g. from a local PySpark session connecting to
`spark://localhost:7077`), its DAG/stage UI is available at
**http://localhost:4040** for the duration of that job.

## Postgres

On first startup against an empty `postgres-data` volume, the official
`postgres` image's entrypoint automatically creates the database/user (from
`docker/.env`) and then runs every `.sql` file under `docker/init/` --
i.e. `docker compose up` alone auto-creates the `courses` and
`player_season_stats` tables (and their indexes) from `schema.sql`, with no
separate migration step needed.

To connect for manual inspection/debugging, either from the host with
`psql` installed:

```bash
psql -h localhost -U <POSTGRES_USER> -d <POSTGRES_DB>
```

or via `docker exec` (no local `psql` install needed -- runs `psql` inside
the container itself):

```bash
docker exec -it postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

Either way, you'll be prompted for `POSTGRES_PASSWORD` from `docker/.env`.
Once connected, `\dt` lists tables (you should see `courses` and
`player_season_stats`), and `\d <table>` shows a table's columns.

**If `schema.sql` changes later**, `docker-entrypoint-initdb.d` scripts only
run against a genuinely empty data directory -- they will NOT re-run just
because you edited `schema.sql` and restarted the container, since
`postgres-data` (the named volume) already has data in it by then. To force
a re-run and pick up schema changes:

```bash
docker compose down -v
docker compose up -d
```

The `-v` removes the named volumes (including `postgres-data`), not just
the containers -- this deletes any data already loaded into Postgres, so
only do this in local dev, and re-run `python src/pipeline.py` afterward to
repopulate the tables.

## Stop the cluster

```bash
docker compose down
```

This stops and removes the containers (but not the images or named
volumes). Data written under this project's `data/` directory persists on
the host (it's a bind mount, not a container volume), and Postgres's data
persists in the `postgres-data` named volume -- add `-v` to also remove
that volume (see "If schema.sql changes later" above).

## Notes

- The `../data` directory is bind-mounted into both containers at the SAME
  absolute path it lives at on the host (`${PROJECT_ROOT}/data`, from
  `docker/.env`), not remapped to a container-only path. This matters
  because a PySpark driver connecting in client deploy mode (as
  `src/pipeline.py` does) resolves `spark.read`/`spark.write` paths on its
  OWN local filesystem -- since the driver runs locally on the host, that
  path has to exist there too, not just inside the containers.
  `src/pipeline.py` and `src/extract.py` each derive that same path
  independently at runtime (via `Path(__file__).resolve().parent.parent`),
  so as long as `docker/.env`'s `PROJECT_ROOT` is set correctly (see
  One-time setup above), all three agree automatically -- nothing
  machine-specific is hardcoded in any of them.
- Both services also set `user: "${UID}:${GID}"` (from `docker/.env`), so
  the containers run as your host user rather than the image's baked-in
  uid. `spark.write` with `mode("overwrite")` deletes and recreates its
  output directory on every run -- the driver (host, your uid) creates the
  top-level directory, and the executor (container) then has to create
  files inside it. Matching uids means that always works; mismatched uids
  fail with a `Mkdirs failed` permission error on every write, not just the
  first one, since `chmod` doesn't stick across `overwrite` recreating the
  directory.
- `python src/pipeline.py` writes `player_season_stats` and `courses` to
  this Postgres container as its last step, via Spark's JDBC writer
  (`src/load.py`'s `write_to_postgres()`). The Postgres JDBC driver itself
  doesn't need manual installation -- `src/pipeline.py`'s
  `build_spark_session()` configures `spark.jars.packages` with the driver
  coordinate, so Spark downloads (and caches) it automatically. See the
  `/etc/hosts` requirement above -- the pipeline's Postgres write will fail
  with a hostname resolution error without it.
