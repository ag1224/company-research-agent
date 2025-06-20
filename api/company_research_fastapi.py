import asyncio
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from email_service import EmailService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to find third_party_api module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import CoreSignal API
# Import the new MultiSourceResearcher class
from researchers.multi_source_researcher import MultiSourceResearcher

# Import Apollo API for backward compatibility (if needed elsewhere)
from third_party_api.coresignal_multisource_api import CoreSignalMultiSourceAPI

# Import Google Drive uploader
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from drive_uploader_complete import GoogleDriveUploader

    GOOGLE_DRIVE_AVAILABLE = True
    logger.info("Google Drive uploader imported successfully")
    # check if folder id exists in environment variable
    # if not os.getenv("GOOGLE_DRIVE_FOLDER_ID"):
    #     raise ValueError("GOOGLE_DRIVE_FOLDER_ID environment variable is not set")
except ImportError as e:
    GOOGLE_DRIVE_AVAILABLE = False

    # # Create a dummy class for type checking when imports fail
    # class GoogleDriveUploader:
    #     def __init__(self, *args, **kwargs):
    #         pass

    #     def upload_file(self, *args, **kwargs):
    #         return None

    logger.warning("Google Drive functionality not available: %s", e)
    logger.warning("Make sure drive_uploader_complete.py is in the same directory")

# Import Email Service
EmailService = None
try:
    from email_service import EmailService

    EMAIL_SERVICE_AVAILABLE = True
    logger.info("Email service imported successfully")
except ImportError as e:
    EMAIL_SERVICE_AVAILABLE = False
    logger.warning("Email service not available: %s", e)

app = FastAPI(title="Company Research PDF Report API", version="2.0.0")


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log the incoming request
    logger.info("Incoming request: %s %s", request.method, request.url.path)

    # Process the request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log the response
    logger.info(
        "Request completed: %s %s - Status: %d - Duration: %.3fs",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )

    return response


# Mount static files to serve the frontend
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Directory doesn't exist, create it
    import os

    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")


class CoreSignalCompanyResearchRequest(BaseModel):
    website: str  # e.g., "https://www.example.com" or "example.com"
    email: Optional[str] = None  # Optional: email to send the report
    upload_to_drive: bool = False  # Optional: upload PDF to Google Drive
    upload_to_drive_folder_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    )  # Optional: upload PDF to Google Drive folder


class BackgroundCompanyResearchRequest(BaseModel):
    website: str  # e.g., "https://www.example.com" or "example.com"
    email: str  # Required: email to send the report


class MultiSourceBackgroundCompanyResearchRequest(BaseModel):
    website: str  # Company domain for Apollo API (e.g., example.com)
    email: str  # Required: email to send the report


class MultiSourceCompanyResearchRequest(BaseModel):
    domain: str  # Company domain for Apollo API (e.g., example.com)
    email: Optional[str] = None  # Optional: email to send the report
    return_data: bool = False  # Whether to return raw data in response
    upload_to_drive: bool = False  # Optional: upload PDF to Google Drive
    upload_to_drive_folder_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    )  # Optional: upload PDF to Google Drive folder


