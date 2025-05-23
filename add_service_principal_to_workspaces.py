"""
Add Service Principal to Power BI Workspaces
-------------------------------------------
Script to add a service principal with contributor role to multiple Power BI workspaces.
"""
import os
import sys
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Import from our existing modules
from clients.rest_client import PowerBIRestClient
from pbi_tenant_analyzer import log, get_access_token, get_workspaces

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def verify_workspace_access(token, workspace_id):
    """
    Verify if the current user has access to the workspace.
    
    Args:
        token (str): Power BI access token
        workspace_id (str): ID of the workspace to check
        
    Returns:
        tuple: (bool, str) - (has_access, error_message)
    """
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return True, ""
    except requests.exceptions.HTTPError as e:
        error_message = f"Error accessing workspace: {str(e)}"
        try:
            error_details = response.json().get('error', {})
            error_message += f" - {error_details.get('code', '')}: {error_details.get('message', '')}"
        except:
            pass
        return False, error_message
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def add_service_principal_to_workspace(token, workspace_id, service_principal_id, principal_type="App", principal_access="Contributor"):
    """
    Add a service principal to a workspace with specified access level.
    
    Args:
        token (str): Power BI access token
        workspace_id (str): ID of the workspace to add the service principal to
        service_principal_id (str): Object ID of the service principal in Azure AD
        principal_type (str): Type of principal (default: "App" for service principals)
        principal_access (str): Access level (Admin, Contributor, Member, Viewer)
        
    Returns:
        tuple: (bool, str) - (success, error_message)
    """
    # First verify we have access to the workspace
    has_access, error_message = verify_workspace_access(token, workspace_id)
    if not has_access:
        return False, error_message
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Payload for adding service principal
    payload = {
        "identifier": service_principal_id,
        "principalType": principal_type,
        "groupUserAccessRight": principal_access
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True, ""
    except requests.exceptions.HTTPError as e:
        if response.status_code == 409:
            # User already exists in the workspace
            return True, "Service principal already exists in workspace"
        else:
            error_message = f"Failed to add service principal: {str(e)}"
            try:
                error_details = response.json().get('error', {})
                error_message += f" - {error_details.get('code', '')}: {error_details.get('message', '')}"
            except:
                pass
            return False, error_message
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def refresh_workspaces(token):
    """
    Get an updated list of workspaces from the Power BI API.
    
    Args:
        token (str): Power BI access token
        
    Returns:
        list: List of workspace dictionaries
    """
    url = "https://api.powerbi.com/v1.0/myorg/groups"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        workspaces = response.json().get('value', [])
        log(f"Successfully refreshed workspace list: found {len(workspaces)} workspaces")
        return workspaces
    except Exception as e:
        log(f"Error refreshing workspace list: {str(e)}")
        return []

def process_workspaces(token, service_principal_id, workspace_filter=None, workspace_id_filter=None, 
                    dry_run=False, access_level="Contributor", verify_only=False, refresh=False):
    """
    Process workspaces and add service principal to each.
    
    Args:
        token (str): Power BI access token
        service_principal_id (str): Object ID of the service principal in Azure AD
        workspace_filter (str, optional): Filter workspaces by name (case-insensitive partial match)
        workspace_id_filter (str, optional): Filter by exact workspace ID
        dry_run (bool): If True, only list workspaces without making changes
        access_level (str): Access level to grant (Admin, Contributor, Member, Viewer)
        verify_only (bool): If True, only verify access to workspaces without adding service principal
        refresh (bool): If True, refresh the workspace list directly from the API
        
    Returns:
        dict: Summary of operations
    """
    # Get all workspaces
    log(f"Fetching all workspaces...")
    if refresh:
        workspaces = refresh_workspaces(token)
    else:
        workspaces = get_workspaces(token)
    log(f"Found {len(workspaces)} workspaces")
    
    # Filter workspaces if needed
    if workspace_filter:
        workspaces = [w for w in workspaces if workspace_filter.lower() in w.get("name", "").lower()]
        log(f"Filtered to {len(workspaces)} workspaces matching '{workspace_filter}'")
    
    if workspace_id_filter:
        workspaces = [w for w in workspaces if w.get("id") == workspace_id_filter]
        log(f"Filtered to {len(workspaces)} workspaces with ID '{workspace_id_filter}'")
    
    # Summary
    summary = {
        "total_workspaces": len(workspaces),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "workspaces": []
    }
    
    # Process each workspace
    for workspace in workspaces:
        workspace_summary = {
            "id": workspace["id"],
            "name": workspace["name"],
            "status": "skipped" if dry_run else "pending",
            "error": ""
        }
        
        log(f"Processing workspace: {workspace['name']} ({workspace['id']})")
        
        if dry_run:
            log(f"  [DRY RUN] Would add service principal to workspace")
            workspace_summary["status"] = "skipped"
            summary["skipped"] += 1
        elif verify_only:
            has_access, error = verify_workspace_access(token, workspace["id"])
            if has_access:
                log(f"  ✓ Successfully verified access to workspace")
                workspace_summary["status"] = "verified"
                summary["successful"] += 1
            else:
                log(f"  ✗ Failed to verify access to workspace: {error}")
                workspace_summary["status"] = "failed"
                workspace_summary["error"] = error
                summary["failed"] += 1
        else:
            success, error = add_service_principal_to_workspace(
                token, 
                workspace["id"], 
                service_principal_id,
                principal_access=access_level
            )
            
            if success:
                log(f"  ✓ Successfully added service principal to workspace")
                workspace_summary["status"] = "success"
                summary["successful"] += 1
            else:
                log(f"  ✗ Failed to add service principal to workspace: {error}")
                workspace_summary["status"] = "failed"
                workspace_summary["error"] = error
                summary["failed"] += 1
        
        summary["workspaces"].append(workspace_summary)
        
        # Small delay to avoid throttling
        time.sleep(0.5)
    
    return summary

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Add service principal to Power BI workspaces')
    
    # Service principal ID (required unless verify-only)
    parser.add_argument('--service-principal-id', help='Object ID of the service principal (from Azure AD). If not provided, will use OBJECT_ID from .env')
    
    # Filters
    parser.add_argument('--workspace', help='Filter by workspace name (case-insensitive partial match)')
    parser.add_argument('--workspace-id', help='Filter by exact workspace ID')
    
    # Access level
    parser.add_argument('--access-level', default='Contributor', 
                        choices=['Admin', 'Contributor', 'Member', 'Viewer'],
                        help='Access level to grant (default: Contributor)')
    
    # Dry run
    parser.add_argument('--dry-run', action='store_true', 
                        help='List workspaces without making changes')
    
    # Verify only
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify access to workspaces without adding service principal')
    
    # Refresh workspace list
    parser.add_argument('--refresh', action='store_true',
                        help='Refresh workspace list directly from the API')
    
    # List accessible workspaces
    parser.add_argument('--list-accessible', action='store_true',
                        help='List only workspaces the service principal has access to')
    
    # Output
    parser.add_argument('--output', help='Path to save summary JSON file')
    
    args = parser.parse_args()
    
    # If service_principal_id is not provided, try to load from environment
    if not (args.verify_only or args.list_accessible):
        if not args.service_principal_id:
            env_object_id = os.getenv('OBJECT_ID')
            if env_object_id:
                args.service_principal_id = env_object_id
            else:
                parser.error("--service-principal-id not provided and OBJECT_ID not set in .env. Please provide one.")
    
    # Get access token
    token = get_access_token()
    
    # If list-accessible is specified, verify access to all workspaces and show only accessible ones
    if args.list_accessible:
        log("Listing accessible workspaces...")
        args.verify_only = True
    
    # Process workspaces
    summary = process_workspaces(
        token,
        args.service_principal_id,
        workspace_filter=args.workspace,
        workspace_id_filter=args.workspace_id,
        dry_run=args.dry_run,
        access_level=args.access_level,
        verify_only=args.verify_only,
        refresh=args.refresh
    )
    
    # Print summary
    log("\nSummary:")
    log(f"Total workspaces: {summary['total_workspaces']}")
    log(f"Successful: {summary['successful']}")
    log(f"Failed: {summary['failed']}")
    log(f"Skipped: {summary['skipped']}")
    
    # If list-accessible is specified, show only accessible workspaces
    if args.list_accessible and summary['workspaces']:
        accessible_workspaces = [w for w in summary['workspaces'] if w['status'] == 'verified']
        if accessible_workspaces:
            log("\nAccessible workspaces:")
            for i, workspace in enumerate(accessible_workspaces, 1):
                log(f"{i}. {workspace['name']} ({workspace['id']})")
        else:
            log("\nNo accessible workspaces found.")
    
    # Save summary to file if requested
    if args.output:
        output_path = args.output
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        log(f"\nSummary saved to {output_path}")

if __name__ == "__main__":
    main()
