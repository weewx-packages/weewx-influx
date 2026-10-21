# Repair validation

Version 0.21.0. Original repository and revision are in ORIGIN.md.

* https://github.com/matthewwall/weewx-influx/pull/36: Removed distutils, added numeric/prerelease-aware gate; measured import and regression tests.
* https://github.com/matthewwall/weewx-influx/issues/35: Imports on Python 3.14 without distutils.
* https://github.com/matthewwall/weewx-influx/pull/34: Native v1/v2 endpoint selection, encoded org/bucket, token authentication; v1 remains supported. Tested against actual InfluxDB 1.8 and 2.7 with readback.
* https://github.com/matthewwall/weewx-influx/issues/33: backfill.py reads wx_binding through WeeWX manager and replays original record timestamps within explicit bounds; stops on upload failure.
* https://github.com/matthewwall/weewx-influx/issues/32: Version 2 configuration uses full server_url, org, bucket and token. Existing bucket required. Real v2 write/readback passed; original account permissions not tested.
* https://github.com/matthewwall/weewx-influx/pull/31: Token authentication implemented alongside v1 Basic authentication; loop_bucket supported without replacing v1.
* https://github.com/matthewwall/weewx-influx/pull/30: README converted to Markdown and updated for WeeWX 5, dual backends and replay. Original attribution retained.
* https://github.com/matthewwall/weewx-influx/issues/28: Native Token authentication implemented and observed on local HTTP wire.
* https://github.com/matthewwall/weewx-influx/issues/26: CREATE DATABASE quotes/escapes identifiers, uses actual admin credentials, and URL-encodes database on write. Real hyphenated v1 database write/readback passed.
* https://github.com/matthewwall/weewx-influx/issues/25: Database creation is POST /query; records POST /write or /api/v2/write. 405 is reported as permanent endpoint error. Reporter endpoint/proxy needs its response/config to diagnose specifically.
* https://github.com/matthewwall/weewx-influx/issues/24: Real server readback confirms record measurement, original timestamp, binding and field. Documented matching query bucket/database, measurement and range. Reporter server configuration not available.
* https://github.com/matthewwall/weewx-influx/issues/14: Bounded WeeWX archive replay added; original timestamps retained.
* https://github.com/matthewwall/weewx-influx/issues/13: Configurable data_binding selects kl_binding; real service/queue test verifies custom temp0 and humidity0 values reach the local HTTP receiver. backfill --binding supports custom archives. Original hardware is not required for this reproduced binding case.
* https://github.com/matthewwall/weewx-influx/issues/6: ConfigObj tag lists are joined, including direct thread construction; station=A,field=C observed on the wire. Existing service had already joined list tags.
* https://github.com/matthewwall/weewx-influx/issues/1: TLS verifies certificate and hostname by default; ca_file and explicit verify_ssl option. Real local TLS rejects untrusted CA and accepts configured CA.

Tests run under WeeWX 4.10.2/5.1.0 on Python 3.10 and WeeWX 5.5.2 on Python 3.14. Local receivers and isolated install directories avoid live station changes. The tests do not establish individual external account permissions.
