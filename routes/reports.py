# labmanagement/routes/reports.py
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------
# SINGLETON PATTERN - Configuration Manager
# ---------------------------------------
class ConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration"""
        self._config = {
            'upload_folder': UPLOAD_FOLDER,
            'allowed_extensions': ALLOWED_EXTENSIONS,
            'max_file_size': MAX_FILE_SIZE,
            'allowed_mime_types': {'application/pdf'},
            'backup_folder': os.path.join(UPLOAD_FOLDER, 'backups')
        }
        
        # Create backup directory
        os.makedirs(self._config['backup_folder'], exist_ok=True)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self._config[key] = value
    
    def get_upload_path(self, filename):
        """Get full upload path for filename"""
        return os.path.join(self.get('upload_folder'), filename)

# ---------------------------------------
# FACTORY PATTERN - Response Factory
# ---------------------------------------
class ResponseFactory:
    @staticmethod
    def create_response(response_type, data=None, message=None, errors=None, metadata=None):
        """Factory method to create standardized API responses"""
        base_response = {
            "timestamp": datetime.now().isoformat(),
            "success": response_type == "success",
            "version": "1.0"
        }
        
        if response_type == "success":
            if data is not None:
                base_response["data"] = data
            if message:
                base_response["message"] = message
            if metadata:
                base_response["metadata"] = metadata
                
        elif response_type == "error":
            if errors:
                base_response["errors"] = errors if isinstance(errors, list) else [errors]
            if message:
                base_response["message"] = message
                
        else:  # info response
            base_response["message"] = message or "Request processed"
            if data is not None:
                base_response["data"] = data
        
        return base_response

# ---------------------------------------
# REPOSITORY PATTERN for File Management
# ---------------------------------------
class ReportRepository:
    def __init__(self):
        self.config = ConfigManager()
        self.upload_folder = Path(self.config.get('upload_folder'))
    
    def validate_file(self, file):
        """Validate uploaded file"""
        errors = []
        
        # Check if file exists
        if not file or file.filename == '':
            errors.append("No file selected")
            return errors
        
        # Check file extension
        if not self._allowed_file(file.filename):
            allowed_types = ', '.join(self.config.get('allowed_extensions'))
            errors.append(f"Invalid file type. Allowed types: {allowed_types}")
        
        # Check file size
        try:
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset seek position
            if file_size > self.config.get('max_file_size'):
                max_mb = self.config.get('max_file_size') // (1024 * 1024)
                errors.append(f"File size too large. Maximum allowed: {max_mb}MB")
        except Exception as e:
            errors.append("Unable to determine file size")
        
        return errors
    
    def validate_patient_id(self, patient_id):
        """Validate patient ID"""
        errors = []
        
        if not patient_id:
            errors.append("Patient ID is required")
        else:
            try:
                patient_id_int = int(patient_id)
                if patient_id_int <= 0:
                    errors.append("Patient ID must be a positive integer")
                elif patient_id_int > 999999:  # Reasonable upper limit
                    errors.append("Patient ID seems invalid")
            except (ValueError, TypeError):
                errors.append("Patient ID must be a valid integer")
        
        return errors
    
    def save_report(self, file, patient_id):
        """Save report file with proper naming and validation"""
        try:
            # Generate secure filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = secure_filename(file.filename)
            filename = f"report_{patient_id}_{timestamp}_{original_name}"
            filepath = self.upload_folder / filename
            
            # Save file
            file.save(filepath)
            
            # Verify file was saved
            if not filepath.exists():
                return {"success": False, "errors": ["Failed to save file"]}
            
            # Create backup
            self._create_backup(filepath, patient_id)
            
            file_info = {
                "filename": filename,
                "original_name": original_name,
                "filepath": str(filepath),
                "size": filepath.stat().st_size,
                "patient_id": patient_id,
                "upload_time": datetime.now().isoformat()
            }
            
            logger.info(f"Report saved successfully: {file_info}")
            
            return {"success": True, "file_info": file_info}
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            return {"success": False, "errors": [f"File save error: {str(e)}"]}
    
    def get_report(self, patient_id, filename=None):
        """Get report file for patient"""
        try:
            if filename:
                # Specific filename requested
                filepath = self.upload_folder / secure_filename(filename)
            else:
                # Find latest report for patient
                pattern = f"report_{patient_id}_*.pdf"
                reports = list(self.upload_folder.glob(pattern))
                
                if not reports:
                    return {"success": False, "errors": ["No reports found for patient"]}
                
                # Get the most recent report
                reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                filepath = reports[0]
            
            if not filepath.exists():
                return {"success": False, "errors": ["Report file not found"]}
            
            if not filepath.is_file():
                return {"success": False, "errors": ["Invalid file path"]}
            
            file_info = {
                "filepath": str(filepath),
                "filename": filepath.name,
                "size": filepath.stat().st_size,
                "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
            }
            
            return {"success": True, "file_info": file_info}
            
        except Exception as e:
            logger.error(f"Error getting report: {str(e)}")
            return {"success": False, "errors": [f"File retrieval error: {str(e)}"]}
    
    def get_patient_reports(self, patient_id):
        """Get all reports for a patient"""
        try:
            pattern = f"report_{patient_id}_*.pdf"
            reports = list(self.upload_folder.glob(pattern))
            
            report_list = []
            for report_path in sorted(reports, key=lambda x: x.stat().st_mtime, reverse=True):
                report_list.append({
                    "filename": report_path.name,
                    "size": report_path.stat().st_size,
                    "upload_date": datetime.fromtimestamp(report_path.stat().st_mtime).isoformat(),
                    "download_url": f"/reports/{patient_id}/{report_path.name}"
                })
            
            return {"success": True, "reports": report_list, "count": len(report_list)}
            
        except Exception as e:
            logger.error(f"Error listing reports: {str(e)}")
            return {"success": False, "errors": [f"Error listing reports: {str(e)}"]}
    
    def delete_report(self, patient_id, filename):
        """Delete a specific report file"""
        try:
            filepath = self.upload_folder / secure_filename(filename)
            
            if not filepath.exists():
                return {"success": False, "errors": ["Report file not found"]}
            
            # Move to backup before deletion
            backup_path = Path(self.config.get('backup_folder')) / f"deleted_{filename}"
            filepath.rename(backup_path)
            
            logger.info(f"Report moved to backup: {filename}")
            return {"success": True, "message": "Report deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting report: {str(e)}")
            return {"success": False, "errors": [f"Error deleting report: {str(e)}"]}
    
    def _allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.config.get('allowed_extensions')
    
    def _create_backup(self, filepath, patient_id):
        """Create backup of uploaded file"""
        try:
            backup_dir = Path(self.config.get('backup_folder'))
            backup_path = backup_dir / f"backup_{filepath.name}"
            
            import shutil
            shutil.copy2(filepath, backup_path)
            logger.info(f"Backup created: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {str(e)}")

# ---------------------------------------
# SERVICE LAYER using Repository and Factory
# ---------------------------------------
class ReportService:
    def __init__(self):
        self.repository = ReportRepository()
        self.response_factory = ResponseFactory()
    
    def upload_report_service(self, file, patient_id):
        """Service method for uploading reports"""
        # Validate patient ID
        patient_errors = self.repository.validate_patient_id(patient_id)
        if patient_errors:
            return self.response_factory.create_response(
                "error", 
                errors=patient_errors,
                message="Patient validation failed"
            ), 400
        
        # Validate file
        file_errors = self.repository.validate_file(file)
        if file_errors:
            return self.response_factory.create_response(
                "error",
                errors=file_errors,
                message="File validation failed"
            ), 400
        
        # Save report
        save_result = self.repository.save_report(file, patient_id)
        
        if save_result["success"]:
            return self.response_factory.create_response(
                "success",
                data=save_result["file_info"],
                message="Report uploaded successfully",
                metadata={"patient_id": patient_id}
            ), 201
        else:
            return self.response_factory.create_response(
                "error",
                errors=save_result["errors"],
                message="Failed to upload report"
            ), 500
    
    def download_report_service(self, patient_id, filename=None):
        """Service method for downloading reports"""
        # Validate patient ID
        patient_errors = self.repository.validate_patient_id(patient_id)
        if patient_errors:
            return self.response_factory.create_response(
                "error",
                errors=patient_errors,
                message="Invalid patient ID"
            ), 400
        
        # Get report
        report_result = self.repository.get_report(patient_id, filename)
        
        if report_result["success"]:
            try:
                return send_file(
                    report_result["file_info"]["filepath"],
                    as_attachment=True,
                    download_name=report_result["file_info"]["filename"],
                    mimetype='application/pdf'
                )
            except Exception as e:
                logger.error(f"Error sending file: {str(e)}")
                return self.response_factory.create_response(
                    "error",
                    errors=["Failed to send file"],
                    message="File transmission error"
                ), 500
        else:
            status_code = 404 if "not found" in str(report_result["errors"]).lower() else 500
            return self.response_factory.create_response(
                "error",
                errors=report_result["errors"],
                message="Report not available"
            ), status_code
    
    def list_reports_service(self, patient_id):
        """Service method for listing patient reports"""
        patient_errors = self.repository.validate_patient_id(patient_id)
        if patient_errors:
            return self.response_factory.create_response(
                "error",
                errors=patient_errors,
                message="Invalid patient ID"
            ), 400
        
        list_result = self.repository.get_patient_reports(patient_id)
        
        if list_result["success"]:
            return self.response_factory.create_response(
                "success",
                data=list_result,
                message=f"Found {list_result['count']} reports"
            )
        else:
            return self.response_factory.create_response(
                "error",
                errors=list_result["errors"],
                message="Failed to retrieve reports"
            ), 500

# Initialize services
report_service = ReportService()
config_manager = ConfigManager()

# ---------------------------------------
# ROUTES with Enhanced Error Handling
# ---------------------------------------

@reports_bp.route('/reports', methods=['POST'])
def upload_report():
    """Upload lab report for a patient"""
    try:
        # Check if file part exists
        if 'file' not in request.files:
            return jsonify(
                ResponseFactory.create_response(
                    "error",
                    errors=["No file part in request"],
                    message="File upload failed"
                )
            ), 400
        
        file = request.files['file']
        patient_id = request.form.get('patient_id')
        
        return report_service.upload_report_service(file, patient_id)
        
    except Exception as e:
        logger.error(f"Unexpected error in upload_report: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error",
                errors=["Internal server error"],
                message="Upload failed"
            )
        ), 500

@reports_bp.route('/reports/<int:patient_id>', methods=['GET'])
def download_report(patient_id):
    """Download the latest report for a patient"""
    try:
        return report_service.download_report_service(patient_id)
        
    except Exception as e:
        logger.error(f"Unexpected error in download_report: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error", 
                errors=["Internal server error"],
                message="Download failed"
            )
        ), 500

@reports_bp.route('/reports/<int:patient_id>/<filename>', methods=['GET'])
def download_specific_report(patient_id, filename):
    """Download a specific report file"""
    try:
        return report_service.download_report_service(patient_id, filename)
        
    except Exception as e:
        logger.error(f"Unexpected error in download_specific_report: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error",
                errors=["Internal server error"],
                message="Download failed"
            )
        ), 500

@reports_bp.route('/reports/<int:patient_id>/list', methods=['GET'])
def list_patient_reports(patient_id):
    """List all reports for a patient"""
    try:
        return report_service.list_reports_service(patient_id)
        
    except Exception as e:
        logger.error(f"Unexpected error in list_patient_reports: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error",
                errors=["Internal server error"],
                message="Failed to list reports"
            )
        ), 500

@reports_bp.route('/reports/<int:patient_id>/<filename>', methods=['DELETE'])
def delete_report(patient_id, filename):
    """Delete a specific report"""
    try:
        # Validate patient ID
        patient_errors = ReportRepository().validate_patient_id(patient_id)
        if patient_errors:
            return jsonify(
                ResponseFactory.create_response(
                    "error",
                    errors=patient_errors,
                    message="Invalid patient ID"
                )
            ), 400
        
        delete_result = ReportRepository().delete_report(patient_id, filename)
        
        if delete_result["success"]:
            return jsonify(
                ResponseFactory.create_response(
                    "success",
                    message=delete_result["message"]
                )
            )
        else:
            return jsonify(
                ResponseFactory.create_response(
                    "error",
                    errors=delete_result["errors"],
                    message="Failed to delete report"
                )
            ), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in delete_report: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error",
                errors=["Internal server error"],
                message="Deletion failed"
            )
        ), 500

@reports_bp.route('/reports/health', methods=['GET'])
def health_check():
    """Health check endpoint for reports service"""
    try:
        upload_folder = config_manager.get('upload_folder')
        is_accessible = os.path.exists(upload_folder) and os.path.isdir(upload_folder)
        
        health_info = {
            "service": "reports",
            "status": "healthy" if is_accessible else "degraded",
            "upload_folder_accessible": is_accessible,
            "allowed_extensions": list(config_manager.get('allowed_extensions')),
            "max_file_size_mb": config_manager.get('max_file_size') // (1024 * 1024)
        }
        
        status_code = 200 if is_accessible else 503
        
        return jsonify(
            ResponseFactory.create_response(
                "success" if is_accessible else "error",
                data=health_info,
                message="Reports service health check"
            )
        ), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify(
            ResponseFactory.create_response(
                "error",
                errors=["Service unhealthy"],
                message="Health check failed"
            )
        ), 503