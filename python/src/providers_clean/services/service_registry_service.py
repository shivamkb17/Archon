"""Service for managing the service/agent registry and LLM usage tracking."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from ..core.interfaces.unit_of_work import IUnitOfWork


logger = logging.getLogger(__name__)


class ServiceRegistration(BaseModel):
    """Data model for service registration."""
    service_name: str = Field(..., description="Unique service identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Service description")
    icon: Optional[str] = Field(None, description="Emoji or icon")
    category: str = Field(..., description="agent or service")
    service_type: str = Field(..., description="pydantic_ai, backend_service, or embedding_service")
    model_type: str = Field(..., description="llm or embedding")
    location: Optional[str] = Field(None, description="Where service runs")
    supports_temperature: bool = Field(True, description="Supports temperature parameter")
    supports_max_tokens: bool = Field(True, description="Supports max_tokens parameter")
    default_model: Optional[str] = Field(None, description="Default model string")
    cost_profile: Optional[str] = Field("medium", description="Expected cost tier")
    owner_team: Optional[str] = Field(None, description="Owning team")
    contact_email: Optional[str] = Field(None, description="Contact for issues")
    documentation_url: Optional[str] = Field(None, description="Documentation link")


class ServiceInfo(BaseModel):
    """Complete service information from registry."""
    id: str
    service_name: str
    display_name: str
    description: Optional[str]
    icon: Optional[str]
    category: str
    service_type: str
    model_type: str
    location: Optional[str]
    supports_temperature: bool
    supports_max_tokens: bool
    default_model: Optional[str]
    cost_profile: Optional[str]
    is_active: bool
    is_deprecated: bool
    deprecation_reason: Optional[str]
    replacement_service: Optional[str]
    owner_team: Optional[str]
    contact_email: Optional[str]
    documentation_url: Optional[str]
    first_seen: Optional[datetime]
    last_used: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ServiceRegistryService:
    """Service for managing the registry of all services and agents using LLMs."""
    
    def __init__(self, uow: IUnitOfWork):
        """Initialize with Unit of Work.
        
        Args:
            uow: Unit of Work instance for database access
        """
        self.uow = uow
    
    async def register_service(self, registration: ServiceRegistration) -> ServiceInfo:
        """Register or update a service in the registry.
        
        Args:
            registration: Service registration data
            
        Returns:
            Complete service information after registration
        """
        try:
            async with self.uow as uow:
                # Convert ServiceRegistration to dict for repository
                service_data = registration.model_dump()
                
                # Use repository to register service
                service_id = await uow.service_registry.register_service(service_data)
                
                # Get the updated service info
                return await self.get_service(registration.service_name)
                
        except Exception as e:
            logger.error(f"Failed to register service {registration.service_name}: {e}")
            raise e
    
    async def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get service information by name.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service information or None if not found
        """
        try:
            async with self.uow as uow:
                service_data = await uow.service_registry.get_service(service_name)
                
                if service_data:
                    return ServiceInfo(**service_data)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            return None
    
    async def get_all_services(self, active_only: bool = True, category: Optional[str] = None) -> List[ServiceInfo]:
        """Get all services from the registry.
        
        Args:
            active_only: If True, only return active services
            category: Optional filter by category ('agent' or 'service')
            
        Returns:
            List of service information
        """
        try:
            async with self.uow as uow:
                if category:
                    # Use the specific category method
                    services_data = await uow.service_registry.get_services_by_category(category, active_only)
                else:
                    # Use the general get_all method
                    services_data = await uow.service_registry.get_all_services(active_only)
                
                return [ServiceInfo(**data) for data in services_data]
                
        except Exception as e:
            logger.error(f"Failed to get all services: {e}")
            return []
    
    async def get_agents(self, active_only: bool = True) -> List[ServiceInfo]:
        """Get all PydanticAI agents from the registry.
        
        Args:
            active_only: If True, only return active agents
            
        Returns:
            List of agent information
        """
        try:
            async with self.uow as uow:
                services_data = await uow.service_registry.get_services_by_category('agent', active_only)
                return [ServiceInfo(**data) for data in services_data]
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            return []
    
    async def get_backend_services(self, active_only: bool = True) -> List[ServiceInfo]:
        """Get all backend services from the registry.
        
        Args:
            active_only: If True, only return active services
            
        Returns:
            List of backend service information
        """
        try:
            async with self.uow as uow:
                services_data = await uow.service_registry.get_services_by_category('service', active_only)
                return [ServiceInfo(**data) for data in services_data]
        except Exception as e:
            logger.error(f"Failed to get backend services: {e}")
            return []
    
    async def get_services_by_team(self, team: str, active_only: bool = True) -> List[ServiceInfo]:
        """Get services owned by a specific team.
        
        Args:
            team: Team name
            active_only: If True, only return active services
            
        Returns:
            List of services owned by the team
        """
        try:
            async with self.uow as uow:
                query = uow.db.table('service_registry').select('*').eq('owner_team', team)
                
                if active_only:
                    query = query.eq('is_active', True).eq('is_deprecated', False)
                
                response = query.order('category', 'display_name').execute()
                return [ServiceInfo(**data) for data in (response.data or [])]
                
        except Exception as e:
            logger.error(f"Failed to get services for team {team}: {e}")
            return []
    
    async def deprecate_service(
        self, 
        service_name: str, 
        reason: str, 
        replacement_service: Optional[str] = None
    ) -> bool:
        """Mark a service as deprecated.
        
        Args:
            service_name: Name of service to deprecate
            reason: Reason for deprecation
            replacement_service: Optional replacement service
            
        Returns:
            True if deprecated successfully
        """
        try:
            async with self.uow as uow:
                response = uow.db.rpc('deprecate_service', {
                    'p_service_name': service_name,
                    'p_reason': reason,
                    'p_replacement': replacement_service
                }).execute()
                
                result = response.data
                if result:
                    logger.info(f"Deprecated service {service_name}: {reason}")
                    return True
                else:
                    logger.warning(f"Service not found for deprecation: {service_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to deprecate service {service_name}: {e}")
            return False

    async def update_default_model(self, service_name: str, model_string: str) -> bool:
        """Update the registry's default_model for a service.

        Args:
            service_name: Service identifier
            model_string: New default model string

        Returns:
            True if the registry entry was updated.
        """
        try:
            async with self.uow as uow:
                updated = await uow.service_registry.update_service_metadata(
                    service_name, {"default_model": model_string}
                )
                return updated
        except Exception as e:
            logger.warning(
                f"Failed to update default_model in registry for {service_name}: {e}"
            )
            return False
    
    async def discover_unregistered_services(self) -> List[Dict[str, Any]]:
        """Discover services that have model configurations but no registry entries.
        
        Returns:
            List of unregistered services found in model_config
        """
        try:
            async with self.uow as uow:
                response = uow.db.from_('unregistered_services').select('*').execute()
                return response.data or []
                
        except Exception as e:
            logger.error(f"Failed to discover unregistered services: {e}")
            return []
    
    async def find_orphaned_registry_entries(self) -> List[Dict[str, Any]]:
        """Find registry entries that don't have corresponding model configurations.
        
        Returns:
            List of registry entries without model configs
        """
        try:
            async with self.uow as uow:
                response = uow.db.from_('unconfigured_services').select('*').execute()
                return response.data or []
                
        except Exception as e:
            logger.error(f"Failed to find orphaned registry entries: {e}")
            return []
    
    async def get_registry_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the service registry.
        
        Returns:
            Dictionary with registry statistics
        """
        try:
            async with self.uow as uow:
                # Get counts by category and type
                all_services = await self.get_all_services(active_only=False)
                active_services = await self.get_all_services(active_only=True)
                agents = await self.get_agents(active_only=True)
                backend_services = await self.get_backend_services(active_only=True)
                
                # Get validation info
                unregistered = await self.discover_unregistered_services()
                orphaned = await self.find_orphaned_registry_entries()
                
                # Get deprecated services
                deprecated_response = uow.db.from_('deprecated_services').select('*').execute()
                deprecated_services = deprecated_response.data or []
                
                # Group by team
                team_counts = {}
                for service in active_services:
                    team = service.owner_team or 'unassigned'
                    team_counts[team] = team_counts.get(team, 0) + 1
                
                # Group by cost profile
                cost_profile_counts = {}
                for service in active_services:
                    profile = service.cost_profile or 'unknown'
                    cost_profile_counts[profile] = cost_profile_counts.get(profile, 0) + 1
                
                return {
                    'total_services': len(all_services),
                    'active_services': len(active_services),
                    'deprecated_services': len([s for s in all_services if s.is_deprecated]),
                    'agents': len(agents),
                    'backend_services': len(backend_services),
                    'unregistered_services': len(unregistered),
                    'orphaned_registry_entries': len(orphaned),
                    'deprecated_needing_cleanup': len(deprecated_services),
                    'services_by_team': team_counts,
                    'services_by_cost_profile': cost_profile_counts,
                    'validation_issues': {
                        'unregistered': unregistered,
                        'orphaned': orphaned,
                        'deprecated': deprecated_services
                    },
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get registry statistics: {e}")
            return {'error': str(e)}
    
    async def bulk_register_from_agent_configs(self, agent_configs: List[Dict[str, Any]]) -> int:
        """Bulk register services from frontend AGENT_CONFIGS data.
        
        Args:
            agent_configs: List of agent config dictionaries
            
        Returns:
            Number of services registered
        """
        registered_count = 0
        
        for config in agent_configs:
            try:
                # Map agent config to service registration
                registration = ServiceRegistration(
                    service_name=config['id'],
                    display_name=config['name'], 
                    description=config['description'],
                    icon=config['icon'],
                    category=config['category'],
                    service_type='pydantic_ai' if config['category'] == 'agent' else 'backend_service',
                    model_type=config['modelType'],
                    location='agents_server' if config['category'] == 'agent' else 'main_server',
                    supports_temperature=config['supportsTemperature'],
                    supports_max_tokens=config['supportsMaxTokens'], 
                    default_model=config['defaultModel'],
                    cost_profile=config['costProfile'],
                    owner_team='core'  # Default team
                )
                
                await self.register_service(registration)
                registered_count += 1
                
            except Exception as e:
                logger.error(f"Failed to register service from config {config.get('id', 'unknown')}: {e}")
        
        logger.info(f"Bulk registered {registered_count}/{len(agent_configs)} services from AGENT_CONFIGS")
        return registered_count
    
    async def sync_registry_with_model_configs(self) -> Dict[str, Any]:
        """Ensure all services with model configs are registered.
        
        Returns:
            Sync results with statistics
        """
        try:
            # Discover unregistered services
            unregistered = await self.discover_unregistered_services()
            registered_count = 0
            
            for service_info in unregistered:
                try:
                    # Derive category and types from naming/model heuristics
                    service_name = service_info['service_name']
                    model_string = service_info['model_string']

                    is_agent = service_name.endswith('_agent') or service_name.startswith('agent_')
                    is_embedding = ('embedding' in service_name) or ('embedding' in model_string)

                    if is_agent:
                        category = 'agent'
                        service_type = 'pydantic_ai'
                        model_type = 'llm'
                        location = 'agents_server'
                        supports_temperature = True
                        supports_max_tokens = True
                        icon = '🤖'
                    elif is_embedding:
                        category = 'service'
                        service_type = 'embedding_service'
                        model_type = 'embedding'
                        location = 'main_server'
                        supports_temperature = False
                        supports_max_tokens = False
                        icon = '🧩'
                    else:
                        category = 'service'
                        service_type = 'backend_service'
                        model_type = 'llm'
                        location = 'main_server'
                        supports_temperature = True
                        supports_max_tokens = True
                        icon = '🔧'

                    # Create registration for unregistered service
                    registration = ServiceRegistration(
                        service_name=service_name,
                        display_name=service_name.replace('_', ' ').title(),
                        description=f"Auto-discovered using {model_string}",
                        icon=icon,
                        category=category,
                        service_type=service_type,
                        model_type=model_type,
                        location=location,
                        supports_temperature=supports_temperature,
                        supports_max_tokens=supports_max_tokens,
                        default_model=model_string,
                        cost_profile='medium',
                        owner_team='auto-discovered'
                    )
                    
                    await self.register_service(registration)
                    registered_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to auto-register service {service_info['service_name']}: {e}")
            
            return {
                'status': 'success',
                'services_discovered': len(unregistered),
                'services_registered': registered_count,
                'sync_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync registry with model configs: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'sync_time': datetime.now().isoformat()
            }
    
    async def update_service_last_used(self, service_name: str) -> None:
        """Update the last_used timestamp for a service.
        
        Args:
            service_name: Name of the service that was used
        """
        try:
            async with self.uow as uow:
                uow.db.rpc('update_service_last_used', {
                    'p_service_name': service_name
                }).execute()
                
        except Exception as e:
            # Don't raise error for usage tracking - just log
            logger.warning(f"Failed to update last_used for service {service_name}: {e}")
    
    async def get_usage_summary_by_service(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage summary grouped by service with registry metadata.
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            List of service usage summaries with metadata
        """
        try:
            async with self.uow as uow:
                # Use the enhanced_model_usage view that includes registry metadata
                from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                
                response = uow.db.from_('enhanced_model_usage').select(
                    'service_name, service_display_name, category, service_type, '
                    'model_type, cost_profile, owner_team, location, '
                    'sum(request_count) as total_requests, '
                    'sum(total_tokens) as total_tokens, '
                    'sum(estimated_cost) as total_cost, '
                    'avg(avg_tokens_per_request) as avg_tokens_per_request'
                ).gte(
                    'period_start', (from_date - datetime.timedelta(days=days)).isoformat()
                ).group_by(
                    'service_name, service_display_name, category, service_type, '
                    'model_type, cost_profile, owner_team, location'
                ).order('total_cost', desc=True).execute()
                
                return response.data or []
                
        except Exception as e:
            logger.error(f"Failed to get usage summary by service: {e}")
            return []
    
    async def get_services_by_cost_profile(self, cost_profile: str, active_only: bool = True) -> List[ServiceInfo]:
        """Get services filtered by cost profile.
        
        Args:
            cost_profile: Cost profile ('low', 'medium', 'high')
            active_only: If True, only return active services
            
        Returns:
            List of services with the specified cost profile
        """
        try:
            async with self.uow as uow:
                query = uow.db.table('service_registry').select('*').eq('cost_profile', cost_profile)
                
                if active_only:
                    query = query.eq('is_active', True).eq('is_deprecated', False)
                
                response = query.order('display_name').execute()
                return [ServiceInfo(**data) for data in (response.data or [])]
                
        except Exception as e:
            logger.error(f"Failed to get services by cost profile {cost_profile}: {e}")
            return []
    
    async def validate_registry_completeness(self) -> Dict[str, Any]:
        """Validate that the registry is complete and consistent.
        
        Returns:
            Validation report with issues found
        """
        try:
            # Get validation data
            unregistered = await self.discover_unregistered_services()
            orphaned = await self.find_orphaned_registry_entries()
            
            # Check for deprecated services still being used
            deprecated_services = await self.get_all_services(active_only=False, category=None)
            deprecated_still_configured = [
                s for s in deprecated_services 
                if s.is_deprecated and s.last_used and 
                (datetime.now() - s.last_used).days < 7  # Used in last week
            ]
            
            issues = []
            warnings = []
            
            if unregistered:
                issues.append(f"{len(unregistered)} services have model configs but no registry entries")
            
            if orphaned:
                warnings.append(f"{len(orphaned)} registry entries have no model configurations")
            
            if deprecated_still_configured:
                issues.append(f"{len(deprecated_still_configured)} deprecated services still being used")
            
            validation_status = 'clean' if not issues and not warnings else 'issues_found'
            
            return {
                'status': validation_status,
                'issues': issues,
                'warnings': warnings,
                'unregistered_services': unregistered,
                'orphaned_entries': orphaned,
                'deprecated_still_used': [
                    {
                        'service_name': s.service_name,
                        'display_name': s.display_name,
                        'last_used': s.last_used.isoformat() if s.last_used else None,
                        'replacement': s.replacement_service
                    }
                    for s in deprecated_still_configured
                ],
                'validation_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate registry completeness: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'validation_time': datetime.now().isoformat()
            }
