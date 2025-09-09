# Provider Services Test Suite

This directory contains comprehensive tests for the clean-multi-provider-feature, a simplified provider integration system for PydanticAI.

## Test Structure

### Unit Tests

- **`test_api_key_service.py`** - Tests for API key management functionality
- **`test_model_config_service.py`** - Tests for model configuration management
- **`test_usage_service.py`** - Tests for usage tracking and cost calculation

### Integration Tests

- **`test_integration.py`** - Tests for services working together in realistic scenarios

### Error Handling & Edge Cases

- **`test_error_handling.py`** - Tests for error conditions and edge cases

### Performance Tests

- **`test_performance.py`** - Tests for performance characteristics under load

### Test Infrastructure

- **`conftest.py`** - Shared test fixtures and mock implementations

## Running Tests

### Prerequisites

- Python 3.8+
- pytest
- pytest-asyncio

### Install Dependencies

```bash
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Unit tests
pytest test_api_key_service.py -v
pytest test_model_config_service.py -v
pytest test_usage_service.py -v

# Integration tests
pytest test_integration.py -v

# Error handling tests
pytest test_error_handling.py -v

# Performance tests
pytest test_performance.py -v
```

### Run Tests with Coverage

```bash
pytest --cov=providers_clean --cov-report=html
```

### Run Tests in Parallel

```bash
pytest -n auto
```

## Test Coverage

The test suite covers:

### API Key Service

- ✅ Secure key storage with encryption
- ✅ Environment variable priority
- ✅ Key rotation and updates
- ✅ Provider validation
- ✅ Error handling for corrupted data
- ✅ Special characters and Unicode support

### Model Configuration Service

- ✅ Model string validation (provider:model format)
- ✅ Temperature and max_tokens bounds checking
- ✅ Service-specific configurations
- ✅ Bulk operations
- ✅ Provider switching
- ✅ Case sensitivity handling

### Usage Service

- ✅ Token tracking (input/output)
- ✅ Cost calculation
- ✅ Usage summaries and reports
- ✅ Daily cost analysis
- ✅ Top models identification
- ✅ Metadata support

### Integration Scenarios

- ✅ End-to-end provider setup workflows
- ✅ API key to model config integration
- ✅ Usage tracking across providers
- ✅ Provider switching with usage continuity
- ✅ Bulk operations across services

### Error Handling

- ✅ Corrupted data handling
- ✅ Invalid input validation
- ✅ Boundary condition testing
- ✅ Unicode and special character support
- ✅ Concurrent operation safety

### Performance

- ✅ Bulk operations (100+ items)
- ✅ High-volume usage tracking (1000+ requests)
- ✅ Concurrent operations
- ✅ Large dataset handling (5000+ records)
- ✅ Mixed workload scenarios
- ✅ Scalability with many services

## Mock Infrastructure

The test suite uses comprehensive mocks:

- **`MockUnitOfWork`** - Mock implementation of the unit of work pattern
- **`MockApiKeyRepository`** - Mock API key storage
- **`MockModelConfigRepository`** - Mock model configuration storage
- **`MockUsageRepository`** - Mock usage data storage
- **Sample fixtures** - Pre-configured test data

## Test Categories

### Happy Path Tests

Tests that verify normal operation under expected conditions.

### Edge Case Tests

Tests for boundary conditions, unusual but valid inputs.

### Error Condition Tests

Tests for invalid inputs, corrupted data, and failure scenarios.

### Performance Tests

Tests that verify the system performs adequately under load.

### Integration Tests

Tests that verify components work together correctly.

## Adding New Tests

When adding new tests:

1. **Follow naming conventions**: `test_<functionality>_<scenario>`
2. **Use descriptive docstrings**: Explain what the test verifies
3. **Include assertions**: Test both success and failure cases
4. **Use fixtures**: Leverage existing mock infrastructure
5. **Mark async tests**: Use `@pytest.mark.asyncio` for async tests
6. **Test edge cases**: Include boundary conditions and error scenarios

## Example Test Structure

```python
@pytest.mark.asyncio
async def test_feature_scenario(self, mock_uow: MockUnitOfWork):
    """Test that feature works correctly in specific scenario."""
    service = Service(mock_uow)

    # Arrange
    setup_data = "test_input"

    # Act
    result = await service.method(setup_data)

    # Assert
    assert result == expected_output
    assert some_condition
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines and provide:

- Fast feedback on code changes
- Regression prevention
- Documentation of expected behavior
- Confidence in deployments

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the `providers_clean` package is in the Python path
2. **Async test failures**: Make sure `pytest-asyncio` is installed
3. **Mock setup issues**: Check that fixtures are properly configured in `conftest.py`

### Debug Mode

```bash
pytest -v -s --pdb
```

This will run tests verbosely, capture output, and drop into debugger on failures.
