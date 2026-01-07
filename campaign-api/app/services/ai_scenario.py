"""AI Scenario Recommendation Service - Uses OpenAI to suggest optimal USB drop profiles."""

import json
import logging
from typing import Optional
from openai import AsyncOpenAI

from app.config import get_settings
from app.models.target import Target
from app.services.content_templates import PROFILE_TEMPLATES

logger = logging.getLogger(__name__)
settings = get_settings()


# Profile descriptions for the AI to understand
PROFILE_DESCRIPTIONS = {
    "it_department": {
        "name": "IT Department",
        "best_for": "Targeting IT staff, sysadmins, network engineers",
        "contains": "Network configs, server inventory, passwords, VPN configs, backup credentials",
        "triggers": "Password files, server lists, config files",
    },
    "hr_documents": {
        "name": "HR Documents",
        "best_for": "Targeting HR staff, office managers, administrative personnel",
        "contains": "Employee handbooks, salary info, benefits docs, onboarding materials",
        "triggers": "Salary spreadsheets, employee directories, policy documents",
    },
    "finance": {
        "name": "Finance",
        "best_for": "Targeting finance, accounting, CFO, controllers",
        "contains": "Financial reports, budgets, invoices, tax documents, bank details",
        "triggers": "Budget spreadsheets, bank account docs, payment records",
    },
    "executive": {
        "name": "Executive",
        "best_for": "Targeting C-suite, board members, senior leadership",
        "contains": "Board presentations, M&A documents, strategic plans, confidential memos",
        "triggers": "Confidential project notes, meeting minutes, investor decks",
    },
    "developer": {
        "name": "Developer",
        "best_for": "Targeting software engineers, DevOps, technical staff",
        "contains": "API keys, .env files, database configs, architecture docs",
        "triggers": "Config files, credential files, API documentation",
    },
    "network_admin": {
        "name": "Network Admin",
        "best_for": "Targeting network engineers, infrastructure teams",
        "contains": "Network topology, WiFi passwords, firewall rules, VPN configs",
        "triggers": "WiFi access files, router passwords, network diagrams",
    },
    "security_audit": {
        "name": "Security Audit",
        "best_for": "Targeting security teams, or when audit theme is plausible",
        "contains": "Pentest reports, vulnerability scans, extracted credentials, evidence",
        "triggers": "Password dumps, vulnerability reports, security assessments",
    },
    "contractor": {
        "name": "Contractor Access",
        "best_for": "Targeting contractors, consultants, temporary workers",
        "contains": "VPN setup, WiFi access, project docs, NDA, timesheets",
        "triggers": "Access credentials, project requirements, onboarding info",
    },
}


class AIScenarioService:
    """Service for AI-powered scenario recommendations."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def recommend_scenario(self, target: Target) -> dict:
        """
        Analyze a target and recommend the best USB drop scenario.

        Returns:
            Dict with recommended_profile, confidence, reasoning, alternatives, etc.
        """
        # Build context about available profiles
        profiles_context = "\n".join([
            f"- {pid}: {pinfo['name']} - Best for: {pinfo['best_for']}. Contains: {pinfo['contains']}"
            for pid, pinfo in PROFILE_DESCRIPTIONS.items()
        ])

        # Build target context
        target_context = f"""
Target Organization Analysis:
- Company: {target.company_name}
- Industry: {target.industry}
- Size: {target.company_size}
- Target Department: {target.target_department or 'Not specified'}
- Region: {target.geographic_region or 'Not specified'}
- Known Technologies: {', '.join(target.known_technologies) if target.known_technologies else 'None specified'}
- Email Domain: {target.email_domain or 'Not specified'}
- OSINT Notes: {target.osint_notes or 'None'}
"""

        system_prompt = """You are an expert penetration tester specializing in physical security assessments and USB drop attacks. Your role is to analyze target organizations and recommend the most effective USB drop profile for authorized security testing.

You understand social engineering, organizational psychology, and what types of content different employees are likely to open. You consider industry-specific factors, company culture, and security awareness levels.

Always provide actionable, specific recommendations. Your recommendations must be for AUTHORIZED penetration testing only."""

        user_prompt = f"""Analyze this target organization and recommend the best USB drop profile for an authorized penetration test.

{target_context}

Available USB Drop Profiles:
{profiles_context}

