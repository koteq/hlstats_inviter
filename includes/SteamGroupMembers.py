import logging
import urllib2
import xml.etree.ElementTree as ElementTree

logger = logging.getLogger()


class SteamGroupMembers(object):
    """
    Retrives all members of the specified group.
    """
    _members = None

    def __init__(self, group_id):
        self._group_id = group_id

    def __len__(self):
        return len(self._get_members())

    def __contains__(self, item):
        return item in self._get_members()

    def __iter__(self):
        return self._get_members().__iter__()

    def _get_members(self):
        if self._members is None:
            self._members = []
            url = 'http://steamcommunity.com/gid/%s/memberslistxml/?xml=1' % self._group_id
            logger.debug('Loading steam group members %s', url)
            while True:
                responce = urllib2.urlopen(url)
                xml = ElementTree.parse(responce).getroot()
                members_elements = xml.findall('members/steamID64')

                members = map(lambda e: e.text, members_elements)
                self._members.extend(members)
                next_page = xml.find('nextPageLink')
                if next_page is not None:
                    url = next_page.text
                    logger.debug('Loading steam group members (next page) %s', url)
                else:
                    break
            logger.debug('Found %d members in group %s', len(self._members), self._group_id)
        return self._members
