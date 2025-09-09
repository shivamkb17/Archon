"""Tests for Model Config Service."""

import pytest
from typing import Dict, Any

from providers_clean.services.model_config_service import ModelConfigService, ModelConfig
from providers_clean.tests.conftest import MockUnitOfWork


class TestModelConfigService:
    """Test cases for Model Config Service."""

    @pytest.mark.asyncio
    async def test_set_model_config_success(self, mock_uow: MockUnitOfWork):
        """Test successful model configuration setting."""
        service = ModelConfigService(mock_uow)

        config = await service.set_model_config(
            "test_agent",
            "openai:gpt-4o",
            temperature=0.8,
            max_tokens=2000
        )

        assert isinstance(config, ModelConfig)
        assert config.service_name == "test_agent"
        assert config.model_string == "openai:gpt-4o"
        assert config.temperature == 0.8
        assert config.max_tokens == 2000

    @pytest.mark.asyncio
    async def test_set_model_config_defaults(self, mock_uow: MockUnitOfWork):
        """Test model configuration with default values."""
        service = ModelConfigService(mock_uow)

        config = await service.set_model_config("test_agent", "anthropic:claude-3-opus-20240229")

        assert config.temperature == 0.7  # default
        assert config.max_tokens is None  # default

    @pytest.mark.asyncio
    async def test_get_model_config_success(self, mock_uow: MockUnitOfWork):
        """Test successful model configuration retrieval."""
        service = ModelConfigService(mock_uow)

        # First set the config
        await service.set_model_config("test_agent", "openai:gpt-4o", temperature=0.9)

        # Then retrieve it
        config = await service.get_model_config("test_agent")

        assert isinstance(config, ModelConfig)
        assert config.service_name == "test_agent"
        assert config.model_string == "openai:gpt-4o"
        assert config.temperature == 0.9

    @pytest.mark.asyncio
    async def test_get_model_config_not_found(self, mock_uow: MockUnitOfWork):
        """Test model configuration retrieval when not found."""
        service = ModelConfigService(mock_uow)

        with pytest.raises(ValueError, match="Configuration not found for service 'nonexistent'"):
            await service.get_model_config("nonexistent")

    @pytest.mark.asyncio
    async def test_get_all_configs(self, mock_uow: MockUnitOfWork):
        """Test getting all service configurations."""
        service = ModelConfigService(mock_uow)

        # Set multiple configs
        await service.set_model_config("agent1", "openai:gpt-4o")
        await service.set_model_config("agent2", "anthropic:claude-3-sonnet-20240229")
        await service.set_model_config("agent3", "google:gemini-1.5-pro")

        configs = await service.get_all_configs()

        assert configs == {
            "agent1": "openai:gpt-4o",
            "agent2": "anthropic:claude-3-sonnet-20240229",
            "agent3": "google:gemini-1.5-pro"
        }

    @pytest.mark.asyncio
    async def test_get_all_configs_empty(self, mock_uow: MockUnitOfWork):
        """Test getting all configs when none exist."""
        service = ModelConfigService(mock_uow)

        configs = await service.get_all_configs()

        assert configs == {}

    @pytest.mark.asyncio
    async def test_delete_config_success(self, mock_uow: MockUnitOfWork):
        """Test successful configuration deletion."""
        service = ModelConfigService(mock_uow)

        # Set and then delete
        await service.set_model_config("test_agent", "openai:gpt-4o")
        result = await service.delete_config("test_agent")

        assert result is True

        # Verify it's gone
        with pytest.raises(ValueError):
            await service.get_model_config("test_agent")

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, mock_uow: MockUnitOfWork):
        """Test deletion of non-existent configuration."""
        service = ModelConfigService(mock_uow)

        result = await service.delete_config("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_model_string_valid(self, mock_uow: MockUnitOfWork):
        """Test model string validation with valid inputs."""
        service = ModelConfigService(mock_uow)

        # Test various valid model strings
        test_cases = [
            ("openai:gpt-4o", "openai:gpt-4o"),
            ("anthropic:claude-3-opus-20240229",
             "anthropic:claude-3-opus-20240229"),
            ("google:gemini-1.5-pro", "google:gemini-1.5-pro"),
            ("groq:llama-3.1-70b-versatile", "groq:llama-3.1-70b-versatile"),
            ("mistral:mistral-large-latest", "mistral:mistral-large-latest"),
            ("cohere:command-r-plus", "cohere:command-r-plus"),
            ("ollama:llama3", "ollama:llama3"),
            ("deepseek:deepseek-chat", "deepseek:deepseek-chat"),
            # Test case-insensitive provider correction
            ("OpenAI:gpt-4o", "openai:gpt-4o"),
            ("ANTHROPIC:claude-3-opus", "anthropic:claude-3-opus"),
            ("GOOGLE:gemini-pro", "google:gemini-pro")
        ]

        for input_model, expected_output in test_cases:
            result = service.validate_model_string(input_model)
            assert result == expected_output

    @pytest.mark.asyncio
    async def test_validate_model_string_invalid_format(self, mock_uow: MockUnitOfWork):
        """Test model string validation with invalid format."""
        service = ModelConfigService(mock_uow)

        with pytest.raises(ValueError, match="Invalid model string format"):
            service.validate_model_string("gpt-4o")  # Missing provider

        with pytest.raises(ValueError, match="Invalid model string format"):
            service.validate_model_string("openai")  # Missing model

    @pytest.mark.asyncio
    async def test_validate_model_string_unknown_provider(self, mock_uow: MockUnitOfWork):
        """Test model string validation with unknown provider."""
        service = ModelConfigService(mock_uow)

        with pytest.raises(ValueError, match="Unknown provider: unknown_provider"):
            service.validate_model_string("unknown_provider:gpt-4o")

    @pytest.mark.asyncio
    async def test_get_provider_from_service(self, mock_uow: MockUnitOfWork):
        """Test getting provider from service configuration."""
        service = ModelConfigService(mock_uow)

        await service.set_model_config("test_agent", "anthropic:claude-3-sonnet-20240229")

        provider = await service.get_provider_from_service("test_agent")

        assert provider == "anthropic"

    @pytest.mark.asyncio
    async def test_get_provider_from_service_not_found(self, mock_uow: MockUnitOfWork):
        """Test getting provider from non-existent service."""
        service = ModelConfigService(mock_uow)

        with pytest.raises(ValueError, match="Configuration not found for service 'nonexistent'"):
            await service.get_provider_from_service("nonexistent")

    @pytest.mark.asyncio
    async def test_bulk_update_provider(self, mock_uow: MockUnitOfWork):
        """Test bulk updating provider for multiple services."""
        service = ModelConfigService(mock_uow)

        # Set up initial configs
        await service.set_model_config("agent1", "openai:gpt-4o")
        await service.set_model_config("agent2", "openai:gpt-3.5-turbo")
        await service.set_model_config("agent3", "anthropic:claude-3-opus-20240229")

        # Bulk update openai to anthropic
        model_mappings = {
            "openai:gpt-4o": "anthropic:claude-3-5-sonnet-20241022",
            "openai:gpt-3.5-turbo": "anthropic:claude-3-haiku-20240307"
        }

        count = await service.bulk_update_provider("openai", "anthropic", model_mappings)

        assert count == 2

        # Verify updates
        configs = await service.get_all_configs()
        assert configs["agent1"] == "anthropic:claude-3-5-sonnet-20241022"
        assert configs["agent2"] == "anthropic:claude-3-haiku-20240307"
        # unchanged
        assert configs["agent3"] == "anthropic:claude-3-opus-20240229"

    @pytest.mark.asyncio
    async def test_bulk_update_provider_no_mappings(self, mock_uow: MockUnitOfWork):
        """Test bulk updating provider without specific model mappings."""
        service = ModelConfigService(mock_uow)

        # Set up initial configs
        await service.set_model_config("agent1", "openai:gpt-4o")
        await service.set_model_config("agent2", "openai:gpt-3.5-turbo")

        # Bulk update without mappings (should use default pattern)
        count = await service.bulk_update_provider("openai", "anthropic")

        assert count == 2

        # Verify updates use default pattern
        configs = await service.get_all_configs()
        assert configs["agent1"] == "anthropic:gpt-4o"
        assert configs["agent2"] == "anthropic:gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_bulk_update_provider_no_matches(self, mock_uow: MockUnitOfWork):
        """Test bulk updating when no services match the provider."""
        service = ModelConfigService(mock_uow)

        # Set up configs with different provider
        await service.set_model_config("agent1", "anthropic:claude-3-opus-20240229")

        # Try to update openai (no matches)
        count = await service.bulk_update_provider("openai", "google")

        assert count == 0

        # Verify no changes
        configs = await service.get_all_configs()
        assert configs["agent1"] == "anthropic:claude-3-opus-20240229"

    @pytest.mark.asyncio
    async def test_model_config_pydantic_validation(self, mock_uow: MockUnitOfWork):
        """Test Pydantic validation in ModelConfig."""
        service = ModelConfigService(mock_uow)

        # Test temperature bounds
        with pytest.raises(ValueError):
            # > 2.0
            await service.set_model_config("test", "openai:gpt-4o", temperature=2.5)

        with pytest.raises(ValueError):
            # < 0.0
            await service.set_model_config("test", "openai:gpt-4o", temperature=-0.5)

        # Test max_tokens validation
        with pytest.raises(ValueError):
            # < 0
            await service.set_model_config("test", "openai:gpt-4o", max_tokens=-100)

        # Valid bounds should work
        config = await service.set_model_config("test", "openai:gpt-4o", temperature=1.5, max_tokens=1000)
        assert config.temperature == 1.5
        assert config.max_tokens == 1000

    @pytest.mark.asyncio
    async def test_valid_providers_list(self, mock_uow: MockUnitOfWork):
        """Test that all expected providers are in the valid list."""
        service = ModelConfigService(mock_uow)

        expected_providers = [
            "openai", "anthropic", "google", "groq", "mistral",
            "cohere", "ai21", "replicate", "together", "fireworks",
            "openrouter", "deepseek", "xai", "ollama"
        ]

        assert set(service.VALID_PROVIDERS) == set(expected_providers)

    @pytest.mark.asyncio
    async def test_model_config_with_optional_fields(self, mock_uow: MockUnitOfWork):
        """Test model configuration with optional embedding and batch fields."""
        # Test with embedding dimensions and batch size
        config_data: Dict[str, Any] = {
            "service_name": "embedding_agent",
            "model_string": "openai:text-embedding-3-large",
            "temperature": 0.0,
            "embedding_dimensions": 3072,
            "batch_size": 100
        }

        # Save directly to repository to test full config
        assert mock_uow.model_configs is not None
        saved_config = await mock_uow.model_configs.save_config("embedding_agent", config_data)
        config = ModelConfig(**saved_config)

        assert config.service_name == "embedding_agent"
        assert config.model_string == "openai:text-embedding-3-large"
        assert config.temperature == 0.0
        assert config.embedding_dimensions == 3072
        assert config.batch_size == 100
