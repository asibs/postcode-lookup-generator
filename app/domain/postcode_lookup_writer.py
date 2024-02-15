import psycopg
from typing import Any

class PostcodeLookupWriter:
    def generate(self) -> None:
        self.initialize_writer()

        with psycopg.connect('user=local password=password host=localhost port=54321 dbname=gis') as conn:
          with conn.cursor() as cursor:
              cursor.execute(
                  """
                  SELECT
                      postcode,
                      uprn_pcon_1, uprn_pcon_1_confidence::float,
                      uprn_pcon_2, uprn_pcon_2_confidence::float,
                      uprn_pcon_3, uprn_pcon_3_confidence::float,
                      uprn_pcon_4, uprn_pcon_4_confidence::float,
                      uprn_pcon_5, uprn_pcon_5_confidence::float,
                      onspd_pcon, onspd_pcon_confidence::float,
                      mysociety_pcon, mysociety_pcon_confidence::float
                  FROM combined_postcode_to_constituency_multicol
                  ORDER BY postcode
                  """
              )
              for row in cursor.fetchall():
                  parsed_row = self._parse_row(row)
                  confidences = self._calculate_confidences(parsed_row)
                  self.write_row(parsed_row, confidences)

        self.finalise_writer()

    def initialize_writer(self) -> None:
        raise NotImplementedError('Implement the initialize_writer method in a subclass')

    def write_row(self, parsed_row: dict[str, Any], confidences: dict[str, float]) -> None:
        raise NotImplementedError('Implement the write_row method in a subclass')

    def finalise_writer(self) -> None:
        raise NotImplementedError('Implement the finalise_writer method in a subclass')

    def _parse_row(self, row: Any) -> dict[str, Any]:
        uprn_pcons = []
        for i in range(1, 10, 2): # 1,3,5,...
            if row[i] is not None:
                uprn_pcons.append({'pcon': row[i], 'confidence': row[i+1]})
        
        onspd_pcons = []
        if row[11] is not None:
            onspd_pcons.append({'pcon': row[11], 'confidence': row[12]})
        
        mysociety_pcons = []
        if row[13] is not None:
            mysociety_pcons.append({'pcon': row[13], 'confidence': row[14]})
            
            
        return {
            'postcode': row[0],
            'uprn_pcons': uprn_pcons,
            'onspd_pcons': onspd_pcons,
            'mysociety_pcons': mysociety_pcons
        }
    
    def _calculate_confidences(self, parsed_row: dict[str, Any]) -> dict[str, float]:
        confidences = {}

        all_pcons = {
            item['pcon']
            for item
            in (parsed_row['uprn_pcons'] + parsed_row['onspd_pcons'] + parsed_row['mysociety_pcons'])
        }

        for pcon in all_pcons:
            uprn_match = next((item for item in parsed_row['uprn_pcons'] if item['pcon'] == pcon), None)
            onspd_match = next((item for item in parsed_row['onspd_pcons'] if item['pcon'] == pcon), None)
            mysoc_match = next((item for item in parsed_row['mysociety_pcons'] if item['pcon'] == pcon), None)

            # We give 50% of the confidence to UPRN, then we give 25% each to ONSPD & MySoc, so a postcode -> constituency
            # will only have 100% if ALL properties in the UPRN give the same constituency, and if both ONSPD & MySociety
            # agree with this. Note, the total confidences for a postcode _may not_ add up to 100% if a single property in
            # ONSPD overlaps with multiple constituency boundaries (in practice, there are only a couple of records where
            # this is a problem). 
            confidence = 0.0
            confidence += (uprn_match['confidence'] * 0.50) if uprn_match else 0.0
            confidence += (onspd_match['confidence'] * 0.25) if onspd_match else 0.0
            confidence += (mysoc_match['confidence'] * 0.25) if mysoc_match else 0.0

            confidences[pcon] = confidence
        return confidences
