"""Background service for scheduled model synchronization."""

import asyncio
import logging
from typing import Optional
from datetime import datetime, time
from ..infrastructure.dependencies import DependencyContainer
from .model_sync_service import ModelSyncService


logger = logging.getLogger(__name__)


class BackgroundModelSync:
    """Service for running scheduled model synchronization in the background."""
    
    def __init__(self):
        """Initialize background sync service."""
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
        self._sync_interval_hours = 24  # Sync once per day
    
    async def start_scheduled_sync(self):
        """Start the background sync task."""
        if self._running:
            logger.warning("Background sync is already running")
            return
        
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Background model sync started (daily schedule)")
    
    async def stop_scheduled_sync(self):
        """Stop the background sync task."""
        self._running = False
        
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                logger.info("Background sync task cancelled")
        
        logger.info("Background model sync stopped")
    
    async def _sync_loop(self):
        """Main background sync loop."""
        logger.info(f"Starting background sync loop (interval: {self._sync_interval_hours} hours)")
        
        while self._running:
            try:
                # Perform the sync
                await self._perform_sync()
                
                # Wait for next sync (24 hours)
                await asyncio.sleep(self._sync_interval_hours * 3600)
                
            except asyncio.CancelledError:
                logger.info("Background sync loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background sync loop: {e}")
                # Wait a shorter time before retrying on error
                await asyncio.sleep(3600)  # 1 hour retry delay
    
    async def _perform_sync(self):
        """Perform a single sync operation."""
        try:
            logger.info("Starting scheduled model sync...")
            
            # Get dependency container and sync service
            container = DependencyContainer.get_instance()
            sync_service = ModelSyncService(container.unit_of_work)
            
            # Check if sync is needed
            should_sync = await sync_service.should_sync(max_age_hours=self._sync_interval_hours)
            
            if should_sync:
                # Perform full sync
                result = await sync_service.full_sync(force_refresh=False)
                
                if result['status'] == 'success':
                    logger.info(
                        f"Scheduled sync completed successfully: "
                        f"{result['total_models_synced']} models synced, "
                        f"{result.get('models_deactivated', 0)} deactivated"
                    )
                else:
                    logger.warning(f"Scheduled sync completed with issues: {result}")
            else:
                logger.info("Scheduled sync skipped - data is still fresh")
                
        except Exception as e:
            logger.error(f"Failed to perform scheduled sync: {e}")
    
    async def trigger_immediate_sync(self, force_refresh: bool = False) -> dict:
        """Trigger an immediate sync operation.
        
        Args:
            force_refresh: If True, force fresh data fetch from APIs
            
        Returns:
            Sync result dictionary
        """
        try:
            logger.info(f"Triggering immediate sync (force_refresh={force_refresh})")
            
            # Get dependency container and sync service
            container = DependencyContainer.get_instance()
            sync_service = ModelSyncService(container.unit_of_work)
            
            # Perform sync
            result = await sync_service.full_sync(force_refresh=force_refresh)
            
            logger.info(f"Immediate sync completed: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            error_msg = f"Immediate sync failed: {str(e)}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg,
                'sync_time': datetime.now().isoformat()
            }
    
    def is_running(self) -> bool:
        """Check if background sync is currently running.
        
        Returns:
            True if sync task is running
        """
        return self._running and self._sync_task and not self._sync_task.done()
    
    def get_status(self) -> dict:
        """Get current status of background sync service.
        
        Returns:
            Status dictionary
        """
        return {
            'running': self.is_running(),
            'sync_interval_hours': self._sync_interval_hours,
            'last_check': datetime.now().isoformat()
        }


# Global instance for background sync management
_background_sync: Optional[BackgroundModelSync] = None


async def get_background_sync() -> BackgroundModelSync:
    """Get or create the global background sync instance.
    
    Returns:
        BackgroundModelSync instance
    """
    global _background_sync
    if _background_sync is None:
        _background_sync = BackgroundModelSync()
    return _background_sync


async def start_background_model_sync():
    """Start the global background model sync service."""
    sync_service = await get_background_sync()
    await sync_service.start_scheduled_sync()


async def stop_background_model_sync():
    """Stop the global background model sync service."""
    global _background_sync
    if _background_sync:
        await _background_sync.stop_scheduled_sync()
        _background_sync = None