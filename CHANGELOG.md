# Changelog

All notable changes to the NeuroCluster SDK will be documented in this file.

## [1.0.0] - 2025-12-25

### 🎉 Production Release

### Added
- **Retry Logic**: Automatic retry with exponential backoff for transient failures (429, 500, 502, 503, 504, network errors)
- **Composio Integration**: Full Composio client with toolkit, profile, and tool management
- **Pipedream Integration**: Complete Pipedream client with app, profile, and MCP connection support
- **Modular Design**: Lazy-loaded integration clients (Pipedream/Composio) for optimal performance
- **Comprehensive Tests**: Unit tests for serialization, base client, error handling, retry logic, and integration clients
- **Troubleshooting Guide**: Complete troubleshooting documentation (TROUBLESHOOTING.md)
- **Type Safety**: Improved type hints with TypedDict definitions throughout
- **Connection Pooling**: HTTP connection pooling for better performance
- **Constants Module**: Centralized magic strings in constants.py

### Changed
- **Version**: Bumped from 0.1.0 (Alpha) to 1.0.0 (Production/Stable)
- **Development Status**: Updated to Production/Stable
- **Error Handling**: Standardized error handling across all clients
- **Code Organization**: Refactored to use shared BaseAPIClient and serialization utilities

### Improved
- **Documentation**: Enhanced README with comprehensive examples and integration guides
- **Code Quality**: Removed all TODOs, improved type safety, better error messages
- **Performance**: Connection pooling, lazy loading, optimized serialization

### Fixed
- **Serialization**: Improved handling of nested dataclasses, Optional types, and Lists
- **Error Messages**: More descriptive error messages with proper exception types
- **Type Hints**: Replaced `Any` types with specific TypedDict definitions

## [0.1.0] - Previous Versions

### Initial Release
- Core SDK functionality
- Agents, Threads, Versions APIs
- MCP tools support
- Basic error handling
