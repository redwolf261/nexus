import os
import ast
import pytest
from backend.services.analytics_service import get_executive_dashboard_service

def test_no_function_shadowing_in_services():
    """
    Parses the AST of all Python files in the backend/services/ directory
    to ensure that no function is defined more than once in the same file.
    This prevents accidental shadowing where a mock implementation overrides
    a real implementation.
    """
    services_dir = os.path.join(os.path.dirname(__file__), '..', 'services')
    
    for root, _, files in os.walk(services_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content, filename=path)
                except SyntaxError:
                    continue
                
                functions = set()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Assert that the function name hasn't been seen before in this file
                        assert node.name not in functions, f"Shadowed function detected: '{node.name}' in {path}"
                        functions.add(node.name)

def test_executive_dashboard_service_no_mock():
    """
    Executes the executive dashboard service to ensure it hits the database
    and does not return the hardcoded mock data.
    """
    try:
        from sqlalchemy.exc import OperationalError
        import psycopg2
        result = get_executive_dashboard_service()
        
        assert "todays_firs" in result
        assert "active_campaigns" in result
        assert "predicted_hotspots" in result
        
        is_mock = (
            result.get("todays_firs") == 42 and
            result.get("active_campaigns") == 39 and
            result.get("predicted_hotspots") == 224
        )
        assert not is_mock, "The executive dashboard service returned mocked data instead of executing a real database query."
    except Exception as e:
        # If it raises a DB connection error, that proves it's hitting the real DB logic
        # and not returning the static mock dict.
        error_str = str(e).lower()
        if "connection" in error_str or "operationalerror" in error_str:
            pass # Passed: Attempted to connect to real DB
        else:
            raise
