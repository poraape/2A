import pytest
from agent_logic import extract_json_from_response

@pytest.mark.parametrize("response_text, expected_json_str", [
    ("Aqui está o JSON: ```json\n{\"key\": \"value\"}\n```", '{"key": "value"}'),
    ("```json{\"tool\": \"T1\", \"input\": \"I1\"}```", '{"tool": "T1", "input": "I1"}'),
    ("Thought: Preciso fazer algo. Action: {\"tool\": \"T2\"}", '{"tool": "T2"}'),
    ("Sem JSON aqui.", None),
    ("JSON malformado: {\"key\": }", '{"key": }') # A extração funciona, a validação (json.loads) falharia depois
])
def test_extract_json_from_response(response_text, expected_json_str):
    """Testa a função de extração de JSON com vários formatos de resposta da IA."""
    assert extract_json_from_response(response_text) == expected_json_str
