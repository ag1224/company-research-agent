#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError as e:
    print("❌ Missing required Google API libraries!")
    print("📦 Please install them with:")
    print("   pip install google-api-python-client google-auth")
    print(f"\nError: {e}")
    sys.exit(1)


class GoogleDriveUploader:
    """
    A comprehensive class to handle Google Drive file uploads using Service Account authentication
    """

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]

    def __init__(self, service_account_file="service_account.json"):
        """
        Initialize the Google Drive uploader with Service Account

        Args:
            service_account_file (str): Path to the Service Account JSON credentials file
        """
        self.service_account_file = service_account_file
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate using Service Account and build the Google Drive service"""
        if not os.path.exists(self.service_account_file):
            raise FileNotFoundError(
                f"Service Account file '{self.service_account_file}' not found. "
                "Please download it from Google Cloud Console."
            )

        # Verify it's a service account file
        try:
            with open(self.service_account_file, "r") as f:
                cred_data = json.load(f)
                if cred_data.get("type") != "service_account":
                    raise ValueError(
                        f"'{self.service_account_file}' is not a service account file. "
                        "Please use a service account JSON file."
                    )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid JSON file: {e}")

        print("🔐 Authenticating with Service Account...")

        # Create credentials from service account file
        credentials = Credentials.from_service_account_file(
            self.service_account_file, scopes=self.SCOPES
        )

        # Build the service
        self.service = build("drive", "v3", credentials=credentials)
        print("✅ Successfully authenticated with Service Account")

    def upload_file(self, file_path, folder_id=None, description=None, filename=None):
        """
        Upload a file to Google Drive

        Args:
            file_path (str): Path to the file to upload
            folder_id (str, optional): ID of the folder to upload to
            description (str, optional): Description for the file
            filename (str, optional): Custom filename to use instead of the original file name

        Returns:
            dict: File metadata from Google Drive
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_path}' not found")

            # File metadata
            file_metadata: dict = {
                "name": filename if filename else file_path.name,
            }

            if description:
                file_metadata["description"] = description
            if folder_id:
                file_metadata["parents"] = [folder_id]

            # Determine MIME type based on file extension
            mime_type = self._get_mime_type(file_path.suffix)

            media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

            upload_name = filename if filename else file_path.name
            print(f"📤 Uploading '{upload_name}' to Google Drive...")
            if self.service is None:
                raise ValueError("Service not initialized. Call authenticate() first.")

            file = (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id,name,webViewLink,size",
                )
                .execute()
            )

            print("✅ File uploaded successfully!")
            print(f"   📁 Name: {file.get('name')}")
            print(f"   🆔 File ID: {file.get('id')}")
            print(f"   🔗 View Link: {file.get('webViewLink')}")
            print(f"   📊 Size: {file.get('size')} bytes")

            return file

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None
        except Exception as error:
            print(f"❌ Unexpected error: {error}")
            return None

    def create_folder(self, folder_name, parent_folder_id=None):
        """
        Create a folder in Google Drive

        Args:
            folder_name (str): Name of the folder to create
            parent_folder_id (str, optional): ID of the parent folder

        Returns:
            str: ID of the created folder
        """
        try:
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }

            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]
            if self.service is None:
                raise ValueError("Service not initialized. Call authenticate() first.")

            folder = (
                self.service.files()
                .create(body=file_metadata, fields="id,name")
                .execute()
            )

            print(f"✅ Folder '{folder_name}' created successfully!")
            print(f"   🆔 Folder ID: {folder.get('id')}")

            return folder.get("id")

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None

    def list_files(self, folder_id=None, max_results=10):
        """
        List files in Google Drive

        Args:
            folder_id (str, optional): ID of the folder to list files from
            max_results (int): Maximum number of files to return

        Returns:
            list: List of file metadata
        """
        try:
            query = ""
            if folder_id:
                query = f"'{folder_id}' in parents"
            if self.service is None:
                print("❌ Service not initialized")
                return []

            results = (
                self.service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                )
                .execute()
            )

            items = results.get("files", [])

            if not items:
                print("📁 No files found.")
                return []

            print(f"📁 Found {len(items)} file(s):")
            for item in items:
                print(f"   📄 {item['name']} (ID: {item['id']})")

            return items

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return []

    def _get_mime_type(self, file_extension):
        """
        Get MIME type based on file extension

        Args:
            file_extension (str): File extension (e.g., '.py', '.pdf')

        Returns:
            str: MIME type
        """
        mime_types = {
            ".py": "text/x-python",
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".csv": "text/csv",
            ".json": "application/json",
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".md": "text/markdown",
            ".zip": "application/zip",
        }

        return mime_types.get(file_extension.lower(), "application/octet-stream")