@app.get("/")
async def root():
    """Serve the frontend interface"""
    try:
        from fastapi.responses import HTMLResponse

        with open("static/index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        # Fallback to API info if frontend file doesn't exist
        return {
            "message": "Company Research Multi-Source API with CoreSignal, Apollo & Tavily",
            "version": "3.0.0",
            "endpoints": {
                "health": "GET /api/health - API health check",
                "multi_source_research": "POST /api/multi-source-research - Apollo + Tavily research",
                "multi_source_research_background": "POST /api/multi-source-research-background - Apollo + Tavily research (background)",
                "coresignal_generate_pdf": "POST /api/coresignal/generate-pdf - CoreSignal PDF report generation",
                "drive_files": "GET /api/drive-files - List Google Drive files",
                "frontend": "GET / - Web interface for report generation",
            },
            "description": "Comprehensive company research using multiple data sources",
            "data_sources": [
                "CoreSignal Multi-Source API",
                "Apollo Organization API",
                "Tavily Search API",
            ],
            "google_drive_available": GOOGLE_DRIVE_AVAILABLE,
        }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    email_configured = False
    if EMAIL_SERVICE_AVAILABLE and EmailService:
        try:
            email_service = EmailService()
            email_configured = email_service.is_configured()
        except Exception:
            email_configured = False

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_availability": {
            "coresignal": bool(os.getenv("CORESIGNAL_API_KEY")),
            "apollo": bool(os.getenv("APOLLO_API_KEY")),
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
        },
        "google_drive_available": GOOGLE_DRIVE_AVAILABLE,
        "email_service_available": EMAIL_SERVICE_AVAILABLE,
        "email_configured": email_configured,
        "service_account_exists": os.path.exists("service_account.json"),
        "uploader_module_available": GOOGLE_DRIVE_AVAILABLE,
    }


@app.post("/api/multi-source-research-background")
async def multi_source_research_background(
    request: MultiSourceBackgroundCompanyResearchRequest,
):
    """
    Generate a multi-source research PDF report in background and send via email
    Returns immediately with success message while processing continues in background
    """
    try:
        # Extract domain from website URL
        domain = (
            request.website.replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
        )

        logger.info(
            "Starting background multi-source research for: %s",
            request.website,
        )

        # Start the background task
        asyncio.create_task(
            multi_source_research_endpoint(
                MultiSourceCompanyResearchRequest(
                    domain=domain,
                    email=request.email,
                    return_data=False,
                    upload_to_drive=True,  # Always upload to drive in background mode
                    upload_to_drive_folder_id=os.getenv(
                        "GOOGLE_DRIVE_INTERFACE_FOLDER_ID"
                    ),
                )
            )
        )

        # Return immediate success response
        return JSONResponse(
            content={
                "message": "🎉 Multi-source research started! You'll receive an email when it's ready.",
                "status": "processing",
                "domain": request.website,
                "email": request.email,
                "timestamp": datetime.now().isoformat(),
                "estimated_time": "5-10 minutes",
            }
        )

    except Exception as e:
        logger.error("Error starting background multi-source research: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Error starting multi-source research: {str(e)}"
        )


