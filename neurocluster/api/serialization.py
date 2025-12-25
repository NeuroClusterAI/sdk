"""Shared serialization utilities for API clients."""

from dataclasses import dataclass, asdict
from typing import Dict, Any, TypeVar, Type, Optional, Callable, get_origin, get_args
import json
import httpx

T = TypeVar("T")

# Registry for custom from_dict handlers
_FROM_DICT_HANDLERS: Dict[type, Callable[[Dict[str, Any]], Any]] = {}


def register_from_dict(cls: type):
    """
    Decorator to register a custom from_dict handler for a specific type.
    
    Usage:
        @register_from_dict(MyClass)
        def _from_dict_my_class(data: Dict[str, Any]) -> MyClass:
            # Custom deserialization logic
            return MyClass(...)
    
    Args:
        cls: The class to register the handler for
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[[Dict[str, Any]], Any]):
        _FROM_DICT_HANDLERS[cls] = func
        return func
    return decorator


def get_registered_handler(cls: type) -> Optional[Callable[[Dict[str, Any]], Any]]:
    """
    Get the registered handler for a class if one exists.
    
    Args:
        cls: The class to look up
        
    Returns:
        The registered handler function, or None if not found
    """
    return _FROM_DICT_HANDLERS.get(cls)


def to_dict(obj: Any, exclude_none: bool = True) -> Dict[str, Any]:
    """Convert dataclass to dict.
    
    Args:
        obj: Dataclass instance or any object
        exclude_none: If True (default), exclude None values. Set False to preserve them.
        
    Returns:
        Dictionary representation
    """
    if hasattr(obj, "__dataclass_fields__"):
        if exclude_none:
            return {k: v for k, v in asdict(obj).items() if v is not None}
        return asdict(obj)
    return obj


def from_dict(cls: Type[T], data: Dict[str, Any]) -> Optional[T]:
    """Create dataclass instance from dict with proper type handling.
    
    This function handles:
    - Custom registered handlers (checked first)
    - Nested dataclasses
    - Optional types
    - List types with nested dataclasses
    - Missing or None values
    
    Args:
        cls: The dataclass type to instantiate
        data: Dictionary data to convert
        
    Returns:
        Instance of cls, or None if data is empty/None
    """
    if not data:
        return None
    
    # Check for registered custom handler first
    handler = get_registered_handler(cls)
    if handler is not None:
        return handler(data)
    
    if not hasattr(cls, "__dataclass_fields__"):
        return data
    
    # Handle nested dataclasses using type hints
    field_types = {
        field.name: field.type for field in cls.__dataclass_fields__.values()
    }
    processed_data = {}
    
    for key, value in data.items():
        if key not in field_types:
            # Skip fields not in the dataclass
            continue
            
        field_type = field_types[key]
        
        # Handle Optional types
        origin = get_origin(field_type)
        if origin is not None:
            args = get_args(field_type)
            if len(args) > 0:
                # Check if it's Optional (Union with None)
                if type(None) in args:
                    inner_type = args[0] if args[0] is not type(None) else args[1]
                    if value is None:
                        processed_data[key] = None
                        continue
                    field_type = inner_type
                    origin = get_origin(inner_type)
                    args = get_args(inner_type) if origin else None
        
        # Handle List types
        if origin is list and value is not None:
            if len(value) > 0:
                list_type = args[0] if args else Any
                if hasattr(list_type, "__dataclass_fields__") or (
                    hasattr(list_type, "__origin__") and 
                    get_origin(list_type) is not None
                ):
                    processed_data[key] = [
                        from_dict(list_type, item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    processed_data[key] = value
            else:
                processed_data[key] = []
        # Handle nested dataclasses
        elif hasattr(field_type, "__dataclass_fields__") and value is not None:
            if isinstance(value, dict):
                processed_data[key] = from_dict(field_type, value)
            else:
                processed_data[key] = value
        else:
            processed_data[key] = value
    
    # Filter to only include fields that exist in the dataclass
    filtered_data = {
        k: v for k, v in processed_data.items() 
        if k in cls.__dataclass_fields__
    }
    
    return cls(**filtered_data)


def handle_api_response(response: httpx.Response) -> Dict[str, Any]:
    """Handle API response and raise appropriate exceptions.
    
    Args:
        response: HTTP response from httpx
        
    Returns:
        JSON data from response
        
    Raises:
        ValueError: For 404 Not Found errors
        PermissionError: For 403 Forbidden errors
        httpx.HTTPStatusError: For other HTTP errors
    """
    if response.status_code == 404:
        try:
            error_data = response.json()
            error_message = error_data.get("detail", response.text)
        except (json.JSONDecodeError, ValueError):
            error_message = response.text
        raise ValueError(f"Resource not found: {error_message}")
    
    elif response.status_code == 403:
        try:
            error_data = response.json()
            error_message = error_data.get("detail", response.text)
        except (json.JSONDecodeError, ValueError):
            error_message = response.text
        raise PermissionError(f"Access denied: {error_message}")
    
    elif response.status_code >= 400:
        try:
            error_data = response.json()
            error_detail = error_data.get("detail", f"HTTP {response.status_code}")
        except (json.JSONDecodeError, ValueError):
            error_detail = response.text or f"HTTP {response.status_code}"
        raise httpx.HTTPStatusError(
            f"API request failed ({response.status_code}): {error_detail}",
            request=response.request,
            response=response,
        )
    
    return response.json()

