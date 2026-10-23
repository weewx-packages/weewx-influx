# InfluxDB uploader for WeeWX

Write numeric weather observations with their original timestamps using InfluxDB
line protocol. The service supports InfluxDB v1 database writes and v2
organization/bucket writes, with archive or LOOP bindings.

This is the weewx-packages continuation, release **0.21.1**.
[Origin](ORIGIN.md) records the upstream revision; [repair notes](REPAIR_NOTES.md)
describe the maintenance changes.

The catalog archive targets WeeWX `>=5.5.2,<5.7` and Python `>=3.10,<3.15`.

## Install

Use `weectl` from the Python environment running WeeWX. With stock WeeWX 5,
install the published archive:

```sh
weectl extension install https://github.com/weewx-packages/weewx-influx/releases/download/v0.21.1/weewx-influx-0.21.1.tar.gz --config /path/to/weewx.conf
```

Replace `/path/to/weewx.conf` with your station configuration. You can also
download that URL and pass the local archive to the same command. Use elevated
permissions only when your station files require them.

## Connect to InfluxDB

You need an InfluxDB endpoint and credentials with write permission. The runtime
uses WeeWX and Python's standard library, without an Influx client package.
The installer registers `user.influx.Influx`. Configure one of these destinations
in `weewx.conf`.

For InfluxDB v1:

```ini
[StdRESTful]
    [[Influx]]
        server_url = http://localhost:8086
        database = weather
        create_database = false
```

Create `weather` on the server first for this example. Add `username` and
`password` if authentication is enabled. With `create_database = true`, the
worker attempts database creation at startup, using `dbadmin_username` and
`dbadmin_password` if supplied, otherwise the write credentials.

For InfluxDB v2:

```ini
[StdRESTful]
    [[Influx]]
        version = 2
        server_url = https://influx.example.com:8086
        org = weather
        bucket = archive
        token = YOUR_WRITE_TOKEN
        binding = archive
```

Create the organization, bucket and token in InfluxDB before starting WeeWX.
The v2 writer uses `/api/v2/write` and does not create buckets. The installer's
v1 `host`/`database` placeholders can be removed when using this v2 section.
`server_url` overrides `host` and `port`.

Restart WeeWX yourself. A successful write returns HTTP 204. Query the
configured database or bucket, the default `record` measurement and the record's
original time range. TLS certificates and hostnames are verified by default;
`ca_file` selects a private CA. A 401/403 indicates access failure. Check the
endpoint and response body for 404/405 errors.

## Select observations and storage layout

`binding` defaults to `archive`; `loop` or `loop, archive` also work.
`loop_bucket` can route LOOP records to a separate v2 bucket. `data_binding`
selects the archive used for augmentation, default `wx_binding`; non-weather
archives can select their own binding.

By default, numeric observations retain their source units and receive unit
suffixes. Metadata fields `dateTime`, `interval` and `usUnits` are excluded by
`obs_to_upload = most`. Set `obs_to_upload = none` with an `inputs` map to send
only named observations. An input map alone overrides names, units and formats
while retaining the other observations.

The [configuration reference](docs/configuration.md) covers tags, input maps,
unit conversion and the `single-line`, `multi-line` and `multi-line-dotted`
layouts. These choices affect measurement and field names; choose them before
building dashboards. Values must be numeric and finite.

## Replay historical records

Use [backfill.py](backfill.py) from this checkout with WeeWX's Python environment.
It is a checkout tool, not a module installed by the extension installer.
Stop concurrent WeeWX uploads to the same measurements during replay.

```sh
python backfill.py --config /path/to/weewx.conf --start 1600000000 --stop 1700000000
```

Start is exclusive and stop inclusive, both Unix seconds. `--binding kl_binding`
selects another archive; otherwise the tool uses `data_binding` or `wx_binding`.
It reads the archive without changing it and stops at the first upload failure.
Repeating a range uses the same measurement/tag/timestamp keys, subject to
InfluxDB field-merge rules. There is no automatic historical upload on install.

## Origin and license

Copyright 2016-2021 Matthew Wall. [GNU GPLv3](license).
The continuation preserves v1 and adds v2 support and bounded replay. Related
work reviewed for these changes includes `david-lutz/weewx-influx2` and upstream
PRs #31, #34 and #30. The [repair notes](REPAIR_NOTES.md) retain validation and
attribution details. Modified 2026-10-22 by weewx-packages.
