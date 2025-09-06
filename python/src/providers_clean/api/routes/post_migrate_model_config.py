from fastapi import APIRouter, HTTPException
import os

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("/migrate/model-config")
async def migrate_model_config():
    """Apply migration to add embedding_dimensions and batch_size columns to model_config table"""
    try:
        from ...infrastructure.dependencies import get_supabase_client
        
        client = get_supabase_client()
        
        # Read and execute the migration file
        migration_path = os.path.join(os.path.dirname(__file__), "../../migrations/001_add_model_config_columns.sql")
        
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        result = client.rpc('exec', {'sql': migration_sql}).execute()
        
        return {
            "status": "success",
            "message": "Model config migration applied successfully",
            "migration": "001_add_model_config_columns.sql"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )