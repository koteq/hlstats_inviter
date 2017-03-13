import warnings

import MySQLdb

from includes.SteamGroupMembers import SteamGroupMembers


class Candidate(object):
    def __init__(self, community_id, parent):
        self._community_id = community_id
        self._parent = parent

    def __repr__(self):
        return str(self._community_id)

    def invited(self):
        self._parent._invited(self)

    def failed(self):
        self._parent._failed(self)


class HlstatsInvitationSource(object):
    def __init__(self, target_group_id, mysql_connection_params, min_connection_time=3600, min_activity=90):
        self._target_group_id = target_group_id
        self._db = MySQLdb.connect(**mysql_connection_params)
        self._min_connection_time = min_connection_time
        self._min_activity = min_activity
        self._init_schema()
        self._update_joined_members()

    def __del__(self):
        self._db.close()

    def __iter__(self):
        with self._db as cursor:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                cursor.execute("""
                    SELECT
                        CAST(LEFT(puid.uniqueId, 1) AS UNSIGNED) +
                        CAST('76561197960265728' AS UNSIGNED) +
                        CAST(MID(puid.uniqueId, 3, 10) * 2 AS UNSIGNED) AS community_id
                    FROM hlstats_players p
                    INNER JOIN hlstats_playeruniqueids puid ON puid.playerId = p.playerId
                    WHERE p.connection_time >= %s
                      AND p.activity >= %s
                      AND NOT EXISTS (
                        SELECT *
                        FROM inviter i
                        WHERE i.community_id = CAST(LEFT(puid.uniqueId, 1) AS UNSIGNED) +
                                               CAST('76561197960265728' AS UNSIGNED) +
                                               CAST(MID(puid.uniqueId, 3, 10) * 2 AS UNSIGNED)
                          AND i.target_group_id = %s
                          AND i.invited = 1
                      )
                    ORDER BY p.connection_time
                """, (self._min_connection_time, self._min_activity, self._target_group_id))
            row = cursor.fetchone()
            while row is not None:
                yield Candidate(row[0], self)
                row = cursor.fetchone()

    def _init_schema(self):
        with self._db as cursor:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS inviter (
                        id INT NOT NULL AUTO_INCREMENT,
                        community_id BIGINT NOT NULL,
                        target_group_id BIGINT NOT NULL,
                        invited TINYINT(1) NOT NULL DEFAULT '0',
                        joined TINYINT(1) NOT NULL DEFAULT '0',
                        failed TINYINT(1) NOT NULL DEFAULT '0',
                        PRIMARY KEY (id),
                        UNIQUE INDEX uniqueness (community_id, target_group_id)
                    )
                """)

    def _update_joined_members(self):
        with self._db as cursor:
            for community_id in SteamGroupMembers(self._target_group_id):
                cursor.execute("""
                    INSERT INTO inviter (community_id, target_group_id, joined)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE joined = 1;
                """, (community_id, self._target_group_id))

    def _invited(self, candidate):
        with self._db as cursor:
            cursor.execute("""
                INSERT INTO inviter (community_id, target_group_id, invited)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE invited = 1;
            """, (candidate, self._target_group_id))

    def _failed(self, candidate):
        with self._db as cursor:
            cursor.execute("""
                INSERT INTO inviter (community_id, target_group_id, failed)
                VALUES (%s, %s, 1)
                ON DUPLICATE KEY UPDATE failed = 1;
            """, (candidate, self._target_group_id))