@app.post("/api/multi-source-research")
async def multi_source_research_endpoint(request: MultiSourceCompanyResearchRequest):
    """
    Multi-source company research using Apollo API and Tavily Search (replicates main.py functionality)
    """
    try:
        logger.info(
            "Starting multi-source research for domain: %s",
            request.domain,
        )

        # Initialize MultiSourceResearcher
        researcher = MultiSourceResearcher(request.domain)

        # Perform complete research using the new class
        logger.info("Performing comprehensive research...")
        research_result = await researcher.research_company()

        # Extract data from research result
        report = research_result["report"]
        company_name = research_result["company_name"]
        apollo_data = research_result["raw_data"]["apollo_data"]
        customers_data = research_result["raw_data"]["tavily_customers"]
        coresignal_data = research_result["raw_data"]["coresignal_data"]
        # news_data = research_result["raw_data"]["tavily_news"]
        # competitors_data = research_result["raw_data"]["tavily_competitors"]

        # Always generate PDF for multi-source research
        logger.info("Generating PDF from report...")

        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as md_file:
            md_file.write(report)
            md_path = md_file.name

        # Generate PDF filename
        safe_company_name = "".join(
            c for c in company_name if c.isalnum() or c in (" ", "-", "_")
        ).replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"{safe_company_name}_multi_source_report_{timestamp}.pdf"

        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_path = pdf_file.name

        logger.info("Converting markdown to PDF with pandoc...")
        # Convert markdown to PDF using pandoc
        simple_cmd = ["pandoc", md_path, "-o", pdf_path]
        subprocess.run(simple_cmd, check=True)
        logger.info("PDF generated successfully")

        # Clean up markdown file
        os.unlink(md_path)

        # Handle Google Drive upload if requested
        drive_result = None
        if request.upload_to_drive:
            if not GOOGLE_DRIVE_AVAILABLE:
                logger.warning(
                    "Google Drive upload requested but uploader not available"
                )
                drive_result = {
                    "success": False,
                    "error": "Google Drive uploader not available. Check drive_uploader_complete.py",
                }
            elif not request.upload_to_drive_folder_id:
                logger.warning(
                    "Google Drive upload requested but upload_to_drive_folder_id is not set"
                )
                drive_result = {
                    "success": False,
                    "error": "Google Drive upload folder ID is not set",
                }
            else:
                logger.info("Uploading to Google Drive...")
                try:
                    uploader = GoogleDriveUploader()  # type: ignore
                    description = f"Multi-source company research report for {company_name} generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    # Upload using the existing uploader
                    upload_result = uploader.upload_file(
                        file_path=pdf_path,
                        folder_id=request.upload_to_drive_folder_id,
                        description=description,
                        filename=pdf_filename,
                    )

                    if upload_result:
                        drive_result = {
                            "success": True,
                            "file_id": upload_result.get("id"),
                            "file_name": upload_result.get("name"),
                            "view_link": upload_result.get("webViewLink"),
                            "size": upload_result.get("size"),
                        }
                        logger.info(
                            "Successfully uploaded to Google Drive: %s",
                            drive_result["view_link"],
                        )
                    else:
                        drive_result = {
                            "success": False,
                            "error": "Upload failed - no result returned from Google Drive",
                        }
                        logger.error("Failed to upload to Google Drive")

                except Exception as e:
                    logger.error("Google Drive upload error: %s", str(e))
                    drive_result = {"success": False, "error": str(e)}

        # Handle email sending if requested
        email_result = None
        if request.email and EMAIL_SERVICE_AVAILABLE and EmailService:
            try:
                email_service = EmailService()
                if email_service.is_configured():
                    logger.info("Sending email to: %s", request.email)
                    drive_link = (
                        drive_result.get("view_link")
                        if drive_result and drive_result.get("success")
                        else None
                    )
                    email_result = email_service.send_pdf_report(
                        to_email=request.email,
                        company_name=company_name,
                        pdf_path=pdf_path,
                        pdf_filename=pdf_filename,
                        drive_link=drive_link,
                    )
                    logger.info("Email result: %s", email_result)
                else:
                    email_result = {
                        "success": False,
                        "error": "Email service not configured",
                    }
                    logger.warning("Email service not configured")
            except Exception as e:
                email_result = {"success": False, "error": f"Email error: {str(e)}"}
                logger.error("Email sending failed: %s", str(e))

        logger.info("Sending PDF: %s", pdf_filename)

        # Return appropriate response based on upload status, email status, and PDF generation
        if request.email:
            # Return JSON response with email status
            response_data = {
                "message": "Multi-source research completed and PDF generated successfully",
                "company_name": company_name,
                "domain": request.domain,
                "pdf_filename": pdf_filename,
                "timestamp": datetime.now().isoformat(),
                "data_sources": ["Apollo Organization API", "Tavily Search API"],
                "email_sent": email_result.get("success", False)
                if email_result
                else False,
            }

            if drive_result:
                response_data["google_drive"] = drive_result

            if email_result:
                response_data["email_result"] = email_result

            # Include raw data if requested
            if request.return_data:
                response_data["raw_data"] = {
                    "apollo_data": apollo_data,
                    "tavily_customers": customers_data,
                    "coresignal_data": coresignal_data,
                }

            # Clean up the temporary PDF file if email was sent successfully or uploaded to drive
            if (email_result and email_result.get("success")) or (
                drive_result and drive_result.get("success")
            ):
                try:
                    os.unlink(pdf_path)
                except Exception:
                    pass

            return JSONResponse(content=response_data)

        elif drive_result and drive_result.get("success"):
            # Return JSON response with Google Drive link
            response_data = {
                "message": "Multi-source research completed and PDF uploaded to Google Drive successfully",
                "company_name": company_name,
                "domain": request.domain,
                "pdf_filename": pdf_filename,
                "timestamp": datetime.now().isoformat(),
                "data_sources": ["Apollo Organization API", "Tavily Search API"],
                "google_drive": drive_result,
            }

            # Include raw data if requested
            if request.return_data:
                response_data["raw_data"] = {
                    "apollo_data": apollo_data,
                    "tavily_customers": customers_data,
                    "coresignal_data": coresignal_data,
                }

            # Clean up the temporary PDF file since it's now on Drive
            try:
                os.unlink(pdf_path)
            except Exception:
                pass

            return JSONResponse(content=response_data)

        else:
            # Return the PDF file as download
            headers = {"Content-Disposition": f"attachment; filename={pdf_filename}"}

            # Add error info if drive upload was attempted but failed
            if drive_result and not drive_result.get("success"):
                headers["X-Drive-Upload-Error"] = drive_result.get(
                    "error", "Unknown error"
                )

            return FileResponse(
                path=pdf_path,
                filename=pdf_filename,
                media_type="application/pdf",
                headers=headers,
            )

    except subprocess.CalledProcessError as e:
        logger.error("Pandoc error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Error converting to PDF. Make sure pandoc is installed.",
        )
    except Exception as e:
        logger.error("Multi-source research error: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Error in multi-source research: {str(e)}"
        )


