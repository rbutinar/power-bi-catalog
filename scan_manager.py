"""
Scan Manager for Power BI Catalog
Manages scan orchestration, snapshot creation, and scan lifecycle
"""
import os
import json
import sqlite3
import subprocess
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)

class ScanStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    PROCESSING = "processing"  # Converting JSON to DB
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScanManager:
    """Manages Power BI scanning operations and snapshots"""
    
    def __init__(self, base_scan_dir: str = "scans"):
        self.base_scan_dir = Path(base_scan_dir)
        self.base_scan_dir.mkdir(exist_ok=True)
        self.active_scans: Dict[str, Dict] = {}  # scan_id -> scan_info
        
    def create_scan(self, scan_name: str = None, description: str = None) -> str:
        """
        Create a new scan instance
        
        Args:
            scan_name: Custom name for the scan (optional)
            description: Scan description (optional)
            
        Returns:
            scan_id: Unique identifier for this scan
        """
        scan_id = str(uuid.uuid4())[:8]  # Short unique ID
        timestamp = datetime.now()
        
        # Create scan name if not provided
        if not scan_name:
            scan_name = f"scan_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"
        else:
            # Sanitize scan name for filesystem
            scan_name = "".join(c for c in scan_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            scan_name = scan_name.replace(' ', '_')
            
        # Create scan directory structure
        scan_dir = self.base_scan_dir / scan_name
        scan_dir.mkdir(exist_ok=True)
        (scan_dir / "json_files").mkdir(exist_ok=True)
        
        # Create scan metadata
        scan_metadata = {
            "scan_id": scan_id,
            "scan_name": scan_name,
            "description": description or f"Power BI scan created at {timestamp.isoformat()}",
            "created_at": timestamp.isoformat(),
            "status": ScanStatus.PENDING.value,
            "progress": 0,
            "total_workspaces": 0,
            "processed_workspaces": 0,
            "total_datasets": 0,
            "processed_datasets": 0,
            "scan_dir": str(scan_dir),
            "json_dir": str(scan_dir / "json_files"),
            "db_path": str(scan_dir / f"{scan_name}.db"),
            "log_messages": [],
            "error_message": None,
            "completed_at": None
        }
        
        # Save metadata to file
        metadata_path = scan_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(scan_metadata, f, indent=2)
            
        # Track active scan
        self.active_scans[scan_id] = scan_metadata
        
        logger.info(f"Created scan '{scan_name}' with ID {scan_id}")
        return scan_id
        
    def get_scan(self, scan_id: str) -> Optional[Dict]:
        """Get scan information by ID"""
        if scan_id in self.active_scans:
            return self.active_scans[scan_id]
            
        # Try to load from disk
        for scan_dir in self.base_scan_dir.iterdir():
            if scan_dir.is_dir():
                metadata_path = scan_dir / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        if metadata.get("scan_id") == scan_id:
                            self.active_scans[scan_id] = metadata
                            return metadata
        return None
        
    def list_scans(self) -> List[Dict]:
        """List all available scans"""
        scans = []
        
        for scan_dir in self.base_scan_dir.iterdir():
            if scan_dir.is_dir():
                metadata_path = scan_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            scans.append(metadata)
                    except Exception as e:
                        logger.error(f"Error reading scan metadata from {metadata_path}: {e}")
                        
        # Sort by creation date (newest first)
        scans.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return scans
        
    def update_scan_status(self, scan_id: str, status: ScanStatus, 
                          progress: int = None, message: str = None, 
                          error: str = None, stats: Dict = None):
        """Update scan status and progress"""
        scan_info = self.get_scan(scan_id)
        if not scan_info:
            logger.error(f"Scan {scan_id} not found")
            return
            
        # Update in memory
        scan_info["status"] = status.value
        if progress is not None:
            scan_info["progress"] = progress
        if message:
            scan_info["log_messages"].append({
                "timestamp": datetime.now().isoformat(),
                "message": message
            })
        if error:
            scan_info["error_message"] = error
        if stats:
            scan_info.update(stats)
        if status in [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]:
            scan_info["completed_at"] = datetime.now().isoformat()
            
        # Save to disk
        scan_dir = Path(scan_info["scan_dir"])
        metadata_path = scan_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(scan_info, f, indent=2)
            
        logger.info(f"Updated scan {scan_id} status to {status.value}")
        
    async def start_scan(self, scan_id: str, 
                        workspace_filter: str = None,
                        workspace_id_filter: str = None,
                        dataset_filter: str = None,
                        dataset_id_filter: str = None) -> bool:
        """
        Start the Power BI scanning process
        
        Args:
            scan_id: ID of the scan to start
            workspace_filter: Filter workspaces by name
            workspace_id_filter: Filter by specific workspace ID
            dataset_filter: Filter datasets by name  
            dataset_id_filter: Filter by specific dataset ID
            
        Returns:
            bool: True if scan started successfully
        """
        scan_info = self.get_scan(scan_id)
        if not scan_info:
            logger.error(f"Scan {scan_id} not found")
            return False
            
        try:
            self.update_scan_status(scan_id, ScanStatus.RUNNING, 0, "Starting Power BI tenant scan...")
            
            # Prepare command arguments - use .venv38 for Power BI scanning
            cmd = [
                str(Path(".venv38/Scripts/python.exe").resolve()),
                "pbi_tenant_analyzer.py"
            ]
            
            # Add filters if provided
            if workspace_filter:
                cmd.extend(["--workspace", workspace_filter])
            if workspace_id_filter:
                cmd.extend(["--workspace-id", workspace_id_filter])
            if dataset_filter:
                cmd.extend(["--dataset", dataset_filter])
            if dataset_id_filter:
                cmd.extend(["--dataset-id", dataset_id_filter])
                
            # Set custom output directory for this scan
            env = os.environ.copy()
            env["OUTPUT_DIR"] = scan_info["json_dir"]
            
            logger.info(f"Starting scan command: {' '.join(cmd)}")
            logger.info(f"Working directory: {os.getcwd()}")
            logger.info(f"Environment OUTPUT_DIR: {env.get('OUTPUT_DIR')}")
            
            # Test if python executable exists
            python_path = Path(".venv38/Scripts/python.exe").resolve()
            logger.info(f"Python executable path: {python_path}")
            logger.info(f"Python executable exists: {python_path.exists()}")
            
            # Run the scanning process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=os.getcwd()
            )
            
            # Monitor the process
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.update_scan_status(
                    scan_id, ScanStatus.PROCESSING, 80, 
                    "Scan completed, processing results into database..."
                )
                
                # Import JSON files to SQLite
                success = await self._import_scan_to_db(scan_id)
                
                if success:
                    self.update_scan_status(
                        scan_id, ScanStatus.COMPLETED, 100, 
                        "Scan completed successfully!"
                    )
                    return True
                else:
                    self.update_scan_status(
                        scan_id, ScanStatus.FAILED, 80,
                        error="Failed to import scan results to database"
                    )
                    return False
            else:
                error_msg = stderr.decode() if stderr else "Unknown error occurred"
                self.update_scan_status(
                    scan_id, ScanStatus.FAILED, 0,
                    error=f"Scan failed: {error_msg}"
                )
                logger.error(f"Scan {scan_id} failed: {error_msg}")
                return False
                
        except Exception as e:
            import traceback
            error_msg = f"Exception during scan: {str(e)}"
            full_traceback = traceback.format_exc()
            logger.error(f"Scan {scan_id} failed with exception: {error_msg}")
            logger.error(f"Full traceback: {full_traceback}")
            self.update_scan_status(scan_id, ScanStatus.FAILED, 0, error=f"{error_msg}\n\nTraceback:\n{full_traceback}")
            return False
            
    async def _import_scan_to_db(self, scan_id: str) -> bool:
        """Import scan JSON files to SQLite database"""
        scan_info = self.get_scan(scan_id)
        if not scan_info:
            return False
            
        try:
            # Import database modules
            from database.schema import create_schema
            from database.json_importer import JsonToSqliteImporter
            
            db_path = scan_info["db_path"]
            json_dir = scan_info["json_dir"]
            
            # Create database schema
            create_schema(db_path)
            
            # Import JSON files
            with JsonToSqliteImporter(db_path) as importer:
                success = importer.import_tenant_analysis(json_dir)
                
            if success:
                self.update_scan_status(
                    scan_id, ScanStatus.PROCESSING, 90,
                    "Database import completed successfully"
                )
                return True
            else:
                logger.error(f"Failed to import JSON files for scan {scan_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error importing scan {scan_id} to database: {e}")
            return False
            
    def delete_scan(self, scan_id: str) -> bool:
        """Delete a scan and all its data"""
        scan_info = self.get_scan(scan_id)
        if not scan_info:
            return False
            
        try:
            # Remove from active scans
            if scan_id in self.active_scans:
                del self.active_scans[scan_id]
                
            # Remove scan directory
            scan_dir = Path(scan_info["scan_dir"])
            if scan_dir.exists():
                shutil.rmtree(scan_dir)
                
            logger.info(f"Deleted scan {scan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting scan {scan_id}: {e}")
            return False
            
    def get_scan_database(self, scan_id: str) -> Optional[str]:
        """Get the database path for a specific scan"""
        scan_info = self.get_scan(scan_id)
        if scan_info and scan_info.get("status") == ScanStatus.COMPLETED.value:
            db_path = scan_info["db_path"]
            if os.path.exists(db_path):
                return db_path
        return None

# Global scan manager instance
scan_manager = ScanManager()