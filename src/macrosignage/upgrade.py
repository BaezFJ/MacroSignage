from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

from .config import DATABASE_ENV_KEY, dotenv_path


DEFAULT_PACKAGE = "MacroSignage"
MEDIA_UPLOAD_ENV_KEY = "MACROSIGNAGE_MEDIA_UPLOAD_FOLDER"


@dataclass(frozen=True)
class BackupResult:
    backup_dir: Path
    created: tuple[Path, ...]
    warnings: tuple[str, ...]


def package_spec(package: str, version: str | None) -> str:
    package = package.strip()
    if not package:
        raise ValueError("Package name cannot be empty.")
    if version:
        return f"{package}=={version.strip()}"
    return package


def build_install_command(
    spec: str,
    *,
    python_executable: str = sys.executable,
    uv_bin: str | None = None,
) -> list[str]:
    uv_path = uv_bin or shutil.which("uv")
    if uv_path:
        return [uv_path, "pip", "install", "--python", python_executable, "--upgrade", spec]
    return [python_executable, "-m", "pip", "install", "--upgrade", spec]


def load_upgrade_environment(env_file: str | os.PathLike[str] | None) -> tuple[Path, dict[str, str]]:
    path = dotenv_path(env_file)
    values = dict(os.environ)
    if path.exists():
        parsed = dotenv_values(path)
        values.update({key: value for key, value in parsed.items() if value is not None})
    return path, values


def sqlite_database_path(database_uri: str) -> Path | None:
    try:
        url = make_url(database_uri)
    except Exception:
        return None
    if url.drivername != "sqlite":
        return None
    if not url.database or url.database == ":memory:":
        return None
    return Path(url.database)


def _copy_env_file(env_path: Path, backup_dir: Path) -> Path | None:
    if not env_path.exists():
        return None
    target = backup_dir / env_path.name
    shutil.copy2(env_path, target)
    return target


def _copy_sqlite_database(environment: Mapping[str, str], backup_dir: Path) -> tuple[Path | None, str | None]:
    database_uri = environment.get(DATABASE_ENV_KEY, "")
    if not database_uri:
        return None, f"{DATABASE_ENV_KEY} is not set; database backup was skipped."
    database_path = sqlite_database_path(database_uri)
    if database_path is None:
        return None, "Database backup was skipped because the configured database is not a file-backed SQLite database."
    if not database_path.exists():
        return None, f"SQLite database was not found at {database_path}; database backup was skipped."
    target = backup_dir / database_path.name
    shutil.copy2(database_path, target)
    return target, None


def _archive_media_folder(environment: Mapping[str, str], backup_dir: Path) -> tuple[Path | None, str | None]:
    media_folder = environment.get(MEDIA_UPLOAD_ENV_KEY, "")
    if not media_folder:
        return None, f"{MEDIA_UPLOAD_ENV_KEY} is not set; media backup was skipped."
    media_path = Path(media_folder)
    if not media_path.exists():
        return None, f"Media folder was not found at {media_path}; media backup was skipped."
    if not media_path.is_dir():
        return None, f"Media path {media_path} is not a directory; media backup was skipped."

    target = backup_dir / "media.tar.gz"
    with tarfile.open(target, "w:gz") as archive:
        archive.add(media_path, arcname=media_path.name)
    return target, None


def create_backup(
    *,
    env_path: Path,
    environment: Mapping[str, str],
    backup_root: Path,
    timestamp: str | None = None,
) -> BackupResult:
    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = backup_root / f"macrosignage-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    created: list[Path] = []
    warnings: list[str] = []

    env_backup = _copy_env_file(env_path, backup_dir)
    if env_backup is None:
        warnings.append(f"Environment file was not found at {env_path}; env backup was skipped.")
    else:
        created.append(env_backup)

    database_backup, database_warning = _copy_sqlite_database(environment, backup_dir)
    if database_backup is not None:
        created.append(database_backup)
    if database_warning:
        warnings.append(database_warning)

    media_backup, media_warning = _archive_media_folder(environment, backup_dir)
    if media_backup is not None:
        created.append(media_backup)
    if media_warning:
        warnings.append(media_warning)

    return BackupResult(backup_dir=backup_dir, created=tuple(created), warnings=tuple(warnings))


def _run_command(command: Sequence[str], *, dry_run: bool) -> int:
    print(f"$ {shlex.join(command)}")
    if dry_run:
        return 0
    return subprocess.run(list(command), check=False).returncode


def _confirm_upgrade(spec: str) -> bool:
    answer = input(f"Upgrade MacroSignage using {spec}? [y/N] ")
    return answer.strip().lower() in {"y", "yes"}


def add_upgrade_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--version",
        help="Install a specific MacroSignage version, for example 0.2.5.",
    )
    parser.add_argument(
        "--package",
        default=DEFAULT_PACKAGE,
        help=f"Python package name or spec to upgrade. Defaults to {DEFAULT_PACKAGE}.",
    )
    parser.add_argument(
        "--uv-bin",
        help="Path to the uv executable, for example /usr/local/bin/uv. Defaults to uv found on PATH.",
    )
    parser.add_argument(
        "--env-file",
        help="Environment file to inspect for database and media backup paths. Defaults to .env in the current directory.",
    )
    parser.add_argument(
        "--backup-dir",
        default="backups",
        help="Directory where timestamped backups are created. Defaults to ./backups.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip the local env, SQLite, and media backups.",
    )
    parser.add_argument(
        "--service",
        help="Optional systemd service name to stop before the upgrade and start afterwards.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the planned backup and package commands without changing anything.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run without prompting for confirmation.",
    )


def build_parser(prog: str = "macrosignage-upgrade") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Upgrade the installed MacroSignage package with optional local backups.",
    )
    add_upgrade_options(parser)
    return parser


def run_upgrade(args: argparse.Namespace) -> int:
    spec = package_spec(args.package, args.version)
    env_path, environment = load_upgrade_environment(args.env_file)
    install_command = build_install_command(spec, uv_bin=args.uv_bin)
    backup_root = Path(args.backup_dir)

    if args.dry_run:
        print(f"Would inspect environment file: {env_path}")
        if args.no_backup:
            print("Would skip backups.")
        else:
            print(f"Would create a timestamped backup under: {backup_root}")

    if not args.dry_run and not args.yes and not _confirm_upgrade(spec):
        print("Upgrade cancelled.")
        return 1

    upgrade_status = 0
    service_was_stopped = False

    if args.service:
        stop_status = _run_command(["systemctl", "stop", args.service], dry_run=args.dry_run)
        if stop_status != 0:
            return stop_status
        service_was_stopped = True

    try:
        if not args.no_backup:
            if args.dry_run:
                print("Backup creation skipped during dry run.")
            else:
                backup = create_backup(env_path=env_path, environment=environment, backup_root=backup_root)
                print(f"Created backup directory: {backup.backup_dir}")
                for created_path in backup.created:
                    print(f"Backed up: {created_path}")
                for warning in backup.warnings:
                    print(f"WARNING: {warning}", file=sys.stderr)

        upgrade_status = _run_command(install_command, dry_run=args.dry_run)
    finally:
        if args.service and service_was_stopped:
            start_status = _run_command(["systemctl", "start", args.service], dry_run=args.dry_run)
            if upgrade_status == 0 and start_status != 0:
                upgrade_status = start_status

    return upgrade_status


def main(argv: Sequence[str] | None = None, *, prog: str = "macrosignage-upgrade") -> int:
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    return run_upgrade(args)