@app.get("/api/drive-files")
async def list_drive_files(folder_id: Optional[str] = None):
    """
    Get list of files from Google Drive folder
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        raise HTTPException(
            status_code=400,
            detail="Google Drive functionality not available. Check drive_uploader_complete.py and environment variables",
        )

    try:
        from drive_uploader_complete import GoogleDriveUploader

        uploader = GoogleDriveUploader()

        # Use provided folder_id or default from environment
        target_folder_id = folder_id or os.getenv("GOOGLE_DRIVE_INTERFACE_FOLDER_ID")

        if not target_folder_id:
            raise HTTPException(
                status_code=400,
                detail="No folder ID provided and GOOGLE_DRIVE_FOLDER_ID environment variable is not set",
            )

        # Get files from the folder using direct API call for more fields
        if uploader.service is None:
            raise HTTPException(
                status_code=500, detail="Google Drive service not initialized"
            )

        query = f"'{target_folder_id}' in parents"
        results = (
            uploader.service.files()
            .list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, webViewLink, webContentLink)",
            )
            .execute()
        )

        files = results.get("files", [])

        if files is None or not isinstance(files, list):
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve files from Google Drive",
            )

        # Format the response
        response_data = {
            "folder_id": target_folder_id,
            "file_count": len(files),
            "files": [],
        }

        for file in files:
            file_info = {
                "id": file.get("id"),
                "name": file.get("name"),
                "mimeType": file.get("mimeType"),
                "size": file.get("size"),
                "createdTime": file.get("createdTime"),
                "modifiedTime": file.get("modifiedTime"),
                "webViewLink": file.get("webViewLink"),
                "webContentLink": file.get("webContentLink"),
            }
            response_data["files"].append(file_info)

        logger.info(
            "Retrieved %d files from Google Drive folder: %s",
            len(files),
            target_folder_id,
        )
        return JSONResponse(content=response_data)

    except ImportError as e:
        logger.error("Google Drive uploader import error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Google Drive uploader module not available",
        )
    except Exception as e:
        logger.error("Error listing Google Drive files: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error listing Google Drive files: {str(e)}",
        )


# @app.post("/upload-pdf")
# async def upload_existing_pdf(
#     file: UploadFile = File(...),
#     filename: Optional[str] = Form(None),
#     folder_id: Optional[str] = Form(None),
# ):
#     """
#     Upload a PDF file to Google Drive using the existing uploader
#     """
#     if not GOOGLE_DRIVE_AVAILABLE:
#         raise HTTPException(
#             status_code=400,
#             detail="Google Drive uploader not available. Check drive_uploader_complete.py",
#         )

