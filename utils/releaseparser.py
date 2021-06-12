#! python3
# releaseparser.py - parse pre'd music release

import logging, re

from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedRelease:
    artist: str
    title: str
    year: str
    lang: str = ''
    encode: str = 'mp3'
    source: str = 'cd'

class ReleaseParser:
    @staticmethod
    def parse_name(name):
        # group1 -> Artist Name
        # group2 -> Album Title
        # group3 -> Lang for FLAC
        # group4 -> WEB
        # group5 -> FLAC

        match = re.search('([\w\.\-]*?)\-{1,2}([\w\.\-\(\)]*?)(?:\-\([A-Z\-\_\d]{4,}\))?(?:\-((?:CN)|(?:KR)|(?:JP)|(?:ES)))?(?:\-\(?(?:(?:P[Rr][Oo][Pp][Ee][Rr])|(?:R[Ee][Pp][Aa][Cc][Kk])|(?:D[Ii]RF[Ii]X))\)?)?(?:\-READNFO)?(?:\-P[Rr][Oo][Mm][Oo])?(?:\-[\w]*(?:(?:E[Dd][Ii][Tt][Ii][Oo][Nn])|(?:Retail)|(?:R[Ee][Ii][Ss][Ss][Uu][Ee])|(?:R[Ee][Mm][Aa][Ss][Tt][Ee][Rr][Ee][Dd])))?(?:\-\(?(?:(WEB)|(?:\d?CD(?:(?:[MRS]?)|(?:EP))|(?:\d?DVD)|(?:EP)|(?:V[Ii][Nn][Yy][Ll])))\)?)?(?:\-\d{2}BIT)?(?:\-(?:WEB)?(FLAC))?(?:\-([A-Z]{2}))?\-(\d{4})\-(?:\w+)', name)

        if match:
            logger.debug('Regex match result {}'.format(match.groups()))
            parsedrelease = ParsedRelease(
                artist=match.group(1).replace('_', ' '),
                title=match.group(2).replace('_', ' '),
                year=match.group(7)
            )
            if match.group(5): parsedrelease.encode = 'flac'
            if match.group(4): parsedrelease.source = 'web'
            if match.group(6): 
                parsedrelease.lang = match.group(6)
            elif match.group(3):
                parsedrelease.lang = match.group(3)

            return parsedrelease
        raise ValueError('Cannot parse release name (Regex did not match anything)')
