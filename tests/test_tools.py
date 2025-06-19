import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from tools import python_code_interpreter, get_data_schema

# Criando um DataFrame de teste que pode ser usado em múltiplos testes
@pytest.fixture
def sample_df():
    return pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})

@patch('tools.get_active_df')
def test_python_interpreter_sum(mock_get_df, sample_df):
    """Testa uma operação de agregação simples no interpretador."""
    mock_get_df.return_value = sample_df
    code = "resultado = df['A'].sum()"
    result = python_code_interpreter(code, "some_scope")
    assert result == 6

@patch('tools.get_active_df')
def test_python_interpreter_no_result(mock_get_df, sample_df):
    """Testa a execução de código que não atribui à variável 'resultado'."""
    mock_get_df.return_value = sample_df
    code = "x = 10"
    result = python_code_interpreter(code, "some_scope")
    assert "Código executado com sucesso" in result

@patch('tools.get_active_df')
def test_python_interpreter_malicious_code_fails(mock_get_df, sample_df):
    """Testa se código malicioso (que usa built-ins restritos) falha."""
    mock_get_df.return_value = sample_df
    # A função `open` não está na lista de `safe_builtins`.
    code = "with open('test.txt', 'w') as f: f.write('malicious')"
    result = python_code_interpreter(code, "some_scope")
    assert "Erro ao executar código Python" in result
    assert "not defined" in str(result) # Especificamente, 'open' não deve ser definido

@patch('streamlit.session_state')
def test_get_data_schema_file_not_found(mock_session_state):
    """Testa o comportamento de get_data_schema quando o arquivo não existe."""
    mock_session_state.dataframes = {} # Simula estado sem o arquivo
    result = get_data_schema("non_existent_file.csv")
    assert "Erro: Arquivo 'non_existent_file.csv' não encontrado" in result
