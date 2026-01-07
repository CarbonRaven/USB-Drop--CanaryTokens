#!/usr/bin/env python3
"""Generate AI images for USB drop templates using DALL-E 3."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
import httpx

# Image prompts for each template - all G/PG rated
TEMPLATE_IMAGES = {
    "it_department": [
        {
            "filename": "server_room.jpg",
            "prompt": "Professional photograph of a modern data center server room with rows of server racks, blue LED lights, clean cable management, cool lighting atmosphere, corporate IT infrastructure"
        },
        {
            "filename": "network_diagram.jpg",
            "prompt": "Photograph of a whiteboard in an IT office with hand-drawn network topology diagram, colored markers, sticky notes, professional office setting"
        },
        {
            "filename": "helpdesk_workspace.jpg",
            "prompt": "IT helpdesk workstation with multiple monitors showing support tickets, headset, keyboard, corporate office environment, natural lighting"
        },
    ],

    "hr_documents": [
        {
            "filename": "office_team.jpg",
            "prompt": "Diverse group of professional office workers in business casual attire having a friendly team meeting in modern open office, natural lighting, positive atmosphere"
        },
        {
            "filename": "employee_event.jpg",
            "prompt": "Corporate employee appreciation event in office break room, cake and decorations, happy coworkers celebrating, professional but festive atmosphere"
        },
        {
            "filename": "onboarding_desk.jpg",
            "prompt": "New employee welcome desk setup with laptop, company welcome packet, branded mug, office supplies, clean modern office background"
        },
    ],

    "finance": [
        {
            "filename": "financial_charts.jpg",
            "prompt": "Professional photograph of computer monitor displaying financial charts and graphs, stock market data, modern trading desk, blue and green color scheme"
        },
        {
            "filename": "accounting_office.jpg",
            "prompt": "Clean organized accounting office workspace with dual monitors, calculator, neat stacks of documents, professional corporate environment"
        },
        {
            "filename": "budget_meeting.jpg",
            "prompt": "Business professionals in meeting room reviewing budget documents, laptops open, financial reports on table, glass-walled conference room"
        },
    ],

    "executive": [
        {
            "filename": "boardroom.jpg",
            "prompt": "Elegant corporate boardroom with long polished conference table, leather chairs, large windows with city skyline view, professional executive setting"
        },
        {
            "filename": "executive_office.jpg",
            "prompt": "Corner executive office with large desk, city view through floor-to-ceiling windows, modern minimalist decor, professional and prestigious atmosphere"
        },
        {
            "filename": "strategy_session.jpg",
            "prompt": "Executive team at whiteboard doing strategic planning, business charts and diagrams, professional attire, collaborative atmosphere"
        },
    ],

    "personal_backup": [
        {
            "filename": "vacation_beach.jpg",
            "prompt": "Beautiful tropical beach sunset with palm trees silhouette, calm ocean waves, golden hour lighting, vacation photography style"
        },
        {
            "filename": "family_picnic.jpg",
            "prompt": "Happy family having picnic in sunny park, picnic blanket with food, green grass, trees in background, warm summer day atmosphere"
        },
        {
            "filename": "pet_photo.jpg",
            "prompt": "Adorable golden retriever dog sitting in living room, happy expression, natural home lighting, pet portrait photography style"
        },
        {
            "filename": "birthday_party.jpg",
            "prompt": "Birthday celebration with cake and candles on table, colorful decorations, balloons, warm indoor lighting, festive home atmosphere"
        },
        {
            "filename": "city_travel.jpg",
            "prompt": "Tourist photograph of iconic city skyline at dusk, urban landscape, dramatic clouds, travel photography style"
        },
    ],

    "training_compliance": [
        {
            "filename": "training_room.jpg",
            "prompt": "Corporate training room with projector screen showing presentation, rows of chairs with notepads, professional learning environment"
        },
        {
            "filename": "workshop_session.jpg",
            "prompt": "Employees participating in interactive workshop, standing around flip chart, engaged discussion, modern office training space"
        },
        {
            "filename": "elearning_laptop.jpg",
            "prompt": "Laptop computer showing online training course interface, coffee cup beside it, home office or quiet workspace setting"
        },
        {
            "filename": "certificate.jpg",
            "prompt": "Professional certificate of completion on desk with pen, elegant paper with gold seal, corporate training achievement"
        },
    ],

    "social_creator": [
        {
            "filename": "coffee_lifestyle.jpg",
            "prompt": "Lifestyle photograph of young woman in casual sweater sitting at trendy coffee shop, holding latte, natural window light, warm cozy atmosphere"
        },
        {
            "filename": "fitness_gym.jpg",
            "prompt": "Young woman at modern gym in athletic wear, holding water bottle, fitness equipment in background, healthy active lifestyle"
        },
        {
            "filename": "beach_casual.jpg",
            "prompt": "Young woman in summer dress and sunhat at beach, ocean in background, golden hour lighting, vacation lifestyle photography"
        },
        {
            "filename": "home_office.jpg",
            "prompt": "Young woman working at stylish home office desk with laptop, plants and decor, natural lighting, modern remote work lifestyle"
        },
        {
            "filename": "urban_style.jpg",
            "prompt": "Young woman in casual trendy outfit on city street, urban background with buildings, street style fashion photography"
        },
    ],

    "project_client": [
        {
            "filename": "project_whiteboard.jpg",
            "prompt": "Whiteboard covered with project planning diagrams, sticky notes, timeline charts, Agile sprint planning, collaborative workspace"
        },
        {
            "filename": "client_meeting.jpg",
            "prompt": "Professional team meeting with clients around conference table, laptops open, presentation on screen, business casual attire"
        },
        {
            "filename": "kanban_board.jpg",
            "prompt": "Colorful Kanban board with sticky notes and task cards, project management visualization, modern office wall"
        },
        {
            "filename": "team_collaboration.jpg",
            "prompt": "Diverse team collaborating around large table with documents and laptops, open office space, engaged productive atmosphere"
        },
    ],

    "developer": [
        {
            "filename": "dev_workstation.jpg",
            "prompt": "Software developer workstation with multiple monitors showing code, mechanical keyboard, dark theme IDE, modern tech office"
        },
        {
            "filename": "code_review.jpg",
            "prompt": "Two developers doing code review at computer screen, pointing at code, collaborative programming session, office setting"
        },
        {
            "filename": "tech_meetup.jpg",
            "prompt": "Tech conference or meetup with attendees networking, presentation stage in background, startup and developer community vibe"
        },
    ],

    "network_admin": [
        {
            "filename": "patch_panel.jpg",
            "prompt": "Network patch panel with organized ethernet cables, fiber optic connections, clean cable management, professional data center"
        },
        {
            "filename": "rack_equipment.jpg",
            "prompt": "Network equipment rack with routers, switches, and servers, blinking status lights, organized cables, server room environment"
        },
        {
            "filename": "network_monitoring.jpg",
            "prompt": "Network monitoring dashboard on multiple screens, graphs and alerts, NOC or network operations center environment"
        },
    ],

    "security_audit": [
        {
            "filename": "security_dashboard.jpg",
            "prompt": "Cybersecurity monitoring dashboard with threat maps and alerts, multiple screens, security operations center, blue lighting"
        },
        {
            "filename": "audit_meeting.jpg",
            "prompt": "Security professionals reviewing documents in meeting room, audit papers on table, serious professional atmosphere"
        },
        {
            "filename": "penetration_test.jpg",
            "prompt": "Cybersecurity professional at workstation with terminal windows, security tools on screen, ethical hacking environment"
        },
    ],

    "contractor": [
        {
            "filename": "temporary_desk.jpg",
            "prompt": "Clean temporary contractor workspace with laptop, visitor badge visible, minimal personal items, corporate office hot desk"
        },
        {
            "filename": "project_kickoff.jpg",
            "prompt": "Project kickoff meeting with contractors and clients, presentation slides, introductions, professional conference room"
        },
        {
            "filename": "remote_work.jpg",
            "prompt": "Professional working remotely from home office, video call on laptop screen, business casual, dedicated workspace"
        },
    ],
}


async def generate_image(client: AsyncOpenAI, prompt: str, filename: str, output_dir: Path) -> bool:
    """Generate a single image using DALL-E 3."""
    try:
        print(f"  Generating: {filename}")

        # Add safety reminder to all prompts
        safe_prompt = f"{prompt}. Style: Professional, appropriate for business settings, G-rated content only."

        response = await client.images.generate(
            model="dall-e-3",
            prompt=safe_prompt,
            size="1024x1024",
            quality="standard",
            style="natural",
            n=1,
        )

        image_url = response.data[0].url

        # Download image
        async with httpx.AsyncClient() as http_client:
            img_response = await http_client.get(image_url)
            image_data = img_response.content

        # Save to file
        output_path = output_dir / filename
        with open(output_path, "wb") as f:
            f.write(image_data)

        print(f"  ✓ Saved: {filename} ({len(image_data)} bytes)")
        return True

    except Exception as e:
        print(f"  ✗ Failed: {filename} - {e}")
        return False


async def generate_template_images(template_id: str, images: list, output_base: Path):
    """Generate all images for a template."""
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    output_dir = output_base / template_id
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Template: {template_id}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")

    success_count = 0
    for img in images:
        if await generate_image(client, img["prompt"], img["filename"], output_dir):
            success_count += 1
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)

    print(f"\nCompleted {template_id}: {success_count}/{len(images)} images generated")
    return success_count


async def main():
    """Main function to generate all template images."""
    # Output directory for generated images - use uploads which is writable
    output_base = Path("/app/uploads/template_images")
    output_base.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("USB Drop Template Image Generator")
    print("="*60)
    print(f"Output directory: {output_base}")
    print(f"Templates to process: {len(TEMPLATE_IMAGES)}")

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    total_success = 0
    total_images = 0

    # Process each template
    for template_id, images in TEMPLATE_IMAGES.items():
        total_images += len(images)
        success = await generate_template_images(template_id, images, output_base)
        total_success += success

    print("\n" + "="*60)
    print(f"COMPLETE: Generated {total_success}/{total_images} images")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