Provide your recommendation in the following JSON format:
{{
    "recommended_profile": "profile_id",
    "confidence": "high|medium|low",
    "reasoning": "2-3 sentences explaining why this profile is best for this target",
    "alternative_profiles": ["profile_id_1", "profile_id_2"],
    "suggested_labels": ["Label idea 1", "Label idea 2", "Label idea 3"],
    "suggested_filenames": ["filename1.docx", "filename2.xlsx", "filename3.pdf"],
    "risk_factors": ["Risk 1", "Risk 2"],
    "tips": ["Tip 1 for this specific target", "Tip 2"]
}}

Consider:
1. Industry-specific content that would seem legitimate
2. Department-specific files that would attract attention
3. Plausible scenarios for how the USB might have been "lost"
4. Security awareness levels typical for this industry/size
5. Technologies in use that suggest what content types would be opened"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)

            # Validate and sanitize response
            valid_profiles = list(PROFILE_DESCRIPTIONS.keys())

            # Ensure recommended profile is valid
            if result.get("recommended_profile") not in valid_profiles:
                result["recommended_profile"] = "it_department"

            # Ensure alternatives are valid
            result["alternative_profiles"] = [
                p for p in result.get("alternative_profiles", [])
                if p in valid_profiles and p != result["recommended_profile"]
            ][:2]

            # Ensure all required fields exist
            result.setdefault("confidence", "medium")
            result.setdefault("reasoning", "Based on the target profile analysis.")
            result.setdefault("suggested_labels", ["Backup", "IT Resources", "Confidential"])
            result.setdefault("suggested_filenames", [])
            result.setdefault("risk_factors", [])
            result.setdefault("tips", [])

            return result

        except Exception as e:
            logger.error(f"AI scenario recommendation failed: {e}")
            # Return a sensible default
            return self._get_default_recommendation(target)

    def _get_default_recommendation(self, target: Target) -> dict:
        """Get a rule-based default recommendation when AI fails."""
        # Simple rule-based fallback
        department_map = {
            "it": "it_department",
            "hr": "hr_documents",
            "finance": "finance",
            "executive": "executive",
            "engineering": "developer",
            "sales": "finance",
            "marketing": "hr_documents",
            "operations": "it_department",
            "legal": "executive",
            "research": "developer",
        }

        industry_map = {
            "healthcare": "hr_documents",
            "finance": "finance",
            "technology": "developer",
            "manufacturing": "it_department",
            "retail": "finance",
            "government": "security_audit",
            "education": "hr_documents",
            "legal": "executive",
            "consulting": "contractor",
        }

        # Priority: department > industry > default
        recommended = "it_department"

        if target.target_department and target.target_department.lower() in department_map:
            recommended = department_map[target.target_department.lower()]
        elif target.industry and target.industry.lower() in industry_map:
            recommended = industry_map[target.industry.lower()]

        # Generate alternatives
        all_profiles = list(PROFILE_DESCRIPTIONS.keys())
        alternatives = [p for p in all_profiles if p != recommended][:2]

        return {
            "recommended_profile": recommended,
            "confidence": "low",
            "reasoning": f"Default recommendation based on {target.target_department or target.industry or 'general'} targeting. AI recommendation unavailable.",
            "alternative_profiles": alternatives,
            "suggested_labels": [
                f"{target.company_name} Backup",
                "IT Resources",
                "Confidential Documents",
            ],
            "suggested_filenames": [],
            "risk_factors": ["Using default recommendation - consider manual review"],
            "tips": ["Gather more OSINT for better recommendations"],
        }

    async def generate_custom_labels(self, target: Target, profile_id: str, count: int = 5) -> list:
        """Generate custom USB drive label suggestions based on target and profile."""
        profile = PROFILE_DESCRIPTIONS.get(profile_id, PROFILE_DESCRIPTIONS["it_department"])

        prompt = f"""Generate {count} realistic USB drive label suggestions for a penetration test.

Target: {target.company_name} ({target.industry})
Profile Theme: {profile['name']}
Region: {target.geographic_region or 'US'}

The labels should:
1. Look like they could have been legitimately created by someone at {target.company_name}
2. Be intriguing enough that someone might plug it in to "return it to the owner"
3. Match the {profile['name']} theme
4. Include a mix of handwritten-style and printed-style suggestions
5. Some should include dates (Q4 2024, Dec 2024, etc.)

Return as a JSON array of strings."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are helping with authorized security testing."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.8,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            labels = result.get("labels", result.get("suggestions", []))

            if isinstance(labels, list):
                return labels[:count]

        except Exception as e:
            logger.error(f"Label generation failed: {e}")

        # Fallback labels
        return [
            f"{target.company_name} Backup",
            f"Q4 2024 - {profile['name']}",
            "CONFIDENTIAL",
            f"{target.industry.title()} Resources",
            "DO NOT FORMAT",
        ]
