import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Simple email service for sending PDF reports"""

    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.email_user)

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.email_user and self.email_password)

    def send_pdf_report(
        self,
        to_email: str,
        company_name: str,
        pdf_path: str,
        pdf_filename: str,
        drive_link: Optional[str] = None,
    ) -> dict:
        """
        Send PDF report via email

        Args:
            to_email: Recipient email address
            company_name: Name of the company analyzed
            pdf_path: Path to the PDF file
            pdf_filename: Name of the PDF file
            drive_link: Optional Google Drive link

        Returns:
            Dict with success status and message
        """
        if not self.is_configured():
            logger.error(
                "Email service not configured - missing EMAIL_USER or EMAIL_PASSWORD"
            )
            return {
                "success": False,
                "error": "Email service not configured. Contact administrator.",
            }

        try:
            logger.info(
                "Creating email for %s (company: %s, pdf: %s)",
                to_email,
                company_name,
                pdf_filename,
            )

            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email or ""
            msg["To"] = to_email
            msg["Subject"] = f"Company Research Report - {company_name}"

            # Email body
            body = self._create_email_body(company_name, drive_link)
            msg.attach(MIMEText(body, "html"))

            attachments_count = 0

            # Attach PDF if file exists and is not too large (25MB limit for most email providers)
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                logger.info(
                    "PDF file found: %s (size: %.2f MB)",
                    pdf_path,
                    file_size / (1024 * 1024),
                )

                if file_size < 25 * 1024 * 1024:  # 25MB limit
                    with open(pdf_path, "rb") as f:
                        attach = MIMEApplication(f.read(), _subtype="pdf")
                        attach.add_header(
                            "Content-Disposition", "attachment", filename=pdf_filename
                        )
                        msg.attach(attach)
                        attachments_count += 1
                    logger.info(
                        "PDF attached to email (size: %.2f MB, attachments: %d)",
                        file_size / (1024 * 1024),
                        attachments_count,
                    )
                else:
                    logger.warning(
                        "PDF too large to attach (%.2f MB), including drive link only",
                        file_size / (1024 * 1024),
                    )
            else:
                logger.warning("PDF file not found: %s", pdf_path)

            logger.info("Email message prepared with %d attachments", attachments_count)

            # Send email - we already checked is_configured() so these should not be None
            if self.email_user and self.email_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_user, self.email_password)
                    server.send_message(msg)
            else:
                raise ValueError("Email credentials not configured")

            logger.info(
                "Email sent successfully to %s with %d attachments",
                to_email,
                attachments_count,
            )
            return {"success": True, "message": f"Report sent to {to_email}"}

        except Exception as e:
            logger.error("Failed to send email: %s", str(e))
            return {"success": False, "error": f"Failed to send email: {str(e)}"}

    def _create_email_body(
        self, company_name: str, drive_link: Optional[str] = None
    ) -> str:
        """Create HTML email body"""
        drive_section = ""
        if drive_link:
            drive_section = f"""
            <div style="margin: 20px 0; padding: 15px; background-color: #e8f5e8; border-radius: 5px; border-left: 4px solid #28a745;">
                <h3 style="margin: 0 0 10px 0; color: #155724;">📁 Google Drive Access</h3>
                <p style="margin: 0;">
                    <a href="{drive_link}" style="color: #007bff; text-decoration: none;">
                        View Report in Google Drive →
                    </a>
                </p>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">🏢 Company Research Report</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">AI-Powered Business Intelligence</p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h2 style="color: #667eea; margin: 0 0 20px 0;">Report Ready: {company_name}</h2>
                
                <p>Your comprehensive company research report has been generated successfully!</p>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #667eea;">
                    <h3 style="margin: 0 0 10px 0; color: #495057;">📊 Report Includes:</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Company overview and key metrics</li>
                        <li>Recent news and market updates</li>
                        <li>Major customers and partnerships</li>
                        <li>Competitive landscape analysis</li>
                        <li>Financial and growth insights</li>
                    </ul>
                </div>
                
                {drive_section}
                
                <div style="margin: 30px 0 20px 0; padding: 15px; background-color: #fff3cd; border-radius: 5px; border-left: 4px solid #ffc107;">
                    <h3 style="margin: 0 0 10px 0; color: #856404;">⚡ Data Sources</h3>
                    <p style="margin: 0;">This report combines data from multiple premium sources including CoreSignal, Apollo, and Tavily APIs for comprehensive business intelligence.</p>
                </div>
                
                <hr style="border: none; height: 1px; background-color: #e9ecef; margin: 30px 0;">
                
                <div style="text-align: center; color: #6c757d; font-size: 14px;">
                    <p style="margin: 0;">Generated by Company Research API</p>
                    <p style="margin: 5px 0 0 0;">Powered by AI and Multi-Source Data Intelligence</p>
                </div>
            </div>
        </body>
        </html>
        """
