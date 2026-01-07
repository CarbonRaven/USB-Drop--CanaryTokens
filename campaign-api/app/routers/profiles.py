"""Profiles router - USB drive templates."""

from datetime import datetime
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
import io

from app.database import get_db
from app.models.profile import Profile
from app.models.profile_file import ProfileFile
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.file_storage import file_storage, ALLOWED_TYPES
from app.services.content_templates import (
    list_profile_templates,
    list_text_templates,
    get_profile_template,
    list_ai_image_prompts,
    get_profile_files_with_ai_images,
    get_template_images,
    list_all_template_images,
    PROFILE_TEMPLATES,
    TEXT_TEMPLATES,
    AI_IMAGE_PROMPTS,
    TEMPLATE_IMAGES,
)

router = APIRouter()


# Pydantic models
class ProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_type: str  # hr, it, executive, creator, etc.
    theme: Optional[str] = None
    file_structure: dict = {}
    token_config: dict = {}
    ai_prompts: dict = {}
    url_config: dict = {}
    label_suggestions: List[str] = []


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_type: Optional[str] = None
    theme: Optional[str] = None
    file_structure: Optional[dict] = None
    token_config: Optional[dict] = None
    ai_prompts: Optional[dict] = None
    url_config: Optional[dict] = None
    label_suggestions: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    scenario_type: str
    theme: Optional[str]
    file_structure: dict
    token_config: dict
    ai_prompts: dict
    url_config: dict
    label_suggestions: List[str]
    is_system: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FilePreview(BaseModel):
    path: str
    type: str
    token_type: Optional[str] = None


class ProfilePreview(BaseModel):
    profile_id: uuid.UUID
    files: List[FilePreview]
    token_summary: dict


