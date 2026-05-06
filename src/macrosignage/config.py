from __future__ import annotations

import os
from os import PathLike
from pathlib import Path
from urllib.parse import parse_qsl

from dotenv import load_dotenv, set_key
from sqlalchemy.engine import URL, make_url


DATABASE_ENV_KEY = "MACROSIGNAGE_DATABASE_URI"
DATABASE_OPTIONS = {
    "sqlite": {
        "label": "SQLite",
        "driver": "sqlite",
        "default_port": "",
        "driver_help": "Built in. No additional database driver is required.",
        "install_command": "",
    },
    "postgresql": {
        "label": "PostgreSQL",
        "driver": "postgresql+psycopg",
        "default_port": "5432",
        "driver_help": "Install the PostgreSQL driver: psycopg, for example `uv add psycopg`.",
        "install_command": "uv add psycopg",
    },
    "mysql": {
        "label": "MySQL",
        "driver": "mysql+pymysql",
        "default_port": "3306",
        "driver_help": "Install the MySQL driver: PyMySQL, for example `uv add pymysql`.",
        "install_command": "uv add pymysql",
    },
    "mariadb": {
        "label": "MariaDB",
        "driver": "mariadb+pymysql",
        "default_port": "3306",
        "driver_help": "Install the MariaDB/MySQL driver: PyMySQL, for example `uv add pymysql`.",
        "install_command": "uv add pymysql",
    },
    "mssql": {
        "label": "Microsoft SQL Server",
        "driver": "mssql+pyodbc",
        "default_port": "1433",
        "driver_help": "Install pyodbc and the Microsoft ODBC driver for SQL Server.",
        "install_command": "uv add pyodbc",
    },
    "oracle": {
        "label": "Oracle",
        "driver": "oracle+oracledb",
        "default_port": "1521",
        "driver_help": "Install the Oracle driver: oracledb, for example `uv add oracledb`.",
        "install_command": "uv add oracledb",
    },
    "advanced": {
        "label": "Advanced SQLAlchemy URI",
        "driver": "",
        "default_port": "",
        "driver_help": "Use any Flask-SQLAlchemy/SQLAlchemy database URI. Install the matching Python driver for its dialect.",
        "install_command": "",
    },
}


def default_database_uri(instance_path: str) -> str:
    return f"sqlite:///{os.path.join(instance_path, 'macrosignage.sqlite3')}"


def dotenv_path(env_file: str | PathLike[str] | None = None) -> Path:
    if env_file is None:
        return Path.cwd() / ".env"
    return Path(env_file)


def load_environment(env_file: str | PathLike[str] | None = None) -> Path:
    path = dotenv_path(env_file)
    load_dotenv(path, override=False)
    return path


def validate_database_uri(uri: str) -> str | None:
    if not uri:
        return "Database URI is required."
    try:
        parsed = make_url(uri)
    except Exception:
        return "Enter a valid SQLAlchemy database URI."
    if not parsed.drivername:
        return "Database URI must include a dialect."
    return None


def sqlite_uri_from_path(path: str) -> str:
    return f"sqlite:///{path}"


def database_uri_from_parts(
    *,
    database_type: str,
    sqlite_path: str = "",
    host: str = "",
    port: str = "",
    username: str = "",
    password: str = "",
    database_name: str = "",
    query: str = "",
    advanced_uri: str = "",
    database_uri: str = "",
) -> str:
    if database_type == "advanced":
        return (advanced_uri or database_uri).strip()
    if database_type == "sqlite":
        return sqlite_uri_from_path(sqlite_path.strip())

    option = DATABASE_OPTIONS[database_type]
    query_items = dict(parse_qsl(query.lstrip("?"), keep_blank_values=True)) if query.strip() else None
    port_number = int(port) if port.strip() else None
    url = URL.create(
        drivername=option["driver"],
        username=username.strip() or None,
        password=password or None,
        host=host.strip() or None,
        port=port_number,
        database=database_name.strip() or None,
        query=query_items,
    )
    return url.render_as_string(hide_password=False)


def database_form_from_uri(uri: str, default_sqlite_path: str) -> dict[str, str]:
    form = {
        "database_type": "advanced",
        "sqlite_path": default_sqlite_path,
        "host": "",
        "port": "",
        "username": "",
        "password": "",
        "database_name": "",
        "query": "",
        "database_uri": uri,
    }
    try:
        parsed = make_url(uri)
    except Exception:
        return form

    driver = parsed.drivername
    if driver == "sqlite":
        form["database_type"] = "sqlite"
        form["sqlite_path"] = parsed.database or default_sqlite_path
        return form

    for key, option in DATABASE_OPTIONS.items():
        if key != "advanced" and option["driver"] == driver:
            form["database_type"] = key
            break

    if form["database_type"] == "advanced":
        return form

    form.update(
        {
            "host": parsed.host or "",
            "port": str(parsed.port or DATABASE_OPTIONS[form["database_type"]]["default_port"]),
            "username": parsed.username or "",
            "password": parsed.password or "",
            "database_name": parsed.database or "",
            "query": "&".join(f"{key}={value}" for key, value in parsed.query.items()),
        }
    )
    return form


def write_database_uri(env_file: str | PathLike[str], uri: str) -> None:
    path = Path(env_file)
    path.touch(mode=0o600, exist_ok=True)
    set_key(str(path), DATABASE_ENV_KEY, uri, quote_mode="always")
