from pydantic import BaseModel, field_validator
from typing import List, Dict

class Rule(BaseModel):
    decomp: str
    reasmb: List[str]

class Keyword(BaseModel):
    key: str
    rank: int
    rules: List[Rule]

class ElizaScript(BaseModel):
    name: str
    initials: List[str]
    finals: List[str]
    quits: List[str]
    pres: Dict[str, str]
    posts: Dict[str, str]
    synons: Dict[str, List[str]]
    keywords: List[Keyword]

    @field_validator('keywords')
    @classmethod
    def validate_script_integrity(cls, keywords: List[Keyword], values) -> List[Keyword]:
        all_keys = {kw.key for kw in keywords}
        synons = values.data.get('synons', {})
        
        if 'xnone' not in all_keys:
            raise ValueError("Script validation error: Essential keyword 'xnone' is missing.")

        for i, keyword in enumerate(keywords):
            for j, rule in enumerate(keyword.rules):
                for k, reasmb_item in enumerate(rule.reasmb):
                    if reasmb_item.startswith("goto "):
                        target_key = reasmb_item.split(" ", 1)[1]
                        if target_key not in all_keys:
                            raise ValueError(
                                f"Invalid 'goto' target: '{target_key}'. "
                                f"Found in keywords[{i}] ('{keyword.key}') -> rule[{j}] -> reasmb[{k}]."
                            )
                
                decomp_parts = rule.decomp.split()
                for part in decomp_parts:
                    if part.startswith('@'):
                        syn_key = part[1:]
                        if syn_key not in synons:
                            raise ValueError(
                                f"Invalid synonym reference: '@{syn_key}'. "
                                f"Found in keywords[{i}] ('{keyword.key}') -> rules[{j}] ('{rule.decomp}'). "
                                f"'{syn_key}' is not defined in the 'synons' section."
                            )
                            
        return keywords