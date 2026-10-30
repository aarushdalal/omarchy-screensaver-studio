"""Daily disk deltas and non-interactive NVMe SMART readings."""
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile


class DailyIOTracker:
    """Persist daily observations without treating counters since boot as lifetime data."""
    def __init__(self, path=None, interval=30):
        self.path = Path(path) if path else Path.home() / '.config/omarchy-screensaver/daily-io.json'
        self.interval = interval
        self.boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        self.boot_at = None
        try:
            for line in Path('/proc/stat').read_text().splitlines():
                if line.startswith('btime '):
                    self.boot_at = dt.datetime.fromtimestamp(int(line.split()[1])).astimezone()
                    break
        except OSError:
            pass

    def observe(self, device, read_bytes, write_bytes, now=None, boot_id=None, boot_at=None):
        now = now or dt.datetime.now().astimezone()
        boot_id = boot_id or self.boot_id
        boot_at = boot_at or self.boot_at
        day, stamp = now.date().isoformat(), now.timestamp()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with (self.path.with_suffix('.lock')).open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                state = json.loads(self.path.read_text())
            except (OSError, ValueError):
                state = {}
            old = state.get('devices', {}).get(device) if state.get('date') == day else None
            if not isinstance(old, dict):
                bootstrap = boot_at is not None and boot_at.date() == now.date()
                record = {'read': int(read_bytes) if bootstrap else 0,
                          'write': int(write_bytes) if bootstrap else 0,
                          'partial': True, 'since': (boot_at if bootstrap else now).isoformat()}
            else:
                if stamp <= old.get('sampled_at', 0):
                    return old
                reboot = old.get('boot_id') != boot_id
                record = dict(old)
                for key, counter in [('read', read_bytes), ('write', write_bytes)]:
                    previous = old.get('last_' + key, counter)
                    delta = int(counter) if reboot or counter < previous else int(counter - previous)
                    record[key] = int(old.get(key, 0)) + max(0, delta)
                if reboot:
                    record['partial'] = True
            record.update(boot_id=boot_id, last_read=int(read_bytes), last_write=int(write_bytes), sampled_at=stamp)
            if old is None or old.get('boot_id') != boot_id or stamp - old.get('sampled_at', 0) >= self.interval:
                if state.get('date') != day:
                    state = {'version': 1, 'date': day, 'devices': {}}
                state.setdefault('devices', {})[device] = record
                with tempfile.NamedTemporaryFile('w', dir=self.path.parent, prefix='.daily-io-', delete=False) as stream:
                    json.dump(state, stream)
                    temporary = stream.name
                os.replace(temporary, self.path)
            return record


def nvme_smart(device):
    """Use the existing UDisks daemon; never prompt for privileges in a screensaver."""
    from gi.repository import Gio, GLib
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    objects = bus.call_sync('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2',
        'org.freedesktop.DBus.ObjectManager', 'GetManagedObjects', None, None,
        Gio.DBusCallFlags.NONE, 2500, None).unpack()[0]
    block = objects.get('/org/freedesktop/UDisks2/block_devices/' + device, {})
    drive = block.get('org.freedesktop.UDisks2.Block', {}).get('Drive')
    controller = objects.get(drive, {}).get('org.freedesktop.UDisks2.NVMe.Controller')
    if controller is None:
        return {}
    options = GLib.Variant('(a{sv})', ({'auth.no_user_interaction': GLib.Variant('b', True)},))
    try:
        bus.call_sync('org.freedesktop.UDisks2', drive, 'org.freedesktop.UDisks2.NVMe.Controller',
                      'SmartUpdate', options, None, Gio.DBusCallFlags.NONE, 2500, None)
    except GLib.Error:
        pass
    attrs = bus.call_sync('org.freedesktop.UDisks2', drive, 'org.freedesktop.UDisks2.NVMe.Controller',
        'SmartGetAttributes', options, None, Gio.DBusCallFlags.NONE, 2500, None).unpack()[0]
    result = decode_nvme_attributes(attrs)
    try:
        snapshot = json.loads((Path.home() / '.config/omarchy-screensaver/smart-cache.json').read_text())
        if snapshot.get('device') == device:
            for key in ('read_commands', 'write_commands', 'updated_at'):
                result[key] = snapshot.get(key)
    except (OSError, ValueError, TypeError):
        pass
    # Optional direct SMART access can expose command counts omitted by UDisks.
    # This is always non-interactive and unprivileged; unavailable counts stay N/A.
    binary = shutil.which('smartctl')
    if binary:
        reply = subprocess.run([binary, '-a', '-j', '/dev/' + device], capture_output=True, text=True, timeout=3)
        try:
            info = json.loads(reply.stdout).get('nvme_smart_health_information_log', {})
            reads, writes = info.get('host_reads'), info.get('host_writes')
            if reads is not None and writes is not None:
                result['read_commands'], result['write_commands'] = int(reads), int(writes)
        except (ValueError, TypeError):
            pass
    return result


def decode_nvme_attributes(attrs):
    used = attrs.get('percent_used')
    return {'read_bytes': attrs.get('total_data_read'), 'write_bytes': attrs.get('total_data_written'),
            'read_commands': attrs.get('host_reads'), 'write_commands': attrs.get('host_writes'),
            'health_percent': max(0, min(100, 100 - int(used))) if used is not None else None,
            'wear_used_percent': int(used) if used is not None else None,
            'media_errors': attrs.get('media_errors')}
