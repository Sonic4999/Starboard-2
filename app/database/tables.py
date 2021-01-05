GUILDS = \
    """CREATE TABLE IF NOT EXISTS guilds (
        id NUMERIC PRIMARY KEY
    )"""

USERS = \
    """CREATE TABLE IF NOT EXISTS users (
        id NUMERIC PRIMARY KEY
    )"""

MEMBERS = \
    """CREATE TABLE IF NOT EXISTS members (
        user_id NUMERIC NOT NULL,
        guild_id NUMERIC NOT NULL,

        stars_given SMALLINT NOT NULL DEFAULT 0,
        stars_received SMALLINT NOT NULL DEFAULT 0,

        xp SMALLINT NOT NULL DEFAULT 0,
        level SMALLINT NOT NULL DEFAULT 0,

        FOREIGN KEY (user_id) REFERENCES users (id)
            ON DELETE CASCADE,
        FOREIGN KEY (guild_id) REFERENCES guilds (id)
            ON DELETE CASCADE
    )"""

STARBOARDS = \
    """CREATE TABLE IF NOT EXISTS starboards (
        id NUMERIC PRIMARY KEY,
        guild_id NUMERIC NOT NULL,

        threshold SMALLINT NOT NULL DEFAULT 3,
        lower_threshold SMALLINT NOT NULL DEFAULT 0,
        selfstar BOOL NOT NULL DEFAULT False,
        unstar BOOL NOT NULL DEFAULT True,
        xp BOOL NOT NULL DEFAULT True,
        link_edits BOOL NOT NULL DEFAULT True,
        link_deletes BOOL NOT NULL DEFAULT False,
        star_emojis TEXT[] NOT NULL DEFAULT {"⭐"},
        display_emoji TEXT DEFAULT "⭐",

        star BOOL NOT NULL DEFAULT True,
        recv_star BOOL NOT NULL DEFAULT True,

        FOREIGN KEY (guild_id) REFERENCES guilds (id)
            ON DELETE CASCADE
    )"""

MESSAGES = \
    """CREATE TABLE IF NOT EXISTS messages (
        id NUMERIC PRIMARY KEY,
        guild_id NUMERIC NOT NULL,
        channel_id NUMERIC NOT NULL,
        author_id NUMERIC,

        points SMALLINT DEFAULT NULL,

        forced NUMERIC[] NOT NULL DEFAULT {},
        trashed BOOL NOT NULL DEFAULT False,

        FOREIGN KEY (guild_id) REFERENCES guilds (id)
            ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users (id)
            ON DELETE SET NULL
    )"""

STARBOARD_MESSAGES = \
    """CREATE TABLE IF NOT EXISTS starboard_messages (
        id NUMERIC PRIMARY KEY,
        orig_id NUMERIC NOT NULL,
        starboard_id NUMERIC NOT NULL,

        FOREIGN KEY (orig_id) REFERENCES messages (id)
            ON DELETE CASCADE,
        FOREIGN KEY (starboard_id) REFERENCES starboards (id)
            ON DELETE CASCADE
    )"""

REACTIONS = \
    """CREATE TABLE IF NOT EXISTS reactions (
        id BIGINT PRIMARY KEY,
        emoji TEXT NOT NULL,
        message_id NUMERIC NOT NULL,

        FOREIGN KEY (message_id) REFERENCES messages (id)
            ON DELETE CASCADE
    )"""

REACTION_USERS = \
    """CREATE TABLE IF NOT EXISTS reaction_users (
        reaction_id BIGINT NOT NULL,
        user_id NUMERIC NOT NULL,

        FOREIGN KEY (reaction_id) REFERECES reactions (id)
            ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id)
            ON DELETE SET NULL
    )"""
