"""Supabase implementation of the usage tracking repository."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from supabase import Client
from ....core.interfaces.repositories import IUsageRepository


class SupabaseUsageRepository(IUsageRepository):
    """Concrete implementation of usage repository using Supabase."""
    
    def __init__(self, db_client: Client):
        """Initialize repository with Supabase client.
        
        Args:
            db_client: Supabase client instance
        """
        self.db = db_client
        self.table_name = "model_usage"
    
    async def track_usage(self, usage_data: Dict[str, Any]) -> bool:
        """Track usage for a service.
        
        Args:
            usage_data: Dictionary containing usage information
            
        Returns:
            True if tracked successfully
        """
        try:
            # Calculate period (daily buckets)
            now = datetime.utcnow()
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
            
            total_tokens = usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)
            
            # Use the increment_usage function for atomic updates
            response = self.db.rpc('increment_usage', {
                'p_service': usage_data["service_name"],
                'p_model': usage_data["model_string"],
                'p_tokens': total_tokens,
                'p_cost': float(usage_data.get("cost", 0)),
                'p_period_start': period_start.isoformat()
            }).execute()
            
            return True  # RPC call succeeded
            
        except Exception as e:
            print(f"Error tracking usage: {e}")
            return False
    
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
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build query
        query = self.db.table(self.table_name).select("*")
        query = query.gte("period_start", start_date.isoformat())
        query = query.lte("period_start", end_date.isoformat())
        
        if service_name:
            query = query.eq("service_name", service_name)
        
        response = query.execute()
        
        if not response.data:
            return {
                "total_cost": Decimal("0"),
                "total_requests": 0,
                "total_tokens": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "by_model": {},
                "by_service": {}
            }
        
        # Calculate aggregates
        total_cost = Decimal("0")
        total_tokens = 0
        total_requests = 0
        by_model = {}
        by_service = {}
        
        for record in response.data:
            record: Dict[str, Any] = record  # Type annotation for clarity
            cost = Decimal(str(record.get("estimated_cost", 0)))
            total_cost += cost
            tokens = record.get("total_tokens", 0)
            total_tokens += tokens
            requests = record.get("request_count", 0)
            total_requests += requests
            
            # Aggregate by model
            model = record["model_string"]
            if model not in by_model:
                by_model[model] = {
                    "count": 0,
                    "cost": Decimal("0"),
                    "tokens": 0
                }
            by_model[model]["count"] += 1
            by_model[model]["cost"] += cost
            by_model[model]["tokens"] += record.get("total_tokens", 0)
            
            # Aggregate by service
            service = record["service_name"]
            if service not in by_service:
                by_service[service] = {
                    "count": 0,
                    "cost": Decimal("0"),
                    "tokens": 0
                }
            by_service[service]["count"] += 1
            by_service[service]["cost"] += cost
            by_service[service]["tokens"] += record.get("total_tokens", 0)
        
        return {
            "total_cost": total_cost,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_input_tokens": total_tokens // 2,  # Estimate
            "total_output_tokens": total_tokens // 2,  # Estimate
            "by_model": by_model,
            "by_service": by_service,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def get_daily_costs(self, days: int = 7) -> Dict[str, Decimal]:
        """Get daily costs for the last N days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            Dictionary mapping dates to costs
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Fetch and aggregate by day
        response = self.db.table(self.table_name).select("period_start", "estimated_cost").gte(
            "period_start", start_date.isoformat()
        ).lte(
            "period_start", end_date.isoformat()
        ).execute()
        
        daily_costs = {}
        
        if response.data:
            for record in response.data:
                record: Dict[str, Any] = record
                # Extract date part
                date_str = record["period_start"][:10]  # YYYY-MM-DD
                
                if date_str not in daily_costs:
                    daily_costs[date_str] = Decimal("0")
                
                daily_costs[date_str] += Decimal(str(record.get("estimated_cost", 0)))
        
        # Fill in missing days with zero
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str not in daily_costs:
                daily_costs[date_str] = Decimal("0")
            current_date += timedelta(days=1)
        
        return dict(sorted(daily_costs.items()))
    
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
            Detailed usage statistics for the service
        """
        return await self.get_usage_summary(start_date, end_date, service_name)
    
    async def estimate_monthly_cost(self, based_on_days: int = 7) -> Decimal:
        """Estimate monthly cost based on recent usage.
        
        Args:
            based_on_days: Number of recent days to base estimate on
            
        Returns:
            Estimated monthly cost
        """
        daily_costs = await self.get_daily_costs(based_on_days)
        
        if not daily_costs:
            return Decimal("0")
        
        # Calculate average daily cost
        total_cost = sum(daily_costs.values())
        avg_daily_cost = total_cost / Decimal(str(len(daily_costs)))
        
        # Estimate for 30 days
        estimated_monthly = avg_daily_cost * Decimal("30")
        
        return estimated_monthly