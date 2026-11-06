"""Read-only deployment probes; evidence contains booleans, never response bodies."""
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

BASE = 'http://172.20.100.100:8090'
BACKEND_PROBE = """import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3) as r:
    assert r.status == 200 and json.loads(r.read(4096)) == {'status': 'ok'}
"""


def check(evidence, budget=50):
    deadline = time.monotonic() + budget
    results = dict(frontend=False, backend=False, proxy=False)
    while time.monotonic() < deadline:
        results = dict(frontend=False, backend=False, proxy=False)
        try:
            probe = subprocess.run(
                ['docker', 'exec', 'uts-visitor-log-backend-1', 'python', '-c', BACKEND_PROBE],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=max(0.001, min(5, deadline - time.monotonic())))
            results['backend'] = probe.returncode == 0
            for name, path in (('frontend', '/login.html'), ('proxy', '/api/health')):
                if time.monotonic() >= deadline:
                    break
                with urllib.request.urlopen(BASE + path, timeout=min(3, deadline - time.monotonic())) as response:
                    results[name] = response.status == 200 and (
                        name == 'frontend' or json.loads(response.read(4096)) == {'status': 'ok'})
        except (OSError, ValueError, subprocess.SubprocessError):
            pass  # ponytail: booleans only; detailed server diagnostics require a separate approved inspection.
        if all(results.values()):
            break
        time.sleep(max(0, min(2, deadline - time.monotonic())))
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    return all(results.values())


if __name__ == '__main__':
    sys.exit(0 if check(Path('evidence/health.json')) else 1)