#     try:
#         # Validate file type
#         if not file.filename or not file.filename.lower().endswith(".pdf"):
#             raise HTTPException(
#                 status_code=400,
#                 detail="File must be a PDF. Please upload a file with .pdf extension.",
#             )

#         # Validate content type if available
#         if file.content_type and not file.content_type == "application/pdf":
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid content type. Expected application/pdf.",
#             )

#         logger.info("Uploading %s to Google Drive...", file.filename)

#         # Create temporary file to save uploaded content
#         with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
#             # Read and write file content
#             content = await file.read()
#             temp_file.write(content)
#             temp_file_path = temp_file.name

#         try:
#             uploader = GoogleDriveUploader()  # type: ignore
#             description = f"PDF uploaded via API on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

#             # Use custom filename if provided, otherwise use original filename
#             upload_filename = filename if filename else file.filename

#             # If custom filename provided, rename the file temporarily
#             final_upload_path = temp_file_path
#             if filename and filename != file.filename:
#                 # Create a new temporary file with the custom name
#                 temp_dir = tempfile.mkdtemp()
#                 final_upload_path = os.path.join(temp_dir, filename)
#                 import shutil

#                 shutil.copy2(temp_file_path, final_upload_path)

#             result = uploader.upload_file(
#                 file_path=final_upload_path,
#                 folder_id=folder_id,
#                 description=description,
#                 filename=upload_filename,
#             )

#             # Clean up temporary files
#             if os.path.exists(temp_file_path):
#                 os.unlink(temp_file_path)
#             if final_upload_path != temp_file_path and os.path.exists(
#                 final_upload_path
#             ):
#                 os.unlink(final_upload_path)
#                 # Remove temp directory if we created one
#                 temp_dir = os.path.dirname(final_upload_path)
#                 if os.path.exists(temp_dir) and temp_dir != os.path.dirname(
#                     temp_file_path
#                 ):
#                     os.rmdir(temp_dir)

#             if result:
#                 return {
#                     "message": "PDF uploaded to Google Drive successfully",
#                     "original_filename": file.filename,
#                     "upload_filename": upload_filename,
#                     "file_size": len(content),
#                     "google_drive": {
#                         "file_id": result.get("id"),
#                         "file_name": result.get("name"),
#                         "view_link": result.get("webViewLink"),
#                         "size": result.get("size"),
#                     },
#                 }
#             else:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="Failed to upload to Google Drive - no result returned",
#                 )

#         except Exception as upload_error:
#             # Clean up temp file on upload error
#             if os.path.exists(temp_file_path):
#                 os.unlink(temp_file_path)
#             raise upload_error

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")


@app.post("/api/coresignal/generate-pdf-background")
async def coresignal_generate_pdf_background(request: BackgroundCompanyResearchRequest):
    """
    Generate a PDF report for a company using CoreSignal API in background and send via email
    Returns immediately with success message while processing continues in background
    """
    try:
        logger.info("Starting background PDF generation for: %s", request.website)

        # Start the background task
        asyncio.create_task(
            coresignal_generate_pdf_report(
                CoreSignalCompanyResearchRequest(
                    website=request.website,
                    email=request.email,
                    upload_to_drive=True,  # Always upload to drive in background mode
                    upload_to_drive_folder_id=os.getenv(
                        "GOOGLE_DRIVE_INTERFACE_FOLDER_ID"
                    ),
                )
            )
        )

        # Return immediate success response
        return JSONResponse(
            content={
                "message": "🎉 Report generation started! You'll receive an email when it's ready.",
                "status": "processing",
                "website": request.website,
                "email": request.email,
                "timestamp": datetime.now().isoformat(),
                "estimated_time": "5-10 minutes",
            }
        )

    except Exception as e:
        logger.error("Error starting background task: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Error starting report generation: {str(e)}"
        )


