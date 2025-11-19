"""dbt model generation utilities."""

from typing import List
from pathlib import Path
from models.schemas import DataVaultModel, HubDefinition, LinkDefinition, SatelliteDefinition


class DBTGenerator:
    """Generate dbt models from Data Vault specifications."""
    
    def __init__(self, project_dir: str = "./dbt_project"):
        """
        Initialize dbt generator.
        
        Args:
            project_dir: dbt project directory
        """
        self.project_dir = Path(project_dir)
        self.models_dir = self.project_dir / "models" / "silver"
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_hub_model(self, hub: HubDefinition) -> str:
        """Generate dbt SQL for a Hub."""
        sql = f"""-- Hub: {hub.name}
-- Business Key: {hub.business_key}
-- Source: {hub.source_table}

{{{{ config(
    materialized='incremental',
    unique_key='{hub.business_key}',
    incremental_strategy='merge',
    merge_update_columns=['LOAD_TIMESTAMP']
) }}}}

SELECT DISTINCT
    {hub.business_key} AS HUB_KEY,
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM {{{{ ref('{hub.source_table}') }}}}

{{% if is_incremental() %}}
WHERE LOAD_TIMESTAMP > (SELECT MAX(LOAD_TIMESTAMP) FROM {{{{ this }}}})
{{% endif %}}
"""
        return sql
    
    def generate_link_model(self, link: LinkDefinition) -> str:
        """Generate dbt SQL for a Link."""
        # For simplicity, assuming link connects two hubs
        hub_refs = ", ".join([f"hub.{hub}_KEY" for hub in link.hub_keys])
        hub_keys_str = ", ".join([f"'{hub}'" for hub in link.hub_keys])
        
        # Build JOIN clauses
        join_clauses = "\n".join([
            f"JOIN {{{{ ref('{hub}') }}}} hub_{i} ON ..."
            for i, hub in enumerate(link.hub_keys)
        ])
        
        sql = f"""-- Link: {link.name}
-- Connects: {', '.join(link.hub_keys)}

{{{{ config(
    materialized='incremental',
    unique_key='LINK_KEY',
    incremental_strategy='merge'
) }}}}

SELECT DISTINCT
    MD5({hub_refs}) AS LINK_KEY,
    {hub_refs},
    CURRENT_TIMESTAMP() AS LOAD_TIMESTAMP
FROM {{{{ ref('{link.source_tables[0]}') }}}} src
{join_clauses}

{{% if is_incremental() %}}
WHERE LOAD_TIMESTAMP > (SELECT MAX(LOAD_TIMESTAMP) FROM {{{{ this }}}})
{{% endif %}}
"""
        return sql
    
    def generate_satellite_model(self, satellite: SatelliteDefinition) -> str:
        """Generate dbt SQL for a Satellite (SCD Type 2)."""
        parent_ref = satellite.parent_hub or satellite.parent_link
        attributes = ", ".join(satellite.attributes)
        
        sql = f"""-- Satellite: {satellite.name}
-- Parent: {parent_ref}
-- Attributes: {attributes}

{{{{ config(
    materialized='incremental',
    unique_key=['PARENT_KEY', '{satellite.effective_date_column}'],
    incremental_strategy='merge'
) }}}}

SELECT
    parent.HUB_KEY AS PARENT_KEY,
    {attributes},
    CURRENT_TIMESTAMP() AS {satellite.effective_date_column},
    NULL AS {satellite.end_date_column or 'END_DATE'}
FROM {{{{ ref('{satellite.parent_hub or satellite.parent_link}') }}}} parent
JOIN {{{{ ref('source_table') }}}} src ON ...

{{% if is_incremental() %}}
WHERE src.LOAD_TIMESTAMP > (SELECT MAX({satellite.effective_date_column}) FROM {{{{ this }}}})
{{% endif %}}
"""
        return sql
    
    def save_model(self, model_name: str, sql_content: str):
        """Save dbt model to file."""
        model_file = self.models_dir / f"{model_name}.sql"
        model_file.write_text(sql_content)
    
    def generate_all_models(self, datavault_model: DataVaultModel):
        """Generate all dbt models for a Data Vault model."""
        # Generate Hub models
        for hub in datavault_model.hubs:
            sql = self.generate_hub_model(hub)
            self.save_model(hub.name.lower(), sql)
        
        # Generate Link models
        for link in datavault_model.links:
            sql = self.generate_link_model(link)
            self.save_model(link.name.lower(), sql)
        
        # Generate Satellite models
        for satellite in datavault_model.satellites:
            sql = self.generate_satellite_model(satellite)
            self.save_model(satellite.name.lower(), sql)