@router.get("", response_model=List[ProfileResponse])
async def list_profiles(
    scenario_type: Optional[str] = None,
    active_only: bool = Query(False, description="Only return active profiles"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all profiles."""
    query = db.query(Profile)
    if scenario_type:
        query = query.filter(Profile.scenario_type == scenario_type)
    if active_only:
        query = query.filter(Profile.is_active == True)
    profiles = query.order_by(Profile.name).all()
    return profiles


@router.post("", response_model=ProfileResponse)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new profile."""
    profile = Profile(**profile_data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ============================================
# Template Images Endpoints (before dynamic routes)
# ============================================

@router.get("/template-images/list")
async def list_template_images_all(
    current_user: User = Depends(get_current_user),
):
    """List all pre-generated template images."""
    return list_all_template_images()


@router.get("/template-images/{template_id}")
async def list_template_images(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """List pre-generated images for a specific template."""
    images = get_template_images(template_id)
    if not images:
        raise HTTPException(status_code=404, detail="No images found for this template")

    return {
        "template_id": template_id,
        "images": images,
        "base_path": f"/uploads/template_images/{template_id}/"
    }


@router.get("/template-images/{template_id}/{filename}")
async def get_template_image(
    template_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """Serve a specific template image file."""
    # Validate template exists
    if template_id not in TEMPLATE_IMAGES:
        raise HTTPException(status_code=404, detail="Template not found")

    # Validate filename is in template
    valid_filenames = [img["filename"] for img in TEMPLATE_IMAGES[template_id]]
    if filename not in valid_filenames:
        raise HTTPException(status_code=404, detail="Image not found in template")

    # Build file path
    file_path = Path("/app/uploads/template_images") / template_id / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    return FileResponse(
        path=str(file_path),
        media_type="image/jpeg",
        filename=filename
    )


# ============================================
# Template Endpoints (static routes before dynamic)
# ============================================

class TemplateInfo(BaseModel):
    id: str
    name: str
    description: str
    file_count: int
    folder_count: int


class TemplateDetail(BaseModel):
    id: str
    name: str
    description: str
    folders: List[str]
    files: List[dict]


class TextTemplateInfo(BaseModel):
    id: str
    filename: str
    preview: Optional[str] = None


# Token types available for profiles
TOKEN_TYPES = [
    {"id": "ms_word", "name": "Word Document", "extension": ".docx", "description": "Microsoft Word document with embedded token"},
    {"id": "ms_excel", "name": "Excel Spreadsheet", "extension": ".xlsx", "description": "Microsoft Excel spreadsheet with embedded token"},
    {"id": "pdf", "name": "PDF Document", "extension": ".pdf", "description": "PDF document with embedded token"},
    {"id": "text", "name": "Text File", "extension": ".txt", "description": "Text file with embedded tracking URLs"},
    {"id": "html_beacon", "name": "HTML Beacon", "extension": ".html", "description": "HTML page with tracking beacon"},
    {"id": "dns", "name": "DNS Token", "extension": None, "description": "DNS-based token trigger"},
    {"id": "web", "name": "Web Bug", "extension": None, "description": "Web-based tracking pixel"},
    {"id": "windows_dir", "name": "Windows Folder", "extension": ".ini", "description": "Windows folder that triggers on access"},
    {"id": "aws_keys", "name": "AWS Credentials", "extension": ".txt", "description": "Fake AWS credentials file"},
    {"id": "qr_code", "name": "QR Code", "extension": ".png", "description": "QR code image with tracking URL"},
    {"id": "ai_image", "name": "AI Generated Image", "extension": ".jpg", "description": "AI-generated image using DALL-E"},
]


@router.get("/templates/list", response_model=List[TemplateInfo])
async def get_templates(
    current_user: User = Depends(get_current_user),
):
    """List all available profile templates."""
    return list_profile_templates()


@router.get("/templates/{template_id}", response_model=TemplateDetail)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific template."""
    template = get_profile_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return TemplateDetail(
        id=template_id,
        name=template["name"],
        description=template["description"],
        folders=template["folders"],
        files=template["files"],
    )


@router.get("/templates/{template_id}/ai-images")
async def get_template_ai_images(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get list of AI images needed for a specific template."""
    template = get_profile_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "template_id": template_id,
        "template_name": template["name"],
        "ai_images": get_profile_files_with_ai_images(template_id)
    }


@router.post("/from-template/{template_id}", response_model=ProfileResponse)
async def create_from_template(
    template_id: str,
    name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new profile from a template."""
    template = get_profile_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    profile = Profile(
        name=name or template["name"],
        description=template["description"],
        scenario_type=template_id,
        file_structure={
            "folders": template["folders"],
            "files": template["files"],
        },
        token_config={},
        is_system="false",
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/text-templates/list", response_model=List[TextTemplateInfo])
async def get_text_templates(
    current_user: User = Depends(get_current_user),
):
    """List all available text file templates."""
    templates = []
    for key, template in TEXT_TEMPLATES.items():
        # Get first 100 chars of content as preview
        preview = template["content"][:100].replace("{canary_url}", "[TRACKING_URL]")
        templates.append(TextTemplateInfo(
            id=key,
            filename=template["filename"],
            preview=preview + "..."
        ))
    return templates


@router.get("/text-templates/{template_id}")
async def get_text_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific text template content."""
    template = TEXT_TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": template_id,
        "filename": template["filename"],
        "content": template["content"].replace("{canary_url}", "[TRACKING_URL]"),
    }


@router.get("/token-types/list")
async def get_token_types(
    current_user: User = Depends(get_current_user),
):
    """List all available token types."""
    return TOKEN_TYPES


@router.get("/ai-images/list")
async def get_ai_images(
    current_user: User = Depends(get_current_user),
):
    """List all available AI image generation prompts."""
    return list_ai_image_prompts()


@router.get("/ai-images/{prompt_id}")
async def get_ai_image_prompt_detail(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a specific AI image prompt."""
    prompt = AI_IMAGE_PROMPTS.get(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="AI image prompt not found")
    return {
        "id": prompt_id,
        **prompt
    }


# ============================================
# Dynamic Profile Routes (must come after static routes)
# Specific sub-routes first, then generic /{profile_id}
# ============================================

@router.post("/{profile_id}/toggle", response_model=ProfileResponse)
async def toggle_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle profile active status (enable/disable)."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.is_active = not profile.is_active
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}/preview", response_model=ProfilePreview)
async def preview_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview the file structure that would be created."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    files = []
    token_summary = {}

    file_structure = profile.file_structure or {}
    token_config = profile.token_config or {}

    # Parse folders
    folders = file_structure.get("folders", [])
    for folder in folders:
        files.append(FilePreview(path=f"{folder}/", type="folder"))

    # Parse files
    for file_def in file_structure.get("files", []):
        folder = file_def.get("folder", "")
        name = file_def.get("name", "")
        token_type = file_def.get("type", "")
        path = f"{folder}/{name}" if folder else name
        files.append(FilePreview(path=path, type="file", token_type=token_type))

        # Count tokens
        if token_type:
            token_summary[token_type] = token_summary.get(token_type, 0) + 1

    return ProfilePreview(
        profile_id=profile_id,
        files=files,
        token_summary=token_summary,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profile by ID."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: uuid.UUID,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a profile."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.is_system == "true":
        raise HTTPException(status_code=400, detail="Cannot modify system profiles")

    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a profile."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.is_system == "true":
        raise HTTPException(status_code=400, detail="Cannot delete system profiles")

    db.delete(profile)
    db.commit()
    return {"message": "Profile deleted"}


# ============================================
# Profile File Upload Endpoints
# ============================================

class ProfileFileResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    filename: str
    stored_filename: str
    folder: str
    file_type: str
    mime_type: Optional[str]
    file_size_bytes: Optional[int]
    token_type: Optional[str]
    token_config: dict
    target_url: Optional[str]
    shortcut_type: Optional[str]
    custom_content: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileFileUpdate(BaseModel):
    folder: Optional[str] = None
    token_type: Optional[str] = None
    token_config: Optional[dict] = None
    target_url: Optional[str] = None
    shortcut_type: Optional[str] = None
    custom_content: Optional[str] = None
    sort_order: Optional[int] = None


class FileReorderRequest(BaseModel):
    file_ids: List[uuid.UUID]


class ShortcutCreateRequest(BaseModel):
    filename: str
    folder: Optional[str] = ""
    target_url: str
    shortcut_type: str = "both"  # 'windows', 'macos', 'both'


class TemplateCreateRequest(BaseModel):
    filename: str
    folder: Optional[str] = ""
    content: str


@router.get("/{profile_id}/files", response_model=List[ProfileFileResponse])
async def list_profile_files(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all uploaded files for a profile."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    files = db.query(ProfileFile).filter(
        ProfileFile.profile_id == profile_id
    ).order_by(ProfileFile.sort_order, ProfileFile.created_at).all()

    return files


@router.post("/{profile_id}/files", response_model=ProfileFileResponse)
async def upload_profile_file(
    profile_id: uuid.UUID,
    file: UploadFile = File(...),
    folder: str = Form(default=""),
    file_type: str = Form(default="auto"),
    token_type: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to a profile."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Validate and save file
    stored_filename, original_filename, mime_type, file_size = await file_storage.save_file(
        file, profile_id
    )

    # Determine file type category
    if file_type == "auto":
        file_type_category = file_storage.get_file_type_category(mime_type)
    else:
        file_type_category = file_type

    # Auto-detect token type for documents if not specified
    if token_type is None and file_type_category == "document":
        token_type = file_storage.get_token_type_for_document(mime_type)

    # Get next sort order
    max_order = db.query(ProfileFile).filter(
        ProfileFile.profile_id == profile_id
    ).count()

    # Create database record
    profile_file = ProfileFile(
        profile_id=profile_id,
        filename=original_filename,
        stored_filename=stored_filename,
        folder=folder,
        file_type=file_type_category,
        mime_type=mime_type,
        file_size_bytes=file_size,
        token_type=token_type,
        sort_order=max_order,
    )

    db.add(profile_file)
    db.commit()
    db.refresh(profile_file)

    return profile_file


@router.get("/{profile_id}/files/{file_id}", response_model=ProfileFileResponse)
async def get_profile_file(
    profile_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific uploaded file."""
    profile_file = db.query(ProfileFile).filter(
        ProfileFile.id == file_id,
        ProfileFile.profile_id == profile_id
    ).first()

    if not profile_file:
        raise HTTPException(status_code=404, detail="File not found")

    return profile_file


@router.put("/{profile_id}/files/{file_id}", response_model=ProfileFileResponse)
async def update_profile_file(
    profile_id: uuid.UUID,
    file_id: uuid.UUID,
    update_data: ProfileFileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update file metadata."""
    profile_file = db.query(ProfileFile).filter(
        ProfileFile.id == file_id,
        ProfileFile.profile_id == profile_id
    ).first()

    if not profile_file:
        raise HTTPException(status_code=404, detail="File not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile_file, key, value)

    db.commit()
    db.refresh(profile_file)

    return profile_file


@router.delete("/{profile_id}/files/{file_id}")
async def delete_profile_file(
    profile_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an uploaded file."""
    profile_file = db.query(ProfileFile).filter(
        ProfileFile.id == file_id,
        ProfileFile.profile_id == profile_id
    ).first()

    if not profile_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete physical file
    file_storage.delete_file(profile_id, profile_file.stored_filename)

    # Delete database record
    db.delete(profile_file)
    db.commit()

    return {"message": "File deleted"}


@router.get("/{profile_id}/files/{file_id}/download")
async def download_profile_file(
    profile_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download an uploaded file."""
    profile_file = db.query(ProfileFile).filter(
        ProfileFile.id == file_id,
        ProfileFile.profile_id == profile_id
    ).first()

    if not profile_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Read file content
    content = await file_storage.read_file(profile_id, profile_file.stored_filename)

    return StreamingResponse(
        io.BytesIO(content),
        media_type=profile_file.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{profile_file.filename}"'
        }
    )


@router.post("/{profile_id}/files/reorder")
async def reorder_profile_files(
    profile_id: uuid.UUID,
    reorder_data: FileReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder files by providing ordered list of file IDs."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update sort order for each file
    for index, file_id in enumerate(reorder_data.file_ids):
        profile_file = db.query(ProfileFile).filter(
            ProfileFile.id == file_id,
            ProfileFile.profile_id == profile_id
        ).first()
        if profile_file:
            profile_file.sort_order = index

    db.commit()

    return {"message": "Files reordered successfully"}


@router.post("/{profile_id}/shortcuts", response_model=ProfileFileResponse)
async def create_shortcut(
    profile_id: uuid.UUID,
    shortcut_data: ShortcutCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a URL shortcut file (.url or .webloc)."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Validate shortcut type
    if shortcut_data.shortcut_type not in ["windows", "macos", "both"]:
        raise HTTPException(status_code=400, detail="Invalid shortcut type")

    # Ensure filename has proper extension based on shortcut type
    filename = shortcut_data.filename
    # Remove any existing shortcut extensions
    for ext in ['.url', '.webloc', '.lnk']:
        if filename.lower().endswith(ext):
            filename = filename[:-len(ext)]
            break

    # Add appropriate extension
    if shortcut_data.shortcut_type == "windows":
        filename = f"{filename}.url"
    elif shortcut_data.shortcut_type == "macos":
        filename = f"{filename}.webloc"
    else:  # both - use .url as primary
        filename = f"{filename}.url"

    # Get next sort order
    max_order = db.query(ProfileFile).filter(
        ProfileFile.profile_id == profile_id
    ).count()

    # Create database record for shortcut
    profile_file = ProfileFile(
        profile_id=profile_id,
        filename=filename,
        stored_filename="",  # Shortcuts don't have stored files
        folder=shortcut_data.folder,
        file_type="shortcut",
        target_url=shortcut_data.target_url,
        shortcut_type=shortcut_data.shortcut_type,
        sort_order=max_order,
    )

    db.add(profile_file)
    db.commit()
    db.refresh(profile_file)

    return profile_file


@router.post("/{profile_id}/templates", response_model=ProfileFileResponse)
async def create_template(
    profile_id: uuid.UUID,
    template_data: TemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a custom text template with placeholders."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Ensure filename has .txt extension
    filename = template_data.filename
    if not filename.lower().endswith('.txt'):
        filename = f"{filename}.txt"

    # Get next sort order
    max_order = db.query(ProfileFile).filter(
        ProfileFile.profile_id == profile_id
    ).count()

    # Create database record for template
    profile_file = ProfileFile(
        profile_id=profile_id,
        filename=filename,
        stored_filename="",  # Templates store content in custom_content
        folder=template_data.folder,
        file_type="template",
        custom_content=template_data.content,
        sort_order=max_order,
    )

    db.add(profile_file)
    db.commit()
    db.refresh(profile_file)

    return profile_file


@router.post("/{profile_id}/templates/{file_id}/preview")
async def preview_template(
    profile_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview a template with sample placeholder values."""
    profile_file = db.query(ProfileFile).filter(
        ProfileFile.id == file_id,
        ProfileFile.profile_id == profile_id,
        ProfileFile.file_type == "template"
    ).first()

    if not profile_file:
        raise HTTPException(status_code=404, detail="Template not found")

    # Replace placeholders with sample values
    content = profile_file.custom_content or ""
    preview_content = content.replace(
        "{canary_url}", "https://example.com/track/abc123"
    ).replace(
        "{short_url}", "https://short.example.com/xyz"
    ).replace(
        "{drive_code}", "ABC123"
    )

    return {
        "filename": profile_file.filename,
        "original_content": content,
        "preview_content": preview_content,
    }
