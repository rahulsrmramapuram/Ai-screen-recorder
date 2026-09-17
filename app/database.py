import socket
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def resolve_database_uri(raw_uri: str) -> str:
    """
    Auto-detect PostgreSQL availability.
    If PostgreSQL is specified but port 5432 (or configured port) is unreachable,
    fallback gracefully to sqlite:///solar.db.
    """
    if not raw_uri or raw_uri.startswith("sqlite"):
        return raw_uri or "sqlite:///solar.db"

    try:
        parsed = urlparse(raw_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        res = sock.connect_ex((host, port))
        sock.close()

        if res == 0:
            print(f"[Database] Connected to PostgreSQL at {host}:{port}")
            return raw_uri
        else:
            print(f"[Database] PostgreSQL port {port} on {host} unreachable. Auto-falling back to sqlite:///solar.db")
            return "sqlite:///solar.db"
    except Exception as err:
        print(f"[Database] Error checking PostgreSQL ({err}). Falling back to sqlite:///solar.db")
        return "sqlite:///solar.db"
