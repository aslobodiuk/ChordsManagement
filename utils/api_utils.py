from typing import Optional, List

from fastapi import Query

def parse_comma_separated_ints(param_name: str):
    def dependency(param_value: Optional[str] = Query(default="", alias=param_name)) -> List[int]:
        if not param_value:
            return []
        return [int(x) for x in param_value.split(",") if x.strip().isdigit()]
    return dependency