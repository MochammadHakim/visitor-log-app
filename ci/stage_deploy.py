"""Sync only public deployment files; never copy or remove the host .env/data."""
from pathlib import Path
import shutil
import sys


def stage(source, target):
    target.mkdir(parents=True, exist_ok=True)
    src, dst = source / 'frontend', target / 'frontend'
    # Reject symlinks before copying/pruning: never follow a path outside frontend.
    for tree in (src, dst):
        if tree.is_symlink() or any(p.is_symlink() for p in tree.rglob('*')):
            raise ValueError('Frontend symlinks are not allowed')
    shutil.copytree(src, dst, dirs_exist_ok=True)
    for path in sorted(dst.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if not (src / path.relative_to(dst)).exists():
            path.rmdir() if path.is_dir() else path.unlink()
    shutil.copytree(source / 'backend', target / 'backend', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copyfile(source / 'docker-compose.yml', target / 'docker-compose.yml')


if __name__ == '__main__':
    stage(Path(__file__).resolve().parents[1], Path(sys.argv[1]))
