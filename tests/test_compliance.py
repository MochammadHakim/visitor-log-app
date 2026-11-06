"""Offline regression checks; no Docker daemon or deployed application needed."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Compliance(unittest.TestCase):
    def test_login_limits_and_unique_attributes(self):
        class Parser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                names = [name for name, _ in attrs]
                self_test.assertEqual(len(names), len(set(names)), tag)
                data = dict(attrs)
                if data.get('id') in ('username', 'password'):
                    limits[data['id']] = data.get('maxlength')
        self_test, limits = self, {}
        for name in ('login.html', 'visitor-log.html'):
            Parser().feed((ROOT / 'frontend' / name).read_text(encoding='utf-8'))
        self.assertEqual(limits, {'username': '100', 'password': '256'})

    def test_stage_sync_preserves_private_files(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / 'frontend/old-dir').mkdir(parents=True)
            (target / 'frontend/old-dir/removed.txt').write_text('obsolete')
            (target / '.env').write_text('private sentinel')
            subprocess.run([sys.executable, str(ROOT / 'ci/stage_deploy.py'), str(target)], check=True)
            self.assertFalse((target / 'frontend/old-dir').exists())
            for source in (ROOT / 'frontend').rglob('*'):
                if source.is_file():
                    self.assertEqual(source.read_bytes(), (target / 'frontend' / source.relative_to(ROOT / 'frontend')).read_bytes())
            self.assertEqual((target / 'docker-compose.yml').read_bytes(), (ROOT / 'docker-compose.yml').read_bytes())
            self.assertEqual((target / '.env').read_text(), 'private sentinel')

    def test_health_success_and_failure_are_sanitized(self):
        import importlib.util
        import subprocess
        import tempfile
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('health', ROOT / 'ci/health_check.py')
        health = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(health)
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return b'{"status":"ok"}'
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'health.json'
            with patch.object(health.subprocess, 'run') as run, patch.object(health.urllib.request, 'urlopen', return_value=Response()):
                run.return_value.returncode = 0
                self.assertTrue(health.check(evidence, budget=1))
                self.assertIn('http://127.0.0.1:5000/health', str(run.call_args))
            with patch.object(health.subprocess, 'run', side_effect=subprocess.TimeoutExpired('private sentinel', 1)):
                self.assertFalse(health.check(evidence, budget=0.01))
            self.assertNotIn('private sentinel', evidence.read_text())
            self.assertIn('false', evidence.read_text())

if __name__ == '__main__':
    unittest.main()
