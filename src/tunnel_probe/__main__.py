"""The app `run-app-tunnel-probe`: a placeholder that exits 0 (hub design 10.1).

The container is a one-shot sandbox: the entrypoint brings the tunnel up, runs this once and
exits with its code. Replace the body by hand with the smoke test to run over the tunnel.
"""

# Standard library imports
import sys


def run_app() -> None:
  """Print one line and return; the entrypoint exits 0 after it."""
  print("tunnel-probe: the tunnel is up and the sandbox ran; nothing to probe yet", file=sys.stderr)


if __name__ == "__main__":
  run_app()
