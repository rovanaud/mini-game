EMPTY_GAME = {
    "display_name": "Empty Game",
    "version": "1.0",
    "category": "system",
    "min_players": 1,
    "max_players": 8,
    "supports_spectators": True,
    "supports_pause": True,
    "supports_resume": True,
    "supports_bots": False,
    "supports_tournament": False,
    "supports_save_resume": True,
    "parameter_schema_json": {},
    "communication_policy_schema_json": {},
    "metadata_json": {"description": "Placeholder game for testing."},
}

VOWEL_GAME = {
    "display_name": "Vowel Game",
    "version": "1.0.0",
    "category": "party",
    "min_players": 2,
    "max_players": 6,
    "supports_spectators": True,
    "supports_pause": True,
    "supports_resume": True,
    "supports_bots": False,
    "supports_tournament": False,
    "supports_save_resume": True,
    "parameter_schema_json": {},
    "communication_policy_schema_json": {},
    "metadata_json": {
        "description": "Each player plays a vowel that hasn't been used yet."
    },
}
