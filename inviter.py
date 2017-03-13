#!/usr/bin/env python2
import ConfigParser
import logging.config

from includes.HlstatsInvitationSource import HlstatsInvitationSource
from includes.SteamGroupInviter import SteamGroupInviter


def main():
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger()

    config = ConfigParser.RawConfigParser()
    config.read('inviter.conf')

    inviter = SteamGroupInviter(**dict(config.items('inviter')))
    invite_candidates = HlstatsInvitationSource(config.get('inviter', 'target_group_id'),
                                                dict(config.items('hlststats_connection')),
                                                **dict(config.items('hlststats_candidates')))
    errors_count = 0
    invitations_sent = 0
    for candidate in invite_candidates:
        try:
            inviter.invite(str(candidate))
            candidate.invited()
            logger.info('%s invited', candidate)
        except Exception as e:
            candidate.failed(str(e))
            logger.exception('Unable to invite %s due to exception `%s`', candidate, e)
            errors_count += 1
            if errors_count >= config.getint('limits', 'max_errors_per_run'):
                logger.warning('Max errors limit is reached')
                break

        invitations_sent += 1
        if invitations_sent >= config.getint('limits', 'max_invitations_per_run'):
            logger.info('Max invitations limit is reached')
            break
    logger.info('Results: %d invitations sent, %d errors', invitations_sent, errors_count)

if __name__ == '__main__':
    main()
