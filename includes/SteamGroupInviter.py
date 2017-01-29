import re
import rsa
import json
import base64
import logging
import xml.etree.ElementTree as etree

from Crawler import Crawler

logger = logging.getLogger('inviter')


class SteamGroupInviter(object):
    def __init__(self, username, password, target_group_id):
        self.username = username
        self.password = password
        self.target_group_id = target_group_id
        self.crawler = Crawler()
        self._auth()

    def invite(self, community_id):
        """
        :param community_id: for example 76561197960287930
        """
        logger.info('Inviting %s' % community_id)
        session_id = self._get_session_id(community_id)
        params = {'xml': 1,
                  'type': 'groupInvite',
                  'inviter': self._steamid,
                  'invitee': community_id,
                  'group': self.target_group_id,
                  'sessionID': session_id}
        responce = self.crawler.request('http://steamcommunity.com/actions/GroupInvite', params)
        results = etree.parse(responce).getroot().find('results')
        if results is None:
            raise Exception('Invalid responce: %s' % responce.read())
        if not results.text == 'OK':
            raise Exception(results.text)

    def _auth(self):
        logger.info('Auth to the steamcommunity.com')
        logger.debug('Requesting rsa key')
        params = {'username': self.username}
        response = self.crawler.ajax('https://steamcommunity.com/login/getrsakey/', params)
        results = json.loads(response.read())
        assert results[u'success']
        # perform password encryption
        public_key = rsa.PublicKey(int(results[u'publickey_mod'], 16), int(results[u'publickey_exp'], 16))
        encrypted_password = base64.b64encode(rsa.encrypt(self.password, public_key))
        # next try to auth
        logger.debug('Performing auth')
        params = {'password': encrypted_password,
                  'username': self.username,
                  'emailauth': '',
                  'captchagid': -1,
                  'captcha_text': '',
                  'emailsteamid': '',
                  'rsatimestamp': results[u'timestamp'],
                  'remember_login': False}
        responce = self.crawler.ajax('https://steamcommunity.com/login/dologin/', params)
        results = json.loads(responce.read())
        assert results[u'success']
        assert results[u'login_complete']
        # great success
        logger.debug('Successfuly auth')
        self._steamid = results[u'transfer_parameters'][u'steamid']

    def _get_session_id(self, community_id):
        logger.debug('Requesting session id')
        responce = self.crawler.request('http://steamcommunity.com/profiles/' + community_id)
        match = re.search(r'sessionID\s*=\s*"(?P<sessionID>.*?)";', responce.read())
        if match is None:
            raise Exception('Session id not found')
        return match.group('sessionID')
