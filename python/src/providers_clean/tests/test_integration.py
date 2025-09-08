"""Integration tests for the provider services working together."""

import pytest

from providers_clean.services.api_key_service import APIKeyService
from providers_clean.services.model_config_service import ModelConfigService
from providers_clean.services.usage_service import UsageService
from providers_clean.tests.conftest import MockUnitOfWork


class TestProviderServicesIntegration:
    """Integration tests for provider services working together."""

    @pytest.mark.asyncio
    async def test_full_provider_workflow(self, mock_uow: MockUnitOfWork):
        """Test complete workflow from API key setup to usage tracking."""
        # Initialize services
        api_key_service = APIKeyService(mock_uow)
        model_config_service = ModelConfigService(mock_uow)
        usage_service = UsageService(mock_uow)

        # Step 1: Set up API keys
        openai_key = "sk-test123456789"
        anthropic_key = "sk-ant-test123456"

        await api_key_service.set_api_key("openai", openai_key)
        await api_key_service.set_api_key("anthropic", anthropic_key)

        # Step 2: Configure models for services
        await model_config_service.set_model_config("rag_agent", "openai:gpt-4o", temperature=0.7)
        await model_config_service.set_model_config("chat_agent", "anthropic:claude-3-sonnet-20240229", temperature=0.8)

        # Step 3: Verify configurations
        rag_config = await model_config_service.get_model_config("rag_agent")
        chat_config = await model_config_service.get_model_config("chat_agent")

        assert rag_config.model_string == "openai:gpt-4o"
        assert rag_config.temperature == 0.7
        assert chat_config.model_string == "anthropic:claude-3-sonnet-20240229"
        assert chat_config.temperature == 0.8

        # Step 4: Get all configurations
        all_configs = await model_config_service.get_all_configs()
        assert all_configs["rag_agent"] == "openai:gpt-4o"
        assert all_configs["chat_agent"] == "anthropic:claude-3-sonnet-20240229"

        # Step 5: Track usage
        await usage_service.track_usage("rag_agent", "openai:gpt-4o", 1000, 500)
        await usage_service.track_usage("chat_agent", "anthropic:claude-3-sonnet-20240229", 800, 300)

        # Step 6: Get usage summary
        summary = await usage_service.get_usage_summary()

        assert summary["total_requests"] == 2
        assert summary["total_tokens"] == 2600  # 1000+500+800+300
        assert summary["by_service"]["rag_agent"]["count"] == 1
        assert summary["by_service"]["chat_agent"]["count"] == 1

        # Step 7: Verify API key retrieval
        retrieved_openai = await api_key_service.get_api_key("openai")
        retrieved_anthropic = await api_key_service.get_api_key("anthropic")

        assert retrieved_openai == openai_key
        assert retrieved_anthropic == anthropic_key

        # Step 8: Check active providers
        active_providers = await api_key_service.get_active_providers()
        assert "openai" in active_providers
        assert "anthropic" in active_providers
        assert "ollama" in active_providers  # Always included

    @pytest.mark.asyncio
    async def test_provider_switching_workflow(self, mock_uow: MockUnitOfWork):
        """Test switching providers for existing services."""
        api_key_service = APIKeyService(mock_uow)
        model_config_service = ModelConfigService(mock_uow)
        usage_service = UsageService(mock_uow)

        # Set up initial configuration
        await api_key_service.set_api_key("openai", "sk-test123")
        await model_config_service.set_model_config("test_agent", "openai:gpt-4o")

        # Track some usage with OpenAI
        await usage_service.track_usage("test_agent", "openai:gpt-4o", 1000, 500)

        # Switch to Anthropic
        await api_key_service.set_api_key("anthropic", "sk-ant-test123")
        await model_config_service.set_model_config("test_agent", "anthropic:claude-3-opus-20240229")

        # Track usage with new provider
        await usage_service.track_usage("test_agent", "anthropic:claude-3-opus-20240229", 800, 400)

        # Verify the switch
        current_config = await model_config_service.get_model_config("test_agent")
        assert current_config.model_string == "anthropic:claude-3-opus-20240229"

        summary = await usage_service.get_usage_summary()
        assert summary["total_requests"] == 2
        assert "openai:gpt-4o" in summary["by_model"]
        assert "anthropic:claude-3-opus-20240229" in summary["by_model"]

    @pytest.mark.asyncio
    async def test_bulk_provider_update_workflow(self, mock_uow: MockUnitOfWork):
        """Test bulk updating multiple services to new provider."""
        api_key_service = APIKeyService(mock_uow)
        model_config_service = ModelConfigService(mock_uow)

        # Set up multiple services with OpenAI
        await api_key_service.set_api_key("openai", "sk-test123")
        await api_key_service.set_api_key("anthropic", "sk-ant-test123")

        await model_config_service.set_model_config("agent1", "openai:gpt-4o")
        await model_config_service.set_model_config("agent2", "openai:gpt-3.5-turbo")
        await model_config_service.set_model_config("agent3", "anthropic:claude-3-sonnet-20240229")

        # Bulk update OpenAI services to Anthropic
        model_mappings = {
            "openai:gpt-4o": "anthropic:claude-3-5-sonnet-20241022",
            "openai:gpt-3.5-turbo": "anthropic:claude-3-haiku-20240307"
        }

        updated_count = await model_config_service.bulk_update_provider("openai", "anthropic", model_mappings)

        assert updated_count == 2

        # Verify updates
        configs = await model_config_service.get_all_configs()
        assert configs["agent1"] == "anthropic:claude-3-5-sonnet-20241022"
        assert configs["agent2"] == "anthropic:claude-3-haiku-20240307"
        # unchanged
        assert configs["agent3"] == "anthropic:claude-3-sonnet-20240229"

    @pytest.mark.asyncio
    async def test_environment_setup_and_usage_tracking(self, mock_uow: MockUnitOfWork):
        """Test environment setup and subsequent usage tracking."""
        api_key_service = APIKeyService(mock_uow)
        usage_service = UsageService(mock_uow)

        # Set up API keys
        await api_key_service.set_api_key("openai", "sk-test123")
        await api_key_service.set_api_key("anthropic", "sk-ant-test123")

        # Simulate environment setup (normally done at startup)
        status = await api_key_service.setup_environment()
        assert status["openai"] is True
        assert status["anthropic"] is True

        # Track usage for different services
        services_and_models = [
            ("web_agent", "openai:gpt-4o"),
            ("code_agent", "anthropic:claude-3-sonnet-20240229"),
            ("chat_agent", "openai:gpt-3.5-turbo"),
        ]

        for service, model in services_and_models:
            await usage_service.track_usage(service, model, 1000, 500)

        # Verify comprehensive usage tracking
        summary = await usage_service.get_usage_summary()
        assert summary["total_requests"] == 3
        assert summary["total_tokens"] == 4500  # 3 * (1000 + 500)

        # Check service-specific usage
        for service, _ in services_and_models:
            service_usage = await usage_service.get_service_usage(service)
            assert service_usage["total_requests"] == 1
            assert service_usage["total_tokens"] == 1500

        # Check provider cost breakdown
        provider_costs = await usage_service.get_cost_by_provider()
        assert "openai" in provider_costs
        assert "anthropic" in provider_costs

    @pytest.mark.asyncio
    async def test_key_rotation_workflow(self, mock_uow: MockUnitOfWork):
        """Test API key rotation and continued usage tracking."""
        api_key_service = APIKeyService(mock_uow)
        model_config_service = ModelConfigService(mock_uow)
        usage_service = UsageService(mock_uow)

        # Initial setup
        old_key = "sk-old123456"
        new_key = "sk-new123456"

        await api_key_service.set_api_key("openai", old_key)
        await model_config_service.set_model_config("test_agent", "openai:gpt-4o")

        # Track usage with old key
        await usage_service.track_usage("test_agent", "openai:gpt-4o", 1000, 500)

        # Rotate key
        rotate_result = await api_key_service.rotate_api_key("openai", new_key)
        assert rotate_result is True

        # Verify new key is active
        current_key = await api_key_service.get_api_key("openai")
        assert current_key == new_key

        # Continue tracking usage with new key
        await usage_service.track_usage("test_agent", "openai:gpt-4o", 800, 400)

        # Verify continued usage tracking
        summary = await usage_service.get_usage_summary()
        assert summary["total_requests"] == 2
        assert summary["total_tokens"] == 2700  # 1000+500+800+400

    @pytest.mark.asyncio
    async def test_service_provider_mapping_workflow(self, mock_uow: MockUnitOfWork):
        """Test mapping services to providers and tracking usage."""
        api_key_service = APIKeyService(mock_uow)
        model_config_service = ModelConfigService(mock_uow)
        usage_service = UsageService(mock_uow)

        # Set up API keys for multiple providers
        await api_key_service.set_api_key("openai", "sk-openai123")
        await api_key_service.set_api_key("anthropic", "sk-anthropic123")
        await api_key_service.set_api_key("google", "google-api-key")

        # Configure different services with different providers
        service_configs = {
            "rag_agent": "openai:gpt-4o",
            "chat_agent": "anthropic:claude-3-sonnet-20240229",
            "vision_agent": "google:gemini-1.5-pro",
            "code_agent": "openai:gpt-3.5-turbo"
        }

        for service, model in service_configs.items():
            await model_config_service.set_model_config(service, model)

        # Track usage for each service
        usage_data = [
            ("rag_agent", "openai:gpt-4o", 2000, 1000),
            ("chat_agent", "anthropic:claude-3-sonnet-20240229", 1500, 800),
            ("vision_agent", "google:gemini-1.5-pro", 1000, 500),
            ("code_agent", "openai:gpt-3.5-turbo", 3000, 1500),
        ]

        for service, model, input_tokens, output_tokens in usage_data:
            await usage_service.track_usage(service, model, input_tokens, output_tokens)

        # Verify comprehensive tracking
        summary = await usage_service.get_usage_summary()
        assert summary["total_requests"] == 4
        assert summary["total_tokens"] == 11300  # Sum of all tokens

        # Check that all services are tracked
        for service in service_configs.keys():
            assert service in summary["by_service"]
            assert summary["by_service"][service]["count"] == 1

        # Check provider distribution
        provider_costs = await usage_service.get_cost_by_provider()
        assert len(provider_costs) == 3  # openai, anthropic, google

        # Verify service-to-provider mapping
        for service, expected_model in service_configs.items():
            config = await model_config_service.get_model_config(service)
            assert config.model_string == expected_model

            provider = await model_config_service.get_provider_from_service(service)
            expected_provider = expected_model.split(":")[0]
            assert provider == expected_provider
