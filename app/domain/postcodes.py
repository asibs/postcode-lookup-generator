import re
from typing import Optional

class Postcode:
    # Postcodes are comprised of a number of different parts, and these parts form a hierarchy of geographical areas.
    # See https://www.getthedata.com/postcode for a more visual explanation.
    #
    # - Postcode Areas are the highest level of the hierarchy, defining the largest geographical areas.
    #   Postcode Areas are identified by 1 or 2 alphabetical characters.
    #   Eg. 'SW', 'AL', 'E', etc.
    #
    # - Postcode Districts are the second level of the hierarchy.
    #   Postcode Districts are identified by the Postcode Area, plus 1 numeric character, and optionally 1 numeric or
    #   alphabetical character.
    #   Eg. 'SW1A', 'AL1', 'E17', etc.
    #
    # - Postcode Sectors are the third level of the hierarchy.
    #   Postcode Sectors are identified by the Postcode District, plus 1 numeric character.
    #   Eg. 'SW1A 1', 'AL1 9', 'E17 0', etc
    #
    # - Unit Postcodes are the fourth & final level of the hierarchy.
    #   Unit Postcodes are identified by the Postcode Sector plus 2 alphabetical characters - forming the full
    #   postcode.
    #   Eg. 'SW1A 1AA', 'AL1 9ZZ', 'E17 0GF', etc
    #
    # Postcodes are often written with a space character separating the first & second 'halves'. The first 'half' is
    # often called the Outcode or Outward Code. The second 'half' is often called the Incode or Inward Code. In
    # practice, the Outcode is the same as the identifier for the Postcode District.
    #
    # The space between the Outcode and Incode can be important if you are provided a partial postcode. You may assume
    # that given a valid partial postcode, you could find a single unique Postcode Area, District, etc. However, some
    # Postcode Districts and Postcode Sectors are identical without the space separator. For example, 'E17' could refer
    # to the Postcode District 'E17' or the Postcode Sector 'E1 7'. However, for the sake of looking up full postcodes,
    # this consideration is not important.
    #
    # Postcode regular expression copied from: https://www.getthedata.com/postcode
    # It matches the 4 component pieces of a postcode:
    # 1 - Area (1-2 letters)
    # 2 - District MINUS Area (1 number + 1 optional letter/number)
    # 3 - Sector MINUS District (1 number)
    # 4 - Unit Postcode MINUS Sector (2 letters)
    #
    # For example:
    # - 'SW1A 1AA' - { 1:'SW', 2:'1A', 3:'1', 4:'AA' }
    # - 'AL1 9ZZ' - { 1:'AL', 2:'1', 3:'9', 4:'ZZ' }
    # - 'E17 0GF' - { 1:'E', 2:'17', 3:'0', 4:'GF' }
    POSTCODE_REGEXP = '^([A-Z][A-Z]{0,1})([0-9][A-Z0-9]{0,1}) {0,}([0-9])([A-Z]{2})$'

    def __init__(self, postcode_string):
      self.match = re.search(self.POSTCODE_REGEXP, postcode_string)

    def valid(self) -> bool:
      return self.match is not None

    def postcode_area(self) -> Optional[str]:
      if not self.valid():
        return None

      return self.match[1]

    def postcode_district(self) -> Optional[str]:
      if not self.valid():
        return None

      return f"{self.match[1]}{self.match[2]}"

    def postcode_sector(self, separator: str = ' ') -> Optional[str]:
      if not self.valid():
        return None

      return f"{self.match[1]}{self.match[2]}{separator}{self.match[3]}"

    def unit_postcode(self, separator: str = ' ') -> Optional[str]:
      if not self.valid():
        return None

      return f"{self.match[1]}{self.match[2]}{separator}{self.match[3]}{self.match[4]}"

    def outcode(self) -> Optional[str]:
      if not self.valid():
        return None

      return f"{self.match[1]}{self.match[2]}"

    def incode(self) -> Optional[str]:
      if not self.valid():
        return None

      return f"{self.match[3]}{self.match[4]}"

    def __str__(self) -> str:
      if not self.valid():
        return 'invalid'

      return self.unit_postcode()
