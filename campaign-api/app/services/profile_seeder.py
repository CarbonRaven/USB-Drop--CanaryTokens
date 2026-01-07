"""Seed default profiles from templates."""

import logging
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.profile import Profile
from app.services.content_templates import PROFILE_TEMPLATES

logger = logging.getLogger(__name__)


def seed_default_profiles():
    """Create or update default profiles from templates."""
    db = SessionLocal()
    try:
        created_count = 0
        updated_count = 0

        for template_id, template in PROFILE_TEMPLATES.items():
            # Check if profile for this template already exists
            existing = db.query(Profile).filter(
                Profile.scenario_type == template_id,
                Profile.is_system == "true"
            ).first()

            file_structure = {
                "folders": template["folders"],
                "files": template["files"],
            }

            if existing:
                # Update existing profile with latest template data
                existing.name = template["name"]
                existing.description = template["description"]
                existing.file_structure = file_structure
                existing.label_suggestions = template.get("label_suggestions", [])
                updated_count += 1
            else:
                # Create new profile
                profile = Profile(
                    name=template["name"],
                    description=template["description"],
                    scenario_type=template_id,
                    file_structure=file_structure,
                    token_config={},
                    ai_prompts={},
                    label_suggestions=template.get("label_suggestions", []),
                    is_system="true",
                )
                db.add(profile)
                created_count += 1
                logger.info(f"Created profile: {template['name']}")

        db.commit()

        if created_count > 0 or updated_count > 0:
            logger.info(f"Profile seeder: created {created_count}, updated {updated_count}")
        else:
            logger.info("All profiles up to date")

    except Exception as e:
        logger.error(f"Failed to seed profiles: {e}")
        db.rollback()
    finally:
        db.close()
