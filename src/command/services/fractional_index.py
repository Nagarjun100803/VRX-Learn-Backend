from fractional_indexing import generate_key_between
from typing import Optional


class FractionalIndex:
    
    @staticmethod
    def generate_key(
        start: Optional[str],
        end: Optional[str]
    ):
        return generate_key_between(start, end)
    

fractional_index = FractionalIndex()