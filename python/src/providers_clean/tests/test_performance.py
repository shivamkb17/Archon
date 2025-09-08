"""Performance tests for provider services."""

import pytest
import asyncio
import time

from providers_clean.services.api_key_service import APIKeyService
from providers_clean.services.model_config_service import ModelConfigService
from providers_clean.services.usage_service import UsageService
from providers_clean.tests.conftest import MockUnitOfWork


class TestPerformance:
    """Test performance characteristics of provider services."""

    @pytest.mark.asyncio
    async def test_api_key_service_bulk_operations(self, mock_uow: MockUnitOfWork):
        """Test performance of bulk API key operations."""
        service = APIKeyService(mock_uow)

        # Test setting many keys
        providers = [f"provider_{i}" for i in range(100)]
        keys = [f"sk-test{i}" for i in range(100)]

        start_time = time.time()
        for provider, key in zip(providers, keys):
            result = await service.set_api_key(provider, key)
            assert result is True
        bulk_set_time = time.time() - start_time

        # Test retrieving many keys
        start_time = time.time()
        for provider in providers:
            key = await service.get_api_key(provider)
            assert key is not None
        bulk_get_time = time.time() - start_time

        # Performance assertions (adjust thresholds based on requirements)
        assert bulk_set_time < 5.0  # Should complete within 5 seconds
        assert bulk_get_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_model_config_service_bulk_configurations(self, mock_uow: MockUnitOfWork):
        """Test performance of bulk model configuration operations."""
        service = ModelConfigService(mock_uow)

        # Create many service configurations
        services = [f"service_{i}" for i in range(50)]
        models = ["openai:gpt-4o",
                  "anthropic:claude-3-opus-20240229", "google:gemini-pro"]

        start_time = time.time()
        for i, service_name in enumerate(services):
            model = models[i % len(models)]
            config = await service.set_model_config(service_name, model, temperature=0.7)
            assert config is not None
        bulk_config_time = time.time() - start_time

        # Test bulk retrieval
        start_time = time.time()
        for service_name in services:
            config = await service.get_model_config(service_name)
            assert config is not None
        bulk_retrieve_time = time.time() - start_time

        assert bulk_config_time < 3.0
        assert bulk_retrieve_time < 1.0

    @pytest.mark.asyncio
    async def test_usage_service_high_volume_tracking(self, mock_uow: MockUnitOfWork):
        """Test performance with high volume usage tracking."""
        service = UsageService(mock_uow)

        # Simulate high volume usage tracking
        num_requests = 1000
        models = ["openai:gpt-4o",
                  "anthropic:claude-3-opus-20240229", "openai:gpt-3.5-turbo"]

        start_time = time.time()
        for i in range(num_requests):
            service_name = f"agent_{i % 10}"
            model = models[i % len(models)]
            input_tokens = 1000 + (i % 500)
            output_tokens = 500 + (i % 250)

            result = await service.track_usage(service_name, model, input_tokens, output_tokens)
            assert result is True
        tracking_time = time.time() - start_time

        # Test summary generation performance
        start_time = time.time()
        summary = await service.get_usage_summary()
        summary_time = time.time() - start_time

        assert tracking_time < 10.0  # Should complete within 10 seconds
        assert summary_time < 1.0    # Summary should be fast
        assert summary["total_requests"] == num_requests

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_uow: MockUnitOfWork):
        """Test performance under concurrent load."""
        api_service = APIKeyService(mock_uow)
        model_service = ModelConfigService(mock_uow)
        usage_service = UsageService(mock_uow)

        async def concurrent_api_operations():
            tasks = []
            for i in range(20):
                tasks.append(asyncio.create_task(api_service.set_api_key(
                    f"concurrent_provider_{i}", f"sk-concurrent{i}")))
                tasks.append(asyncio.create_task(
                    api_service.get_api_key(f"concurrent_provider_{i}")))
            await asyncio.gather(*tasks)

        async def concurrent_model_operations():
            tasks = []
            for i in range(20):
                tasks.append(asyncio.create_task(model_service.set_model_config(
                    f"concurrent_service_{i}", "openai:gpt-4o")))
                tasks.append(asyncio.create_task(
                    model_service.get_model_config(f"concurrent_service_{i}")))
            await asyncio.gather(*tasks)

        async def concurrent_usage_operations():
            tasks = []
            for i in range(50):
                tasks.append(asyncio.create_task(usage_service.track_usage(
                    f"concurrent_agent_{i}", "openai:gpt-4o", 100, 50)))
            await asyncio.gather(*tasks)

        start_time = time.time()
        await asyncio.gather(
            concurrent_api_operations(),
            concurrent_model_operations(),
            concurrent_usage_operations()
        )
        concurrent_time = time.time() - start_time

        assert concurrent_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_with_large_datasets(self, mock_uow: MockUnitOfWork):
        """Test memory usage with large datasets."""
        service = UsageService(mock_uow)

        # Track a large number of usage records
        large_dataset_size = 5000

        for i in range(large_dataset_size):
            await service.track_usage(
                f"service_{i % 100}",  # 100 different services
                "openai:gpt-4o",
                1000,
                500,
                {"request_id": f"req_{i}", "user_id": f"user_{i % 50}"}
            )

        # Verify we can still generate summaries efficiently
        start_time = time.time()
        summary = await service.get_usage_summary()
        summary_time = time.time() - start_time

        assert summary["total_requests"] == large_dataset_size
        assert summary_time < 2.0  # Should be reasonably fast even with large dataset

    @pytest.mark.asyncio
    async def test_api_key_service_encryption_performance(self, mock_uow: MockUnitOfWork):
        """Test performance of encryption/decryption operations."""
        service = APIKeyService(mock_uow)

        # Test with various key lengths
        key_lengths = [50, 100, 200, 500, 1000]
        num_operations = 10

        for length in key_lengths:
            test_key = "sk-" + "a" * length

            # Test encryption performance
            start_time = time.time()
            for _ in range(num_operations):
                result = await service.set_api_key("openai", test_key)
                assert result is True
            encrypt_time = time.time() - start_time

            # Test decryption performance
            start_time = time.time()
            for _ in range(num_operations):
                retrieved = await service.get_api_key("openai")
                assert retrieved == test_key
            decrypt_time = time.time() - start_time

            # Performance should scale reasonably with key length
            assert encrypt_time < 1.0
            assert decrypt_time < 1.0

    @pytest.mark.asyncio
    async def test_model_config_service_validation_performance(self, mock_uow: MockUnitOfWork):
        """Test performance of model string validation."""
        service = ModelConfigService(mock_uow)

        # Test validation performance with many different model strings
        model_strings = [
            "openai:gpt-4o",
            "anthropic:claude-3-opus-20240229",
            "google:gemini-pro",
            "openai:gpt-3.5-turbo",
            "anthropic:claude-3-sonnet-20240229",
        ] * 20  # Repeat for more operations

        start_time = time.time()
        for i, model_string in enumerate(model_strings):
            service_name = f"perf_test_service_{i}"
            config = await service.set_model_config(service_name, model_string)
            assert config is not None
        validation_time = time.time() - start_time

        assert validation_time < 2.0

    @pytest.mark.asyncio
    async def test_usage_service_reporting_performance(self, mock_uow: MockUnitOfWork):
        """Test performance of various reporting operations."""
        service = UsageService(mock_uow)

        # Create a dataset for testing reports
        for i in range(200):
            await service.track_usage(
                f"service_{i % 20}",
                ["openai:gpt-4o", "anthropic:claude-3-opus-20240229",
                    "google:gemini-pro"][i % 3],
                1000 + (i % 500),
                500 + (i % 250)
            )

        # Test different report types
        reports = [
            ("summary", service.get_usage_summary()),
            ("daily_costs", service.get_daily_costs()),
            ("top_models", service.get_top_models()),
        ]

        for _, report_coro in reports:
            start_time = time.time()
            result = await report_coro
            report_time = time.time() - start_time

            assert report_time < 1.0  # All reports should be fast
            assert result is not None

    @pytest.mark.asyncio
    async def test_mixed_workload_performance(self, mock_uow: MockUnitOfWork):
        """Test performance with mixed read/write operations."""
        api_service = APIKeyService(mock_uow)
        model_service = ModelConfigService(mock_uow)
        usage_service = UsageService(mock_uow)

        # Simulate a mixed workload
        operations = []

        # API key operations
        for i in range(10):
            operations.append(api_service.set_api_key(
                f"mixed_provider_{i}", f"sk-mixed{i}"))
            operations.append(api_service.get_api_key(f"mixed_provider_{i}"))

        # Model config operations
        for i in range(10):
            operations.append(model_service.set_model_config(
                f"mixed_service_{i}", "openai:gpt-4o"))
            operations.append(
                model_service.get_model_config(f"mixed_service_{i}"))

        # Usage tracking operations
        for i in range(20):
            operations.append(usage_service.track_usage(
                f"mixed_agent_{i}", "openai:gpt-4o", 100, 50))

        # Execute all operations concurrently
        start_time = time.time()
        await asyncio.gather(*operations)
        mixed_workload_time = time.time() - start_time

        assert mixed_workload_time < 3.0

    @pytest.mark.asyncio
    async def test_service_scalability_with_many_services(self, mock_uow: MockUnitOfWork):
        """Test scalability when managing many different services."""
        model_service = ModelConfigService(mock_uow)
        usage_service = UsageService(mock_uow)

        # Create many services with different configurations
        num_services = 200

        # Configure all services
        start_time = time.time()
        for i in range(num_services):
            service_name = f"scale_service_{i}"
            model = ["openai:gpt-4o", "anthropic:claude-3-opus-20240229"][i % 2]
            await model_service.set_model_config(service_name, model, temperature=0.7)
        config_time = time.time() - start_time

        # Track usage for all services
        start_time = time.time()
        for i in range(num_services):
            service_name = f"scale_service_{i}"
            await usage_service.track_usage(service_name, "openai:gpt-4o", 1000, 500)
        usage_time = time.time() - start_time

        # Generate reports
        start_time = time.time()
        summary = await usage_service.get_usage_summary()
        await usage_service.get_top_models()
        report_time = time.time() - start_time

        assert config_time < 5.0
        assert usage_time < 5.0
        assert report_time < 1.0
        assert summary["total_requests"] == num_services
