# Troubleshooting Guide

## Common Issues and Solutions

### Authentication Errors

#### Issue: `PermissionError: Access denied`
**Cause**: Invalid API key, or insufficient permissions.

**Solutions**:
1. Verify your API key is correct:
   ```python
   from neurocluster import NeuroCluster
   client = NeuroCluster(api_key="your-api-key")
   ```
2. Check that your API key has the required permissions
3. Ensure you're using the correct API endpoint URL

#### Issue: `ValueError: Resource not found`
**Cause**: The resource (agent, thread, profile) doesn't exist or you don't have access to it.

**Solutions**:
1. Verify the resource ID is correct
2. Check that the resource exists in your account
3. Ensure you're using the correct account/workspace

### Network and Connection Issues

#### Issue: `httpx.TimeoutException` or `httpx.NetworkError`
**Cause**: Network connectivity issues or server timeout.

**Solutions**:
1. Check your internet connection
2. Verify the API endpoint is accessible:
   ```python
   # Test connectivity
   import httpx
   async with httpx.AsyncClient() as client:
       response = await client.get("https://api.neurocluster.com/api/health")
   ```
3. Increase timeout if needed (low-level clients expose `timeout=`):
   ```python
   from neurocluster.api import agents
   agents_client = agents.create_agents_client(
       base_url="https://api.neurocluster.com/api",
       auth_token="your-key",
       timeout=60.0,
   )
   ```
4. The SDK automatically retries transient failures (429, 500, 502, 503, 504)

#### Issue: Rate Limiting (429 errors)
**Cause**: Too many requests in a short time period.

**Solutions**:
1. The SDK automatically retries rate-limited requests with exponential backoff
2. Implement request throttling in your code:
   ```python
   import asyncio
   
   async def throttled_request():
       await client.Agent.create(...)
       await asyncio.sleep(1)  # Wait 1 second between requests
   ```
3. Use connection pooling (already enabled by default)

### Integration Platform Issues

#### Issue: Pipedream/Composio client not working
**Cause**: Integration client not initialized or API endpoint incorrect.

**Solutions**:
1. Integration clients are lazy-loaded - access them explicitly:
   ```python
   from neurocluster import NeuroCluster
   client = NeuroCluster(api_key="your-key")
   # This initializes the Pipedream client
   apps = await client.Pipedream.get_apps()
   ```
2. Verify integration endpoints are accessible
3. Check that your account has access to the integration platform

#### Issue: Profile creation fails
**Cause**: Invalid profile configuration or missing required fields.

**Solutions**:
1. Verify all required fields are provided:
   ```python
   # Pipedream
   from neurocluster.api.pipedream import CreateProfileRequest
   profile = await client.Pipedream.create_profile(
       CreateProfileRequest(
           profile_name="My Profile",  # Required
           app_slug="slack",            # Required
           app_name="Slack"             # Required
       )
   )
   ```
2. Check that the app/toolkit exists:
   ```python
   # Check available apps first
   apps = await client.Pipedream.get_apps(q="slack")
   ```

### Serialization Errors

#### Issue: `TypeError` when creating dataclass instances
**Cause**: Data structure mismatch or missing required fields.

**Solutions**:
1. Verify the data structure matches the expected format
2. Check that all required fields are present
3. Use type hints to catch issues early:
   ```python
   from neurocluster.api.agents import AgentCreateRequest
   
   request = AgentCreateRequest(
       name="My Agent",
       system_prompt="You are helpful"
   )
   ```

### Context Manager Issues

#### Issue: Unclosed connections or resource warnings
**Cause**: Not properly closing HTTP clients.

**Solutions**:
1. Always use async context manager:
   ```python
   async with NeuroCluster(api_key="key") as client:
       agent = await client.Agent.create(...)
   # Client is automatically closed
   ```
2. Or manually close:
   ```python
   client = NeuroCluster(api_key="key")
   try:
       agent = await client.Agent.create(...)
   finally:
       await client.close()
   ```

### Performance Issues

#### Issue: Slow API requests
**Cause**: Network latency or inefficient request patterns.

**Solutions**:
1. Connection pooling is enabled by default - reuse clients
2. Use async/await properly:
   ```python
   # Good: Parallel requests
   agent1, agent2 = await asyncio.gather(
       client.Agent.create(...),
       client.Agent.create(...)
   )
   ```
3. Increase connection limits if needed (default: 100 max connections)

## Debugging Tips

### Enable Logging

```python
import logging

# Enable SDK logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("neurocluster")
logger.setLevel(logging.DEBUG)
```

### Check Response Details

```python
try:
    agent = await client.Agent.get("agent-id")
except httpx.HTTPStatusError as e:
    print(f"Status Code: {e.response.status_code}")
    print(f"Response: {e.response.text}")
    raise
```

### Verify Client Configuration

```python
from neurocluster import NeuroCluster

client = NeuroCluster(api_key="key")
print(f"Base URL: {client._api_url}")
print(f"Headers: {client._agents_client.headers}")
```

## Getting Help

1. **Check the README**: Comprehensive examples and API documentation
2. **Review Error Messages**: SDK provides detailed error messages
3. **Check API Status**: Verify the NeuroCluster API is operational
4. **Contact Support**: support@neurocluster.ai

## Common Error Codes

| Code | Error | Solution |
|------|-------|----------|
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Verify API key |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Verify resource exists |
| 429 | Rate Limited | SDK auto-retries, or throttle requests |
| 500 | Server Error | SDK auto-retries, or contact support |
| 502/503/504 | Gateway Error | SDK auto-retries, or check API status |

