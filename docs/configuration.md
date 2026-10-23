# Influx uploader configuration reference

For installation and a working v1 or v2 connection, see [the README](../README.md).
These options belong under `[StdRESTful] [[Influx]]` in `weewx.conf`.

| Option | Meaning and default |
| --- | --- |
| version | API generation, `1` or `2`; default `1` |
| server_url | Base URL with `http://` or `https://`; overrides host/port |
| host, port | Used when server_url is absent; defaults localhost and 8086 |
| database | Required v1 database name |
| username, password | Optional v1 Basic authentication |
| create_database | Attempt v1 database creation at startup; default true |
| dbadmin_username, dbadmin_password | Optional credentials for v1 creation |
| org, bucket, token | Required v2 organization, bucket and write token |
| loop_bucket | v2 bucket for LOOP data; defaults to bucket |
| binding | loop, archive, or both; default archive |
| data_binding | Archive binding for augmentation; default wx_binding |
| measurement | Base measurement name; default record |
| tags | Comma-separated name=value tags; default none |
| line_format | single-line, multi-line, multi-line-dotted; default single-line |
| obs_to_upload | most, all or none; default most |
| append_units_label | Append unit suffixes to generated field names; default true |
| unit_system | US, METRIC or METRICWX; absent means source units |
| augment_record | Add archive-derived weather values; default true |
| verify_ssl | Verify TLS certificates and hostname; default true |
| ca_file | Optional private CA file |
| skip_upload | Skip uploads; default false |

The worker also accepts WeeWX REST options `post_interval`, `max_backlog`,
`stale`, `log_success`, `log_failure`, `timeout`, `max_tries` and `retry_wait`.
The constructor in [influx.py](../bin/user/influx.py) defines their defaults.

## Input map

Set `obs_to_upload = none` to limit output to the input map. With `most` or
`all`, entries override names, units and formats while other observations remain
eligible. `most` omits dateTime, interval and usUnits. Non-numeric, missing and
non-finite readings are skipped.

```ini
[StdRESTful]
    [[Influx]]
        server_url = http://localhost:8086
        database = weather
        create_database = false
        tags = station=A
        obs_to_upload = none
        [[[inputs]]]
            [[[[barometer]]]]
                units = inHg
                name = barometer_inHg
                format = %.3f
            [[[[outTemp]]]]
                units = degree_F
                name = outTemp_F
                format = %.1f
            [[[[outHumidity]]]]
                name = outHumidity
                format = %03.0f
            [[[[windSpeed]]]]
                units = mile_per_hour
                name = windSpeed_mph
                format = %.2f
            [[[[windDir]]]]
                format = %03.0f
```

Custom numeric observations use their registered WeeWX units when converted.
Choose names and tag values without spaces or line-protocol delimiter characters;
the uploader interpolates them into the payload.

## Line layouts

For `measurement = weewx`, fields `name0`, `name1`, and tag `station=A`,
`single-line` places the observations in fields of one measurement:

```text
weewx,binding=archive,station=A name0=12.3,name1=45.6 1700000000000000000
```

`multi-line` uses one measurement per observation:

```text
name0,binding=archive,station=A value=12.3 1700000000000000000
name1,binding=archive,station=A value=45.6 1700000000000000000
```

`multi-line-dotted` prefixes each measurement with the base name:

```text
weewx.name0,binding=archive,station=A value=12.3 1700000000000000000
weewx.name1,binding=archive,station=A value=45.6 1700000000000000000
```

The service adds a `binding=loop` or `binding=archive` tag. Times are the original
record's Unix seconds multiplied by one billion. The v2 endpoint specifies
nanosecond precision explicitly. InfluxDB retention and queries determine which
historical values remain visible.
