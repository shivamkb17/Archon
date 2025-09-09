"""Refactored usage tracking service using repository pattern."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from ..core.interfaces.unit_of_work import IUnitOfWork


class UsageService:
    """Service for tracking and analyzing usage using repository pattern."""
    
    # Cost table per million tokens (input/output)
    COST_TABLE = {
        # OpenAI models
        "openai:gpt-4o": {"input": 5.0, "output": 15.0},
        "openai:gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "openai:gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "openai:gpt-4": {"input": 30.0, "output": 60.0},
        "openai:gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        
        # Anthropic models
        "anthropic:claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "anthropic:claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "anthropic:claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "anthropic:claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        
        # Google models
        "google:gemini-1.5-pro": {"input": 3.5, "output": 10.5},
        "google:gemini-1.5-flash": {"input": 0.075, "output": 0.3},
        "google:gemini-pro": {"input": 0.5, "output": 1.5},
        
        # Other providers
        "groq:llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
        "groq:llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
        "groq:mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
        
        "mistral:mistral-large-latest": {"input": 3.0, "output": 9.0},
        "mistral:mistral-medium-latest": {"input": 2.7, "output": 8.1},
        "mistral:mistral-small-latest": {"input": 0.2, "output": 0.6},
        
        "deepseek:deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek:deepseek-coder": {"input": 0.14, "output": 0.28},
        
        # Local models (free)
        "ollama:llama3": {"input": 0.0, "output": 0.0},
        "ollama:mistral": {"input": 0.0, "output": 0.0},
        "ollama:codellama": {"input": 0.0, "output": 0.0},
        
        # Embedding models
        "openai:text-embedding-3-large": {"input": 0.13, "output": 0.0},
        "openai:text-embedding-3-small": {"input": 0.02, "output": 0.0},
        "openai:text-embedding-ada-002": {"input": 0.10, "output": 0.0},
        "cohere:embed-english-v3.0": {"input": 0.10, "output": 0.0},
        "google:text-embedding-004": {"input": 0.025, "output": 0.0}
    }
    
    def __init__(self, unit_of_work: IUnitOfWork):
        """Initialize service with Unit of Work.
        
        Args:
            unit_of_work: Unit of Work for managing repository operations
        """
        self.uow = unit_of_work
    
    async def track_usage(
        self,
        service_name: str,
        model_string: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track usage for a service.
        
        Args:
            service_name: Name of the service
            model_string: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            metadata: Optional additional metadata
            
        Returns:
            True if tracked successfully
        """
        # Calculate cost
        cost = self._calculate_cost(model_string, input_tokens, output_tokens)
        
        usage_data = {
            "service_name": service_name,
            "model_string": model_string,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "metadata": metadata or {}
        }
        
        async with self.uow:
            result = await self.uow.usage.track_usage(usage_data)
            await self.uow.commit()
            return result
    
    def _calculate_cost(self, model_string: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model and token usage.
        
        Args:
            model_string: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Calculated cost in dollars
        """
        if model_string not in self.COST_TABLE:
            # Try to match by provider prefix
            provider = model_string.split(':', 1)[0]
            
            # Default costs by provider
            default_costs = {
                "openai": {"input": 1.0, "output": 2.0},
                "anthropic": {"input": 3.0, "output": 15.0},
                "google": {"input": 1.0, "output": 2.0},
                "ollama": {"input": 0.0, "output": 0.0}
            }
            
            costs = default_costs.get(provider, {"input": 0.5, "output": 1.0})
        else:
            costs = self.COST_TABLE[model_string]
        
        # Calculate cost (prices are per million tokens)
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        
        return input_cost + output_cost
    
    async def get_usage_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage summary for a time period.
        
        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
            service_name: Optional filter by service
            
        Returns:
            Summary dictionary with statistics
        """
        async with self.uow:
            summary = await self.uow.usage.get_usage_summary(
                start_date, end_date, service_name
            )
            
            # Convert Decimal to float for JSON serialization
            if isinstance(summary.get("total_cost"), Decimal):
                summary["total_cost"] = float(summary["total_cost"])
            
            # Convert costs in nested dictionaries
            for model, stats in summary.get("by_model", {}).items():
                if isinstance(stats.get("cost"), Decimal):
                    stats["cost"] = float(stats["cost"])
            
            for service, stats in summary.get("by_service", {}).items():
                if isinstance(stats.get("cost"), Decimal):
                    stats["cost"] = float(stats["cost"])
            
            return summary
    
    async def get_daily_costs(self, days: int = 7) -> Dict[str, float]:
        """Get daily costs for the last N days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            Dictionary mapping dates to costs
        """
        async with self.uow:
            daily_costs = await self.uow.usage.get_daily_costs(days)
            
            # Convert Decimal to float
            return {
                date: float(cost)
                for date, cost in daily_costs.items()
            }
    
    async def get_service_usage(
        self,
        service_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get detailed usage for a specific service.
        
        Args:
            service_name: Service identifier
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Detailed usage statistics
        """
        async with self.uow:
            usage = await self.uow.usage.get_service_usage(
                service_name, start_date, end_date
            )
            
            # Convert Decimal values to float
            if isinstance(usage.get("total_cost"), Decimal):
                usage["total_cost"] = float(usage["total_cost"])
            
            return usage
    
    async def estimate_monthly_cost(self, based_on_days: int = 7) -> float:
        """Estimate monthly cost based on recent usage.
        
        Args:
            based_on_days: Number of recent days to base estimate on
            
        Returns:
            Estimated monthly cost
        """
        async with self.uow:
            estimate = await self.uow.usage.estimate_monthly_cost(based_on_days)
            return float(estimate)
    
    async def get_top_models(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top models by usage.
        
        Args:
            limit: Maximum number of models to return
            
        Returns:
            List of top models with usage statistics
        """
        summary = await self.get_usage_summary()
        by_model = summary.get("by_model", {})
        
        # Sort by total cost
        sorted_models = sorted(
            by_model.items(),
            key=lambda x: x[1].get("cost", 0),
            reverse=True
        )
        
        return [
            {
                "model": model,
                "requests": stats.get("count", 0),
                "tokens": stats.get("tokens", 0),
                "cost": stats.get("cost", 0)
            }
            for model, stats in sorted_models[:limit]
        ]
    
    async def get_cost_by_provider(self) -> Dict[str, float]:
        """Get total costs grouped by provider.
        
        Returns:
            Dictionary mapping providers to total costs
        """
        summary = await self.get_usage_summary()
        by_model = summary.get("by_model", {})
        
        provider_costs = {}
        for model, stats in by_model.items():
            provider = model.split(':', 1)[0] if ':' in model else 'unknown'
            
            if provider not in provider_costs:
                provider_costs[provider] = 0.0
            
            provider_costs[provider] += stats.get("cost", 0)
        
        return provider_costs