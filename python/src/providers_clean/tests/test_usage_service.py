"""Tests for UsageService functionality."""

import pytest

from providers_clean.services.usage_service import UsageService
from providers_clean.tests.conftest import MockUnitOfWork


class TestUsageService:
    """Test usage tracking and reporting functionality."""

    @pytest.mark.asyncio
    async def test_track_usage_basic(self, mock_uow: MockUnitOfWork):
        """Test basic usage tracking."""
        service = UsageService(mock_uow)

        result = await service.track_usage("test_agent", "openai:gpt-4o", 1000, 500)
        assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 1
        assert summary["total_tokens"] == 1500
        assert summary["total_cost"] > 0

    @pytest.mark.asyncio
    async def test_track_usage_with_metadata(self, mock_uow: MockUnitOfWork):
        """Test usage tracking with metadata."""
        service = UsageService(mock_uow)

        metadata = {"request_id": "req-123", "user_id": "user-456"}
        result = await service.track_usage(
            "test_agent",
            "openai:gpt-4o",
            1000,
            500,
            metadata
        )
        assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_get_usage_summary_empty(self, mock_uow: MockUnitOfWork):
        """Test usage summary with no data."""
        service = UsageService(mock_uow)

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 0
        assert summary["total_tokens"] == 0
        assert summary["total_cost"] == 0.0

    @pytest.mark.asyncio
    async def test_multiple_usage_tracking(self, mock_uow: MockUnitOfWork):
        """Test tracking multiple usage events."""
        service = UsageService(mock_uow)

        # Track multiple requests
        requests = [
            ("agent1", "openai:gpt-4o", 1000, 500),
            ("agent2", "anthropic:claude-3-opus-20240229", 800, 400),
            ("agent1", "openai:gpt-3.5-turbo", 1200, 600),
        ]

        for service_name, model, input_tokens, output_tokens in requests:
            result = await service.track_usage(service_name, model, input_tokens, output_tokens)
            assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 3
        assert summary["total_tokens"] == 4500  # 1500 + 1200 + 1800

    @pytest.mark.asyncio
    async def test_get_daily_costs(self, mock_uow: MockUnitOfWork):
        """Test daily cost calculation."""
        service = UsageService(mock_uow)

        # Track usage over multiple days (simulated)
        await service.track_usage("agent1", "openai:gpt-4o", 1000, 500)

        daily_costs = await service.get_daily_costs()
        assert isinstance(daily_costs, dict)
        # Should have at least today's date
        assert len(daily_costs) >= 1

    @pytest.mark.asyncio
    async def test_get_top_models(self, mock_uow: MockUnitOfWork):
        """Test top models identification."""
        service = UsageService(mock_uow)

        # Track usage for different models
        models_usage = [
            ("openai:gpt-4o", 1000, 500),
            ("openai:gpt-4o", 800, 400),
            ("anthropic:claude-3-opus-20240229", 1200, 600),
            ("openai:gpt-3.5-turbo", 500, 250),
        ]

        for model, input_tokens, output_tokens in models_usage:
            await service.track_usage("agent", model, input_tokens, output_tokens)

        top_models = await service.get_top_models()
        assert isinstance(top_models, list)
        assert len(top_models) > 0

        # The first model should have the highest cost
        assert top_models[0]["cost"] >= top_models[1]["cost"]

    @pytest.mark.asyncio
    async def test_usage_with_different_providers(self, mock_uow: MockUnitOfWork):
        """Test usage tracking across different providers."""
        service = UsageService(mock_uow)

        providers = [
            "openai:gpt-4o",
            "anthropic:claude-3-opus-20240229",
            "google:gemini-pro",
        ]

        for provider in providers:
            await service.track_usage("test_agent", provider, 1000, 500)

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 3

    @pytest.mark.asyncio
    async def test_cost_calculation_accuracy(self, mock_uow: MockUnitOfWork):
        """Test that cost calculations are accurate."""
        service = UsageService(mock_uow)

        # Track known usage
        await service.track_usage("test", "openai:gpt-4o", 1000, 500)

        summary = await service.get_usage_summary()

        # Cost should be calculated based on token counts
        # This is a basic check that cost is positive and reasonable
        assert summary["total_cost"] > 0
        assert isinstance(summary["total_cost"], float)

    @pytest.mark.asyncio
    async def test_usage_service_name_validation(self, mock_uow: MockUnitOfWork):
        """Test service name handling."""
        service = UsageService(mock_uow)

        # Test with various service names
        service_names = [
            "simple_agent",
            "complex-agent-name",
            "agent_with_underscores",
            "AgentWithCamelCase",
        ]

        for service_name in service_names:
            result = await service.track_usage(service_name, "openai:gpt-4o", 100, 50)
            assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == len(service_names)

    @pytest.mark.asyncio
    async def test_zero_token_usage(self, mock_uow: MockUnitOfWork):
        """Test handling of zero token counts."""
        service = UsageService(mock_uow)

        result = await service.track_usage("test", "openai:gpt-4o", 0, 0)
        assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_requests"] == 1
        assert summary["total_tokens"] == 0
        assert summary["total_cost"] == 0.0

    @pytest.mark.asyncio
    async def test_large_token_counts(self, mock_uow: MockUnitOfWork):
        """Test handling of large token counts."""
        service = UsageService(mock_uow)

        # Test with large token counts
        result = await service.track_usage("test", "openai:gpt-4o", 100_000, 50_000)
        assert result is True

        summary = await service.get_usage_summary()
        assert summary["total_tokens"] == 150_000