def print_setup_instructions():
    """Print detailed setup instructions for Service Account"""
    print("\n" + "=" * 70)
    print("🔧 GOOGLE DRIVE API SETUP INSTRUCTIONS (Service Account)")
    print("=" * 70)
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Google Drive API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Google Drive API'")
    print("   - Click on it and press 'Enable'")
    print("\n🔐 CREATE SERVICE ACCOUNT:")
    print("-" * 30)
    print("4. Go to 'APIs & Services' > 'Credentials'")
    print("5. Click 'Create Credentials' > 'Service account'")
    print("6. Fill in service account details:")
    print("   - Service account name: 'drive-uploader'")
    print("   - Service account ID: (auto-generated)")
    print("   - Description: 'Google Drive file uploader'")
    print("7. Click 'Create and Continue'")
    print("8. Skip role assignment (click 'Continue' then 'Done')")
    print("9. Click on the created service account")
    print("10. Go to 'Keys' tab > 'Add Key' > 'Create new key'")
    print("11. Choose 'JSON' format and click 'Create'")
    print("12. Download the JSON file and save it as 'service_account.json'")
    print("13. Place 'service_account.json' in the same directory as this script")
    print("\n✅ Benefits of Service Account:")
    print("   - No browser login required")
    print("   - Perfect for automation and scripts")
    print("   - More secure for server environments")
    print("   - No token expiration issues")
    print("=" * 70)


def upload_specific_file(file_path, folder_id=None):
    """Upload a specific file to Google Drive using Service Account"""
    try:
        if not os.path.exists(file_path):
            print(f"❌ Error: File '{file_path}' not found")
            return False

        uploader = GoogleDriveUploader()

        # Create description with file info
        file_stats = os.stat(file_path)
        description = (
            f"Uploaded via Service Account on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
            f"Original file size: {file_stats.st_size} bytes"
        )

        result = uploader.upload_file(
            file_path=file_path, folder_id=folder_id, description=description
        )

        if result:
            print(f"\n🎉 SUCCESS! '{file_path}' has been uploaded to Google Drive!")
            print(f"🔗 Direct link: {result.get('webViewLink')}")
            print(
                "\n✨ You can now access your file from any device with Google Drive!"
            )
            return True
        else:
            print(f"\n❌ Failed to upload '{file_path}'")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# def interactive_mode():
#     """Interactive mode for uploading files"""
#     print("🎯 INTERACTIVE FILE UPLOAD MODE")
#     print("-" * 40)

#     try:
#         uploader = GoogleDriveUploader()

#         while True:
#             print("\nChoose an option:")
#             print("1. Upload a file")
#             print("2. Create a folder")
#             print("3. List files")
#             print("4. Exit")

#             choice = input("\nEnter your choice (1-4): ").strip()

#             if choice == "1":
#                 file_path = input("Enter file path to upload: ").strip()
#                 description = input("Enter file description (optional): ").strip()

#                 if description == "":
#                     description = None

#                 result = uploader.upload_file(file_path, description=description)
#                 if result:
#                     print(f"✅ Upload successful! View at: {result.get('webViewLink')}")

#             elif choice == "2":
#                 folder_name = input("Enter folder name: ").strip()
#                 folder_id = uploader.create_folder(folder_name)
#                 if folder_id:
#                     print(f"✅ Folder created with ID: {folder_id}")

#             elif choice == "3":
#                 max_files = input(
#                     "Enter max number of files to list (default 10): "
#                 ).strip()
#                 max_files = int(max_files) if max_files.isdigit() else 10
#                 uploader.list_files(max_results=max_files)

#             elif choice == "4":
#                 print("👋 Goodbye!")
#                 break

#             else:
#                 print("❌ Invalid choice. Please enter 1-4.")

#     except KeyboardInterrupt:
#         print("\n👋 Goodbye!")
#     except Exception as e:
#         print(f"❌ Error: {e}")


def main():
    """Main function to handle command line arguments and run the uploader"""
    print("📤 Google Drive File Uploader (Service Account)")
    print("=" * 50)

    # Check for service account file
    service_account_files = ["service_account.json", "credentials.json"]
    service_account_file = None

    for file_name in service_account_files:
        if os.path.exists(file_name):
            service_account_file = file_name
            break

    if not service_account_file:
        print("❌ Service Account credentials not found!")
        print("🔍 Looking for: service_account.json or credentials.json")
        print_setup_instructions()
        return False

    # Handle command line arguments
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"🎯 Uploading file: {file_path}")
        return upload_specific_file(file_path)
    else:
        # Check for company_research_fastapi.py in current directory
        demo_file = "pdfs/jrni_com_coresignal_report_3.pdf"
        if os.path.exists(demo_file):
            print(f"🎯 Found '{demo_file}' in current directory")
            upload_choice = input(f"Upload '{demo_file}'? (y/n): ").strip().lower()
            if upload_choice in ["y", "yes"]:
                return upload_specific_file(
                    demo_file,
                    folder_id="11NiwE908Ms6orYv1-YRuKw2EeIVORJp7",
                )

        # Run interactive mode
        # interactive_mode()
        return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🏁 Operation completed!")
        else:
            print("\n💥 Operation failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
