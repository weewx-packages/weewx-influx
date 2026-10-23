# InfluxDB uploader for WeeWX

Writes numeric WeeWX observations with their original timestamps to InfluxDB
using line protocol. It supports InfluxDB 1 database writes and InfluxDB 2
organization and bucket writes, for archive records, LOOP packets or both.

This is the weewx-packages continuation of
[matthewwall/weewx-influx](https://github.com/matthewwall/weewx-influx). It
adds InfluxDB 2 writes and archive replay. See [ORIGIN.md](ORIGIN.md) and
[REPAIR_NOTES.md](REPAIR_NOTES.md).

## Requirements

- An InfluxDB 1 server with a database, or an InfluxDB 2 server with an
  organization, a bucket and a token with write permission.
- No Python packages beyond WeeWX and the standard library. The uploader does
  not use an InfluxDB client library.

## Installation

Install `influx` from the [WeeWX packages catalog](https://github.com/weewx-packages/catalog/blob/main/packages/influx.md).
The catalog page lists the current release, its WeeWX and Python
requirements, and the install, update and removal commands.

The installer adds `user.influx.Influx` to `restful_services` and writes an
`[[Influx]]` section with the placeholders `INSERT_HOST_HERE` and
`INSERT_DATABASE_HERE`. Replace them with one of the configurations below,
then restart WeeWX.

The installer does not upload existing archive records. To replay them, run
[backfill.py](backfill.py) from a checkout of this repository with the Python
of your WeeWX installation:

```sh
python backfill.py --config /path/to/weewx.conf --start 1600000000 --stop 1700000000
```

`--start` is exclusive and `--stop` inclusive, both in Unix seconds. Without
them the tool replays from the first or up to the last record. `--binding`
selects another archive, otherwise the tool uses `data_binding`. It reads the
archive without changing it and stops at the first failed upload. Stop WeeWX
uploads to the same measurements while it runs. Replaying a range again
writes the same measurement, tag and timestamp keys, so InfluxDB merges the
fields.

## Configuration

InfluxDB 1:

```ini
[StdRESTful]
    [[Influx]]
        server_url = http://localhost:8086
        database = weather
        create_database = false
```

Create the database first, or leave `create_database` at its default. Add
`username` and `password` if the server requires authentication.

InfluxDB 2:

```ini
[StdRESTful]
    [[Influx]]
        version = 2
        server_url = https://influx.example.com:8086
        org = weather
        bucket = archive
        token = YOUR_WRITE_TOKEN
```

Create the organization, bucket and token before starting WeeWX. The uploader
writes to `/api/v2/write` and does not create buckets.

After the next archive record, query the database or bucket for the
measurement `record` over the record's time range. A successful write returns
HTTP 204. HTTP 401 or 403 means the credentials were refused. On 404 or 405,
check the endpoint and the response body in the log.

| Option | Default | Meaning |
|---|---|---|
| `version` | `1` | InfluxDB API, `1` or `2`. |
| `server_url` | `http://<host>:<port>` | Base URL with `http://` or `https://`. Overrides `host` and `port`. |
| `host` | `localhost` | Server host when `server_url` is absent. |
| `port` | `8086` | Server port when `server_url` is absent. |
| `database` | none | InfluxDB 1 database. Required for version 1. |
| `username`, `password` | none | InfluxDB 1 Basic authentication. Sent only when both are set. |
| `create_database` | `True` | InfluxDB 1: create the database at startup. A failure is logged. |
| `dbadmin_username`, `dbadmin_password` | none | Credentials for creating the database. Without them the write credentials are used. |
| `org`, `bucket`, `token` | none | InfluxDB 2 organization, bucket and token. Required for version 2. |
| `loop_bucket` | `bucket` | InfluxDB 2 bucket for LOOP packets. |
| `binding` | `archive` | `archive`, `loop`, or `loop, archive`. |
| `data_binding` | `wx_binding` | Archive used to add rain totals. |
| `augment_record` | `True` | Add `hourRain`, `rain24` and `dayRain` from the archive. |
| `measurement` | `record` | Measurement name, or the prefix in `multi-line-dotted`. |
| `tags` | none | Comma-separated `name=value` tags. |
| `line_format` | `single-line` | `single-line`, `multi-line` or `multi-line-dotted`. |
| `obs_to_upload` | `most` | `most` skips `dateTime`, `interval` and `usUnits`. `all` sends every field. `none` sends only the input map. |
| `append_units_label` | `True` | Append a unit suffix to field names, such as `outTemp_F`. |
| `unit_system` | none | Convert to `US`, `METRIC` or `METRICWX`. Without it, the source units are sent. |
| `verify_ssl` | `True` | Verify the TLS certificate and host name. |
| `ca_file` | none | CA file for a private certificate authority. |
| `skip_upload` | `False` | Build the payload but do not send it. |
| `post_interval` | none | Minimum seconds between two uploaded records. |
| `max_backlog` | `1000000` | Queue length before old records are dropped. |
| `stale` | none | Records older than this many seconds are skipped. |
| `timeout` | `60` | HTTP timeout in seconds. |
| `max_tries` | `3` | Attempts per record. |
| `retry_wait` | `5` | Seconds between attempts. |
| `log_success`, `log_failure` | `True` | Log successful and failed uploads. |

The service adds a `binding=archive` or `binding=loop` tag to every point.
Non-numeric, missing and non-finite values are skipped. Line layouts and the
input map for renaming, converting and formatting single observations are
described in the [configuration reference](docs/configuration.md). The layout
decides measurement and field names, so choose it before building dashboards.

## Limitations

- A missing `database` for version 1, missing `org`, `bucket` or `token` for
  version 2, a `server_url` without `http://` or `https://`, or an option
  that is neither in the table nor `enable` stop WeeWX at startup.
- `unit_system` accepts only `US`, `METRIC` and `METRICWX` in capitals. Any
  other value ends the upload thread at the first record.
- Measurement, tag and field names are written into the line protocol
  without escaping. Do not use spaces, commas or `=` in them.
- Which history stays visible depends on InfluxDB retention.

## Development

```sh
python -m pytest -q tests
```

Run the tests in an environment with WeeWX and pytest.

## License

Copyright 2016-2021 Matthew Wall. Distributed under the terms of the
[GNU General Public License, version 3](license).

The InfluxDB 2 changes draw on `david-lutz/weewx-influx2` and the upstream
pull requests #30, #31 and #34. [REPAIR_NOTES.md](REPAIR_NOTES.md) keeps the
validation and attribution details.

Modified 2026-10-23 by weewx-packages.
