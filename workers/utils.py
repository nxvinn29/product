import os

def get_secret(secret_name, default=None):
    """
    Retrieve secret from Docker secrets file or environment variable.
    Priority: /run/secrets/{secret_name} > os.environ[{SECRET_NAME}] > default
    """
    # 1. Try Docker secret file
    secret_path = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r") as f:
                return f.read().strip()
        except IOError:
            pass # Fallback
    
    # 2. Try Environment variable (Upper case)
    return os.environ.get(secret_name.upper(), default)
