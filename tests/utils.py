import toml


def load_secrets():
    with open(".streamlit/secrets.toml", "r") as f:
        return toml.load(f)
