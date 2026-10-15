"""The app `run-app-tunnel-probe`: one query against the office database over the tunnel (hub design 10.1).

The container is a one-shot sandbox: the entrypoint brings the tunnel up, runs this once and exits
with its code. It reads the SQL Server login from `persisted_data/sql_login.json` (`UID`, `PWD`,
`port`; copied onto the VPS by hand, never in the image or the repo), selects all of
`FasTraxWarehouse.dbo.iteminformation` from the database PC at its tunnel address through Microsoft
ODBC Driver 18, and writes it to `persisted_data/iteminformation.csv`. Any failure exits 1.
"""

# Standard library imports
import csv
import json
import sys
import time
from pathlib import Path

# Third party imports
import pyodbc

PERSISTED = Path("/app/persisted_data")
SERVER = "10.8.0.10"  # office-db-pc's tunnel address
DATABASE = "FasTraxWarehouse"
QUERY = "SELECT * FROM dbo.iteminformation"
BATCH = 5000


def write_csv(cursor: pyodbc.Cursor, path: Path) -> int:
  """Write *cursor*'s columns and remaining rows to *path* as UTF-8 CSV with a BOM; return the row count.

  Rows are fetched `BATCH` at a time. The file is written beside *path* and renamed over it at the
  end, so a failure leaves any previous CSV in place and no partial one. NULL is written empty,
  binary values as hex; the BOM is for Excel.
  """
  tmp = path.with_name(f"{path.name}.tmp")
  count = 0
  try:
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
      out = csv.writer(f)
      out.writerow(column[0] for column in cursor.description)
      while rows := cursor.fetchmany(BATCH):
        out.writerows([v.hex() if isinstance(v, bytes | bytearray) else v for v in row] for row in rows)
        count += len(rows)
    tmp.replace(path)
  except BaseException:
    tmp.unlink(missing_ok=True)
    raise
  return count


def run_app() -> None:
  """Query the table over the tunnel and write it to the CSV; a bad login file exits naming it, never its values."""
  login_file = PERSISTED / "sql_login.json"
  try:
    login = json.loads(login_file.read_text(encoding="utf-8-sig"))
    uid, pwd, port = str(login["UID"]), str(login["PWD"]), int(login["port"])
  except FileNotFoundError:
    sys.exit(f"tunnel-probe: {login_file} is missing; copy sql_login.json into the persisted data folder")
  except KeyError as e:
    sys.exit(f"tunnel-probe: {login_file} has no {e.args[0]!r}; it needs UID, PWD and port")
  except ValueError, TypeError:  # bad JSON (JSONDecodeError is a ValueError), not an object, or a non-numeric port
    sys.exit(f"tunnel-probe: {login_file} is not a JSON object with UID, PWD and a numeric port")

  # A braced value may hold ';', and a '}' inside one is doubled. The tunnel already encrypts the
  # path and the PC's certificate is self-signed, hence TrustServerCertificate.
  uid, pwd = ("{" + v.replace("}", "}}") + "}" for v in (uid, pwd))
  conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER},{port};DATABASE={DATABASE};"
    f"UID={uid};PWD={pwd};Encrypt=yes;TrustServerCertificate=yes"
  )
  start = time.monotonic()
  conn = pyodbc.connect(conn_str, timeout=15)
  try:
    cursor = conn.cursor()
    cursor.execute(QUERY)
    path = PERSISTED / "iteminformation.csv"
    count = write_csv(cursor, path)
  finally:
    conn.close()
  print(
    f"tunnel-probe: wrote {count} rows of {DATABASE}.dbo.iteminformation to {path} in {time.monotonic() - start:.1f} s",
    file=sys.stderr,
  )


if __name__ == "__main__":
  run_app()
