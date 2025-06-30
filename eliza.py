import re
import json
from typing import List, Dict, Optional, Any
from pydantic import ValidationError
from validator import ElizaScript

class Eliza:
    def __init__(self, script_content: str):
        try:
            script_data = json.loads(script_content)
            if not isinstance(script_data, dict):
                raise ValueError("The JSON content must be an object.")
            
            script: ElizaScript = ElizaScript.model_validate(script_data)

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"JSON syntax error: {e.msg}", e.doc, e.pos)
        except ValidationError as e:
            raise ValidationError(f"Script structure validation error: {e}", e.model)

        self.name: str = script.name
        self.initials: List[str] = script.initials
        self.finals: List[str] = script.finals
        self.quits: List[str] = script.quits
        self.pres: Dict[str, str] = script.pres
        self.posts: Dict[str, str] = script.posts
        self.synons: Dict[str, List[str]] = script.synons
        
        self.keywords: Dict[str, Dict[str, Any]] = {}
        for keyword_model in script.keywords:
            keyword_model.rules.sort(key=lambda r: r.decomp.count('*'), reverse=True)
            
            self.keywords[keyword_model.key] = {
                'rank': keyword_model.rank,
                'rules': [rule.model_dump() for rule in keyword_model.rules],
                'last_used_reasmb_idx': 0
            }
        
        self.memory: List[str] = []

    def _substitute(self, words: List[str], sub_dict: Dict[str, str]) -> List[str]:
        return [sub_dict.get(word, word) for word in words]

    def _match_decomp(self, decomp_parts: List[str], input_words: List[str]) -> Optional[List[str]]:
        captured_parts: List[str] = []
        input_idx = 0
        
        if decomp_parts and decomp_parts[0] == '$':
            decomp_parts = decomp_parts[1:]

        for i, decomp_part in enumerate(decomp_parts):
            if not decomp_part: continue

            if decomp_part == '*':
                next_decomp_part = decomp_parts[i + 1] if i < len(decomp_parts) - 1 else None
                end_idx = len(input_words)
                if next_decomp_part:
                    try:
                        end_idx = input_words.index(next_decomp_part, input_idx)
                    except ValueError:
                        return None
                captured_parts.append(' '.join(input_words[input_idx:end_idx]))
                input_idx = end_idx
            
            elif decomp_part.startswith('@'):
                syn_key = decomp_part[1:]
                if (syn_key not in self.synons or 
                        input_idx >= len(input_words) or 
                        input_words[input_idx] not in self.synons[syn_key]):
                    return None
                captured_parts.append(input_words[input_idx])
                input_idx += 1
            
            else:
                if input_idx >= len(input_words) or decomp_part != input_words[input_idx]:
                    return None
                input_idx += 1
        
        if decomp_parts and decomp_parts[-1] == '*' and input_idx < len(input_words):
             captured_parts.append(' '.join(input_words[input_idx:]))

        return captured_parts

    def _reassemble(self, reasmb_rule: str, captured_parts: List[str]) -> str:
        output = reasmb_rule
        for i, part in enumerate(captured_parts):
            placeholder = f'({i+1})'
            words = self._substitute(part.split(), self.posts)
            output = output.replace(placeholder, ' '.join(words))
        return output

    def _get_fallback_response(self) -> str:
        key_data = self.keywords['xnone']
        reasmb_list = key_data['rules'][0]['reasmb']
        reasmb_idx = key_data['last_used_reasmb_idx'] % len(reasmb_list)
        key_data['last_used_reasmb_idx'] += 1
        return reasmb_list[reasmb_idx]

    def _process_decompositions(self, key: str, words: List[str]) -> str:
        key_data = self.keywords[key]
        for rule in key_data['rules']:
            decomp_parts = rule['decomp'].split()
            captured = self._match_decomp(decomp_parts, words)
            
            if captured is not None:
                reasmb_list = rule['reasmb']
                reasmb_idx = key_data['last_used_reasmb_idx'] % len(reasmb_list)
                key_data['last_used_reasmb_idx'] += 1
                response = reasmb_list[reasmb_idx]

                if response.startswith('goto '):
                    goto_key = response.split(' ')[1]
                    return self._process_decompositions(goto_key, words)
                
                return self._reassemble(response, captured)
        
        return self._get_fallback_response()

    def respond(self, text: str) -> Optional[str]:
        text = text.lower().strip()
        if text in self.quits:
            return None

        words = re.findall(r"[\w']+|[.,;!?]", text)
        if not words:
            return self._get_fallback_response()

        words = self._substitute(words, self.pres)

        ranked_keys = sorted(
            [word for word in words if word in self.keywords],
            key=lambda k: self.keywords[k]['rank'],
            reverse=True
        )

        if not ranked_keys:
            if self.memory: return self.memory.pop(0)
            return self._get_fallback_response()

        for key in ranked_keys:
            response = self._process_decompositions(key, words)
            if response != self._get_fallback_response():
                if key in ['my']:
                    self.memory.append(response)
                return response
        
        if self.memory: return self.memory.pop(0)
        return self._get_fallback_response()