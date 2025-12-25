"""Unit tests for serialization utilities."""

import pytest
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import httpx
from unittest.mock import Mock

from neurocluster.api.serialization import to_dict, from_dict, handle_api_response


@dataclass
class SimpleDataclass:
    """Simple test dataclass."""
    name: str
    value: int
    optional_field: Optional[str] = None


@dataclass
class NestedDataclass:
    """Test dataclass with nested structure."""
    id: str
    simple: SimpleDataclass
    items: List[str]


class TestToDict:
    """Tests for to_dict function."""

    def test_simple_dataclass(self):
        """Test converting simple dataclass to dict."""
        obj = SimpleDataclass(name="test", value=42)
        result = to_dict(obj)
        
        assert result == {"name": "test", "value": 42}
        assert "optional_field" not in result  # None values excluded

    def test_with_none_values(self):
        """Test that None values are excluded."""
        obj = SimpleDataclass(name="test", value=42, optional_field=None)
        result = to_dict(obj)
        
        assert "optional_field" not in result

    def test_with_optional_value(self):
        """Test that non-None optional values are included."""
        obj = SimpleDataclass(name="test", value=42, optional_field="present")
        result = to_dict(obj)
        
        assert result["optional_field"] == "present"

    def test_non_dataclass(self):
        """Test that non-dataclass objects are returned as-is."""
        obj = {"key": "value"}
        result = to_dict(obj)
        
        assert result == obj


class TestFromDict:
    """Tests for from_dict function."""

    def test_simple_dataclass(self):
        """Test creating simple dataclass from dict."""
        data = {"name": "test", "value": 42}
        result = from_dict(SimpleDataclass, data)
        
        assert isinstance(result, SimpleDataclass)
        assert result.name == "test"
        assert result.value == 42
        assert result.optional_field is None

    def test_with_optional_field(self):
        """Test creating dataclass with optional field."""
        data = {"name": "test", "value": 42, "optional_field": "present"}
        result = from_dict(SimpleDataclass, data)
        
        assert result.optional_field == "present"

    def test_nested_dataclass(self):
        """Test creating nested dataclass."""
        data = {
            "id": "123",
            "simple": {"name": "test", "value": 42},
            "items": ["a", "b", "c"]
        }
        result = from_dict(NestedDataclass, data)
        
        assert isinstance(result, NestedDataclass)
        assert result.id == "123"
        assert isinstance(result.simple, SimpleDataclass)
        assert result.simple.name == "test"
        assert result.items == ["a", "b", "c"]

    def test_empty_data(self):
        """Test that empty data returns None."""
        result = from_dict(SimpleDataclass, {})
        assert result is None

    def test_none_data(self):
        """Test that None data returns None."""
        result = from_dict(SimpleDataclass, None)
        assert result is None

    def test_extra_fields_ignored(self):
        """Test that extra fields not in dataclass are ignored."""
        data = {"name": "test", "value": 42, "extra_field": "ignored"}
        result = from_dict(SimpleDataclass, data)
        
        assert not hasattr(result, "extra_field")


class TestHandleAPIResponse:
    """Tests for handle_api_response function."""

    def test_success_response(self):
        """Test successful response handling."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        
        result = handle_api_response(mock_response)
        
        assert result == {"data": "success"}

    def test_404_error(self):
        """Test 404 error handling."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_response.text = "Not found"
        
        with pytest.raises(ValueError, match="Resource not found"):
            handle_api_response(mock_response)

    def test_403_error(self):
        """Test 403 error handling."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "Forbidden"}
        mock_response.text = "Forbidden"
        
        with pytest.raises(PermissionError, match="Access denied"):
            handle_api_response(mock_response)

    def test_500_error(self):
        """Test 500 error handling."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_response.request = Mock()
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            handle_api_response(mock_response)
        
        assert "500" in str(exc_info.value)

    def test_error_with_invalid_json(self):
        """Test error handling when response is not valid JSON."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Error message"
        mock_response.request = Mock()
        
        with pytest.raises(httpx.HTTPStatusError):
            handle_api_response(mock_response)

