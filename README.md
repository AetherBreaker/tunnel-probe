# tunnel-probe

The test spoke of the WireGuard tunnel (`10.8.0.21`): a devkit-managed container in fetched mode and a one-shot sandbox. Each deploy brings the tunnel up, runs the app once and exits. Its app is a placeholder, replaced by hand with whatever smoke test should run over the tunnel from inside Coolify.

Its next job is the database: it is where the Python connect-and-query workflow is tested against the office MSSQL database over the tunnel, outside production, before ScheduledReportAggregator's jobs query it. That work, and the decisions it waits on (port, login, driver, the hub's flow line for `10.8.0.21`), are ScheduledReportAggregator's `docs/office-database-access.md`.

The tunnel's overall design is wireguard-hub's `docs/superpowers/specs/2026-09-14-hub-fetched-peer-config-design.md`; this project is in its sections 10.1 and 11.
