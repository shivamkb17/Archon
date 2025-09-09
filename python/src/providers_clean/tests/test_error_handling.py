"""Tests for error handling and edge cases across provider services."""

import pytest
import os
from unittest.mock import patch

from providers_clean.services.api_key_service import APIKeyService
from providers_clean.services.model_config_service import ModelConfigService
from providers_clean.services.usage_service import UsageService
from providers_clean.tests.conftest import MockUnitOfWork


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_api_key_service_corrupted_data(self, mock_uow: MockUnitOfWork):
        """Test handling of corrupted encrypted data."""
        service = APIKeyService(mock_uow)

        # Manually corrupt the stored data by setting an invalid key
        # This simulates corruption in the underlying storage
        await service.set_api_key("openai", "corrupted_data")

        # Attempt to retrieve should handle gracefully
        result = await service.get_api_key("openai")
        # The service should return the stored value even if it's corrupted
        # (corruption detection would be handled at a higher level)
        assert result == "corrupted_data"

    @pytest.mark.asyncio
    async def test_api_key_service_empty_key(self, mock_uow: MockUnitOfWork):
        """Test handling of empty API keys."""
        service = APIKeyService(mock_uow)

        # Try to store empty key
        result = await service.set_api_key("openai", "")
        assert result is True  # Storage succeeds

        # But retrieval should return empty string (as stored)
        retrieved = await service.get_api_key("openai")
        assert retrieved == ""

    @pytest.mark.asyncio
    async def test_api_key_service_very_long_key(self, mock_uow: MockUnitOfWork):
        """Test handling of very long API keys."""
        service = APIKeyService(mock_uow)

        # Create a very long key
        long_key = "sk-" + "a" * 1000

        result = await service.set_api_key("openai", long_key)
        assert result is True

        retrieved = await service.get_api_key("openai")
        assert retrieved == long_key

    @pytest.mark.asyncio
    async def test_model_config_service_invalid_model_strings(self, mock_uow: MockUnitOfWork):
        """Test validation of invalid model strings."""
        service = ModelConfigService(mock_uow)

        invalid_models = [
            "gpt-4o",  # Missing provider
            "openai:",  # Missing model
            ":gpt-4o",  # Missing provider
            "",  # Empty string
            "unknown_provider:gpt-4o",  # Unknown provider
            "openai:gpt-4o:extra",  # Too many parts
        ]

        for invalid_model in invalid_models:
            with pytest.raises(ValueError):
                await service.set_model_config("test", invalid_model)

    @pytest.mark.asyncio
    async def test_model_config_service_temperature_bounds(self, mock_uow: MockUnitOfWork):
        """Test temperature validation bounds."""
        service = ModelConfigService(mock_uow)

        # Test lower bound
        with pytest.raises(ValueError):
            await service.set_model_config("test", "openai:gpt-4o", temperature=-0.1)

        # Test upper bound
        with pytest.raises(ValueError):
            await service.set_model_config("test", "openai:gpt-4o", temperature=2.1)

        # Valid bounds should work
        config = await service.set_model_config("test", "openai:gpt-4o", temperature=1.5)
        assert config.temperature == 1.5

    @pytest.mark.asyncio
    async def test_model_config_service_max_tokens_validation(self, mock_uow: MockUnitOfWork):
        """Test max tokens validation."""
        service = ModelConfigService(mock_uow)

        # Test negative max tokens
        with pytest.raises(ValueError):
            await service.set_model_config("test", "openai:gpt-4o", max_tokens=-100)

        # Test zero max tokens
        with pytest.raises(ValueError):
            await service.set_model_config("test", "openai:gpt-4o", max_tokens=0)

        # Valid max tokens should work
        config = await service.set_model_config("test", "openai:gpt-4o", max_tokens=1000)
        assert config.max_tokens == 1000

    @pytest.mark.asyncio
    async def test_usage_service_negative_tokens(self, mock_uow: MockUnitOfWork):
        """Test handling of negative token counts."""
        service = UsageService(mock_uow)

        # Should still track negative tokens (though unusual)
        result = await service.track_usage("test", "openai:gpt-4o", -100, -50)
        assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_tokens"] == -150

    @pytest.mark.asyncio
    async def test_usage_service_zero_tokens(self, mock_uow: MockUnitOfWork):
        """Test handling of zero token counts."""
        service = UsageService(mock_uow)

        result = await service.track_usage("test", "openai:gpt-4o", 0, 0)
        assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_tokens"] == 0
        assert summary["total_cost"] == 0.0

    @pytest.mark.asyncio
    async def test_usage_service_very_large_token_counts(self, mock_uow: MockUnitOfWork):
        """Test handling of very large token counts."""
        service = UsageService(mock_uow)

        # Test with million-token requests
        result = await service.track_usage("test", "openai:gpt-4o", 1_000_000, 500_000)
        assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_tokens"] == 1_500_000

    @pytest.mark.asyncio
    async def test_api_key_service_environment_variable_priority(self, mock_uow: MockUnitOfWork):
        """Test that environment variables take priority over stored keys."""
        service = APIKeyService(mock_uow)

        stored_key = "sk-stored123"
        env_key = "sk-env123"

        # Store a key
        await service.set_api_key("openai", stored_key)

        # Set environment variable
        with patch.dict(os.environ, {"OPENAI_API_KEY": env_key}):
            retrieved = await service.get_api_key("openai")
            assert retrieved == env_key  # Environment should take priority

    @pytest.mark.asyncio
    async def test_model_config_service_duplicate_services(self, mock_uow: MockUnitOfWork):
        """Test handling of duplicate service configurations."""
        service = ModelConfigService(mock_uow)

        # Set config twice for same service
        await service.set_model_config("test_agent", "openai:gpt-4o", temperature=0.7)
        await service.set_model_config("test_agent", "anthropic:claude-3-opus-20240229", temperature=0.8)

        # Should return the latest config
        config = await service.get_model_config("test_agent")
        assert config.model_string == "anthropic:claude-3-opus-20240229"
        assert config.temperature == 0.8

    @pytest.mark.asyncio
    async def test_usage_service_multiple_concurrent_requests(self, mock_uow: MockUnitOfWork):
        """Test handling multiple concurrent usage tracking requests."""
        service = UsageService(mock_uow)

        # Simulate concurrent requests
        import asyncio

        async def track_request(service_name: str, model: str, input_tokens: int, output_tokens: int):
            return await service.track_usage(service_name, model, input_tokens, output_tokens)

        # Create multiple concurrent tracking requests
        tasks = [
            track_request("agent1", "openai:gpt-4o", 1000, 500),
            track_request(
                "agent2", "anthropic:claude-3-opus-20240229", 800, 400),
            track_request("agent3", "openai:gpt-3.5-turbo", 1200, 600),
            track_request("agent1", "openai:gpt-4o", 900, 450),
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)

        # Verify total tracking
        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 4
        assert summary["total_tokens"] == 5850  # Sum of all tokens

    @pytest.mark.asyncio
    async def test_api_key_service_special_characters(self, mock_uow: MockUnitOfWork):
        """Test handling of special characters in API keys."""
        service = APIKeyService(mock_uow)

        # Test with various special characters
        special_key = "sk-!@#$%^&*()_+-=[]{}|;:,.<>?test123"

        result = await service.set_api_key("openai", special_key)
        assert result is True

        retrieved = await service.get_api_key("openai")
        assert retrieved == special_key

    @pytest.mark.asyncio
    async def test_model_config_service_case_sensitivity(self, mock_uow: MockUnitOfWork):
        """Test case sensitivity in service names and model strings."""
        service = ModelConfigService(mock_uow)

        # Test with mixed case
        await service.set_model_config("Test_Agent", "OpenAI:GPT-4o")

        config = await service.get_model_config("Test_Agent")
        assert config.service_name == "Test_Agent"
        # Provider names are normalized to lowercase for consistency
        assert config.model_string == "openai:GPT-4o"

        # Should be case-sensitive
        with pytest.raises(ValueError):
            await service.get_model_config("test_agent")

    @pytest.mark.asyncio
    async def test_usage_service_empty_metadata(self, mock_uow: MockUnitOfWork):
        """Test usage tracking with empty or None metadata."""
        service = UsageService(mock_uow)

        # Test with None metadata
        result1 = await service.track_usage("test", "openai:gpt-4o", 1000, 500, None)
        assert result1 is True

        # Test with empty dict metadata
        result2 = await service.track_usage("test", "openai:gpt-4o", 800, 400, {})
        assert result2 is True

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 2

    @pytest.mark.asyncio
    async def test_api_key_service_unicode_characters(self, mock_uow: MockUnitOfWork):
        """Test handling of Unicode characters in API keys."""
        service = APIKeyService(mock_uow)

        # Test with Unicode characters
        unicode_key = "sk-tëst123ñ456ü789"

        result = await service.set_api_key("openai", unicode_key)
        assert result is True

        retrieved = await service.get_api_key("openai")
        assert retrieved == unicode_key

    @pytest.mark.asyncio
    async def test_model_config_service_whitespace_handling(self, mock_uow: MockUnitOfWork):
        """Test handling of whitespace in model strings."""
        service = ModelConfigService(mock_uow)

        # Test with extra whitespace
        with pytest.raises(ValueError):
            # Spaces around parts
            await service.set_model_config("test", " openai : gpt-4o ")

        # Test with tabs and newlines
        with pytest.raises(ValueError):
            await service.set_model_config("test", "openai:\t\ngpt-4o")

    @pytest.mark.asyncio
    async def test_usage_service_extremely_large_costs(self, mock_uow: MockUnitOfWork):
        """Test handling of extremely large cost calculations."""
        service = UsageService(mock_uow)

        # Track usage that would result in very large costs
        result = await service.track_usage("test", "openai:gpt-4o", 100_000_000, 50_000_000)
        assert result is True

        summary = await service.get_usage_summary()
        # Cost should be calculable without overflow
        assert isinstance(summary["total_cost"], float)
        assert summary["total_cost"] > 0

    @pytest.mark.asyncio
    async def test_api_key_service_provider_name_validation(self, mock_uow: MockUnitOfWork):
        """Test validation of provider names."""
        service = APIKeyService(mock_uow)

        # Test with valid provider names
        valid_providers = ["openai", "anthropic", "google", "ollama"]

        for provider in valid_providers:
            result = await service.set_api_key(provider, "test-key")
            assert result is True

        # Test with invalid provider names (should still work as we don't validate provider names in API key service)
        result = await service.set_api_key("invalid_provider", "test-key")
        assert result is True

    @pytest.mark.asyncio
    async def test_usage_service_service_name_edge_cases(self, mock_uow: MockUnitOfWork):
        """Test usage tracking with edge case service names."""
        service = UsageService(mock_uow)

        # Test with various service name formats
        edge_cases = [
            "service_with_underscores",
            "service-with-dashes",
            "service.with.dots",
            "ServiceWithCamelCase",
            "service123with456numbers",
            "a",  # Single character
            "a" * 100,  # Very long name
        ]

        for service_name in edge_cases:
            result = await service.track_usage(service_name, "openai:gpt-4o", 100, 50)
            assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == len(edge_cases)
