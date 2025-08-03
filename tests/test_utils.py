"""Tests for utility functions."""

from unittest.mock import Mock

from astroid import nodes

from pylint_sort_functions import utils


class TestUtils:
    """Test cases for utility functions."""

    def test_get_functions_from_node(self) -> None:
        """Test function extraction from module node."""
        mock_node = Mock(spec=nodes.Module)
        
        result = utils.get_functions_from_node(mock_node)
        
        # Currently returns empty list - test the actual implementation
        assert result == []

    def test_get_methods_from_class(self) -> None:
        """Test method extraction from class node."""
        mock_node = Mock(spec=nodes.ClassDef)
        
        result = utils.get_methods_from_class(mock_node)
        
        # Currently returns empty list - test the actual implementation
        assert result == []

    def test_are_functions_sorted(self) -> None:
        """Test function sorting validation."""
        mock_functions = [Mock(spec=nodes.FunctionDef)]
        
        result = utils.are_functions_sorted(mock_functions)
        
        # Currently returns True - test the actual implementation
        assert result is True

    def test_are_methods_sorted(self) -> None:
        """Test method sorting validation."""
        mock_methods = [Mock(spec=nodes.FunctionDef)]
        
        result = utils.are_methods_sorted(mock_methods)
        
        # Currently returns True - test the actual implementation
        assert result is True

    def test_are_functions_properly_separated(self) -> None:
        """Test function visibility separation validation."""
        mock_functions = [Mock(spec=nodes.FunctionDef)]
        
        result = utils.are_functions_properly_separated(mock_functions)
        
        # Currently returns True - test the actual implementation
        assert result is True

    def test_is_private_function_with_private_name(self) -> None:
        """Test private function detection with underscore prefix."""
        mock_func = Mock(spec=nodes.FunctionDef)
        mock_func.name = "_private_function"
        
        result = utils.is_private_function(mock_func)
        
        assert result is True

    def test_is_private_function_with_public_name(self) -> None:
        """Test private function detection with public name."""
        mock_func = Mock(spec=nodes.FunctionDef)
        mock_func.name = "public_function"
        
        result = utils.is_private_function(mock_func)
        
        assert result is False

    def test_get_function_groups(self) -> None:
        """Test function grouping by visibility."""
        # Create mock functions
        public_func = Mock(spec=nodes.FunctionDef)
        public_func.name = "public_function"
        
        private_func = Mock(spec=nodes.FunctionDef)
        private_func.name = "_private_function"
        
        functions = [public_func, private_func]
        
        public_functions, private_functions = utils.get_function_groups(functions)
        
        assert len(public_functions) == 1
        assert len(private_functions) == 1
        assert public_functions[0] == public_func
        assert private_functions[0] == private_func

    def test_get_function_groups_empty_list(self) -> None:
        """Test function grouping with empty list."""
        functions = []
        
        public_functions, private_functions = utils.get_function_groups(functions)
        
        assert public_functions == []
        assert private_functions == []
