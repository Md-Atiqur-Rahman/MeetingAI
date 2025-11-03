# grammar_checker.py

import google.generativeai as genai

class GrammarChecker:
    def __init__(self, model):
        self.model = model
    
    def check(self, text):
        prompt = f"""Analyze this sentence for grammar errors:
        
        Sentence: "{text}"
        
        Respond in JSON format:
        {{
            "is_correct": true/false,
            "errors": [
                {{
                    "type": "verb tense/subject-verb agreement/etc",
                    "incorrect": "the wrong part",
                    "correct": "the correct version",
                    "explanation": "simple explanation"
                }}
            ],
            "corrected_sentence": "fully corrected sentence",
            "suggestion": "friendly tip for improvement"
        }}
        """
        
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)
    
    def _parse_response(self, response_text):
        try:
            # Extract JSON from response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"is_correct": True, "errors": []}
        except:
            return {"is_correct": True, "errors": []}