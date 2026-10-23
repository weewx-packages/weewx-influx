# Influx uploader configuration reference

These options belong under `[StdRESTful] [[Influx]]` in `weewx.conf`. The
connection settings and the full option list with defaults are in
[the README](../README.md#configuration).

## Input map

Set `obs_to_upload = none` to limit output to the input map. With `most` or
`all`, entries override names, units and formats while other observations remain
eligible.

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

Each entry accepts `name`, `units` and `format`. `units` takes a WeeWX unit
name, such as `mile_per_hour`, not `mph`. Custom numeric observations use their
registered WeeWX units when converted. If an observation cannot be converted to
`units`, it is left out of every upload and a warning is logged once.

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

Times are the original record's Unix seconds multiplied by one billion. The
InfluxDB 2 endpoint specifies nanosecond precision explicitly.