@app.post("/api/coresignal/generate-pdf")
async def coresignal_generate_pdf_report(request: CoreSignalCompanyResearchRequest):
    """
    Generate a PDF report for a company using CoreSignal API and optionally upload to Google Drive
    """
    try:
        # Normalize website URL
        website = request.website
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"

        logger.info("Generating CoreSignal report for: %s", website)
        logger.info("Upload to Drive: %s", request.upload_to_drive)

        # Initialize CoreSignal API
        coresignal_api = CoreSignalMultiSourceAPI(website)

        # Get API data
        logger.info("Fetching data from CoreSignal API...")
        api_response = await asyncio.to_thread(
            coresignal_api.company_multi_source_enrich
        )

        # Generate markdown report using LLM
        logger.info("Generating markdown report with LLM...")
        markdown_report = coresignal_api.generate_markdown_report_with_llm(api_response)

        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as md_file:
            md_file.write(markdown_report)
            md_path = md_file.name

        # Generate PDF filename
        company_name = api_response.get("company_name", "Unknown_Company")
        safe_company_name = "".join(
            c for c in company_name if c.isalnum() or c in (" ", "-", "_")
        ).replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"{safe_company_name}_coresignal_report_{timestamp}.pdf"

        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            pdf_path = pdf_file.name

        logger.info("Converting markdown to PDF with pandoc...")

        # Convert markdown to PDF using pandoc
        simple_cmd = ["pandoc", md_path, "-o", pdf_path]
        subprocess.run(simple_cmd, check=True)
        logger.info("PDF generated successfully")

        # Clean up markdown file
        os.unlink(md_path)

        # Handle Google Drive upload if requested
        drive_result = None
        if request.upload_to_drive:
            if not GOOGLE_DRIVE_AVAILABLE:
                logger.warning(
                    "Google Drive upload requested but uploader not available"
                )
                drive_result = {
                    "success": False,
                    "error": "Google Drive uploader not available. Check drive_uploader_complete.py",
                }
            elif not request.upload_to_drive_folder_id:
                logger.warning(
                    "Google Drive upload requested but no folder ID provided"
                )
                drive_result = {
                    "success": False,
                    "error": "Google Drive folder ID is required for upload. Please provide upload_to_drive_folder_id.",
                }
            else:
                logger.info("Uploading to Google Drive...")
                try:
                    uploader = GoogleDriveUploader()  # type: ignore
                    description = f"Company research report for {company_name} generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                    # Upload using the existing uploader
                    upload_result = uploader.upload_file(
                        file_path=pdf_path,
                        folder_id=request.upload_to_drive_folder_id,
                        description=description,
                        filename=pdf_filename,
                    )

                    if upload_result:
                        drive_result = {
                            "success": True,
                            "file_id": upload_result.get("id"),
                            "file_name": upload_result.get("name"),
                            "view_link": upload_result.get("webViewLink"),
                            "size": upload_result.get("size"),
                        }
                        logger.info(
                            "Successfully uploaded to Google Drive: %s",
                            drive_result["view_link"],
                        )
                    else:
                        drive_result = {
                            "success": False,
                            "error": "Upload failed - no result returned from Google Drive",
                        }
                        logger.error("Failed to upload to Google Drive")

                except Exception as e:
                    logger.error("Google Drive upload error: %s", str(e))
                    drive_result = {"success": False, "error": str(e)}

        # Handle email sending if requested
        email_result = None
        if request.email and EMAIL_SERVICE_AVAILABLE and EmailService:
            try:
                email_service = EmailService()
                if email_service.is_configured():
                    logger.info("Sending email to: %s", request.email)
                    drive_link = (
                        drive_result.get("view_link")
                        if drive_result and drive_result.get("success")
                        else None
                    )
                    email_result = email_service.send_pdf_report(
                        to_email=request.email,
                        company_name=company_name,
                        pdf_path=pdf_path,
                        pdf_filename=pdf_filename,
                        drive_link=drive_link,
                    )
                    logger.info("Email result: %s", email_result)
                else:
                    email_result = {
                        "success": False,
                        "error": "Email service not configured",
                    }
                    logger.warning("Email service not configured")
            except Exception as e:
                email_result = {"success": False, "error": f"Email error: {str(e)}"}
                logger.error("Email sending failed: %s", str(e))

        logger.info("Sending PDF: %s", pdf_filename)

        # Return appropriate response based on upload and email status
        if request.email:
            # Return JSON response with email status
            response_data = {
                "message": "PDF generated successfully",
                "pdf_filename": pdf_filename,
                "company_name": company_name,
                "generated_at": datetime.now().isoformat(),
                "email_sent": email_result.get("success", False)
                if email_result
                else False,
            }

            if drive_result:
                response_data["google_drive"] = drive_result

            if email_result:
                response_data["email_result"] = email_result

            # Clean up the temporary PDF file if email was sent successfully or uploaded to drive
            if (email_result and email_result.get("success")) or (
                drive_result and drive_result.get("success")
            ):
                try:
                    os.unlink(pdf_path)
                except Exception:
                    pass

            return JSONResponse(content=response_data)

        elif drive_result and drive_result.get("success"):
            # Return JSON response with Google Drive link
            response_data = {
                "message": "PDF generated and uploaded to Google Drive successfully",
                "pdf_filename": pdf_filename,
                "company_name": company_name,
                "generated_at": datetime.now().isoformat(),
                "google_drive": drive_result,
            }

            # Clean up the temporary PDF file since it's now on Drive
            try:
                os.unlink(pdf_path)
            except Exception:
                pass

            return JSONResponse(content=response_data)

        else:
            # Return the PDF file as download
            headers = {"Content-Disposition": f"attachment; filename={pdf_filename}"}

            # Add error info if drive upload was attempted but failed
            if drive_result and not drive_result.get("success"):
                headers["X-Drive-Upload-Error"] = drive_result.get(
                    "error", "Unknown error"
                )

            return FileResponse(
                path=pdf_path,
                filename=pdf_filename,
                media_type="application/pdf",
                headers=headers,
            )

    except subprocess.CalledProcessError as e:
        logger.error("Pandoc error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Error converting to PDF. Make sure pandoc is installed.",
        )
    except Exception as e:
        logger.error("Error generating PDF report: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Error generating PDF report: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Company Research Multi-Source API...")
    logger.info("Open http://localhost:8000/docs for interactive documentation")
    logger.info("Main endpoints:")
    logger.info("   - POST /api/multi-source-research - Apollo + Tavily research")
    logger.info(
        "   - POST /api/multi-source-research-background - Apollo + Tavily research (background)"
    )
    logger.info(
        "   - POST /api/coresignal/generate-pdf - CoreSignal PDF report generation"
    )
    logger.info("API Status:")
    logger.info(
        "   - CoreSignal: %s", "✅" if os.getenv("CORESIGNAL_API_KEY") else "❌"
    )
    logger.info("   - Apollo: %s", "✅" if os.getenv("APOLLO_API_KEY") else "❌")
    logger.info("   - Tavily: %s", "✅" if os.getenv("TAVILY_API_KEY") else "❌")
    logger.info("   - OpenAI: %s", "✅" if os.getenv("OPENAI_API_KEY") else "❌")
    logger.info("   - Google Drive: %s", "✅" if GOOGLE_DRIVE_AVAILABLE else "❌")

    # Check email service
    email_status = "❌"
    if EMAIL_SERVICE_AVAILABLE and EmailService:
        try:
            email_service = EmailService()
            email_status = "✅" if email_service.is_configured() else "⚠️"
        except Exception:
            email_status = "❌"
    logger.info("   - Email Service: %s", email_status)

    if GOOGLE_DRIVE_AVAILABLE:
        if os.path.exists("service_account.json"):
            logger.info("Service account file found")
        else:
            logger.warning(
                "Service account file not found. Google Drive uploads will fail."
            )
            logger.warning(
                "Place 'service_account.json' in the root directory of the project."
            )

    uvicorn.run(app, host="0.0.0.0", port=8080)
