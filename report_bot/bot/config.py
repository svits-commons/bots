TORTOISE_ORM = {
    "connections": {
        "default": "sqlite://database.db"
    },
    "apps": {
        "models": {
            # your models + aerich internal models
            "models": ["models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
