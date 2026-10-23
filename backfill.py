#!/usr/bin/env python3
# Modified 2026-10-22 by weewx-packages: add bounded archive replay.
# Modified 2026-10-23 by weewx-packages: check unit_system and unknown options
# like the service does.
# Distributed under the terms of the GNU Public License (GPLv3)
"""Replay a WeeWX archive through the configured Influx writer."""

import argparse
import pathlib
import queue
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'bin/user'))

import weecfg
import weewx.manager
import influx


def replay(worker, records, dbm=None):
    """Send archive records in order, stopping on the first failed upload.

    Args:
        worker (influx.InfluxThread): Configured destination writer.
        records (Iterable[dict]): Archive records to upload.
        dbm (weewx.manager.Manager|None): Optional archive used for rain totals.

    Returns:
        int: Number of uploaded records.
    """
    count = 0
    for record in records:
        payload = dict(record, binding='archive')
        worker.process_record(payload, dbm)
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--binding', help='Archive binding, defaults to Influx data_binding or wx_binding')
    parser.add_argument('--start', type=int, help='Exclusive start Unix timestamp')
    parser.add_argument('--stop', type=int, help='Inclusive end Unix timestamp')
    args = parser.parse_args()
    if args.start is not None and args.stop is not None and args.start >= args.stop:
        parser.error('--start must precede --stop')
    _, config = weecfg.read_config(args.config)
    options = weewx.restx.get_site_dict(config, 'Influx')
    if options is None:
        parser.error('Influx is disabled or missing in this configuration')
    options.pop('binding', None)
    configured_binding = options.pop('data_binding', 'wx_binding')
    data_binding = args.binding or configured_binding
    host = options.pop('host', 'localhost')
    port = int(options.pop('port', 8086))
    options.setdefault('server_url', 'http://%s:%d' % (host, port))
    if 'unit_system' in options:
        unit_system = influx.get_unit_system(options['unit_system'])
        if unit_system is None:
            parser.error("unknown unit_system '%s'. Use US, METRIC or METRICWX"
                         % options['unit_system'])
        options['unit_system'] = unit_system
    options['inputs'] = dict(config['StdRESTful']['Influx'].get('inputs', {}))
    influx.drop_unknown_options(options)
    worker = influx.InfluxThread(queue.Queue(), **options)
    with weewx.manager.open_manager_with_config(config, data_binding) as dbm:
        count = replay(worker, dbm.genBatchRecords(args.start, args.stop), dbm)
    print('Uploaded %d archive records' % count)


if __name__ == '__main__':
    main()
