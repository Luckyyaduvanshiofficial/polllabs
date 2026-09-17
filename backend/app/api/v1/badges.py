import io
from fastapi import APIRouter, Response
from PIL import Image, ImageDraw
from app.core.config import settings
from app.core.dependencies import PocketBaseDep

router = APIRouter(prefix="/badges", tags=["Badges"])

def render_svg_badge(label: str, value: str, target_url: str = "", is_error: bool = False) -> str:
    """
    CPU-bound SVG badge generation (Shields.io style).
    Includes clickable link pointing to live poll on website (PRD §4.4).
    """
    val_color = "#e05d44" if is_error else "#4c1"
    width = max(130, len(label) * 8 + len(value) * 8 + 30)
    label_width = len(label) * 8 + 15
    val_width = width - label_width

    inner_svg = f"""  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="{width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{val_width}" height="20" fill="{val_color}"/>
    <rect width="{width}" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text x="{label_width * 5}" y="140" transform="scale(.1)" fill="#fff">{label}</text>
    <text x="{(label_width + val_width / 2) * 10}" y="140" transform="scale(.1)" fill="#fff">{value}</text>
  </g>"""

    if target_url:
        return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="20" role="img" aria-label="{label}: {value}">
  <a xlink:href="{target_url}" target="_blank">
  {inner_svg}
  </a>
</svg>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}: {value}">
{inner_svg}
</svg>"""

def render_png_badge(label: str, value: str, is_error: bool = False) -> bytes:
    """CPU-bound PNG badge generation using Pillow (PRD §4.4)."""
    val_color = (224, 93, 68) if is_error else (76, 175, 80)
    label_color = (85, 85, 85)
    text_color = (255, 255, 255)

    label_width = max(50, len(label) * 7 + 16)
    val_width = max(50, len(value) * 7 + 16)
    total_width = label_width + val_width
    height = 20

    img = Image.new("RGB", (total_width, height), color=label_color)
    draw = ImageDraw.Draw(img)

    # Draw value background
    draw.rectangle([label_width, 0, total_width, height], fill=val_color)

    # Draw text
    draw.text((8, 4), label, fill=text_color)
    draw.text((label_width + 8, 4), value, fill=text_color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

from app.services.poll_utils import is_poll_closed

def format_badge_data(poll: dict | None) -> tuple[str, str, bool, str]:
    """
    Extracts label, result value, error status, and target URL for badge rendering.
    Respects hidden_until_close and displays leading option with percentage breakdown (PRD §4.4).
    """
    if not poll:
        return "poll", "no longer available", True, ""

    poll_id = poll.get("id", "")
    target_url = f"{settings.FRONTEND_URL}/embed/{poll_id}"
    title = poll.get("title", "poll")
    label = title if len(title) <= 24 else f"{title[:22]}…"

    result_display = poll.get("result_display", "show_counts")
    closed = is_poll_closed(poll.get("close_at"))
    total_votes = poll.get("total_votes", 0)

    # PRD §3.2 & §4.4: Hidden until close check
    if result_display == "hidden_until_close" and not closed:
        return label, "results hidden until close", False, target_url

    # Compute leading option breakdown
    options = poll.get("options", [])
    if options and total_votes > 0:
        leading = max(options, key=lambda x: x.get("vote_count", 0))
        pct = round((leading.get("vote_count", 0) / total_votes) * 100)
        leading_text = leading.get("text", "leading")
        if len(leading_text) > 16:
            leading_text = f"{leading_text[:14]}…"
        value = f"{leading_text} {pct}% ({total_votes})"
    else:
        value = f"{total_votes} votes"

    return label, value, False, target_url

@router.get("/{poll_id}.svg")
async def get_poll_badge_svg(poll_id: str, pb: PocketBaseDep) -> Response:
    """
    Renders a live SVG badge linking to the interactive poll (PRD §4.4).
    Shows graceful 'no longer available' state when poll is missing.
    """
    poll = await pb.get_poll(poll_id)
    label, value, is_error, target_url = format_badge_data(poll)
    svg_content = render_svg_badge(label, value, target_url=target_url, is_error=is_error)

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=60, s-maxage=60"},
    )

@router.get("/{poll_id}.png")
async def get_poll_badge_png(poll_id: str, pb: PocketBaseDep) -> Response:
    """
    Renders a live raster PNG badge (PRD §4.4).
    """
    poll = await pb.get_poll(poll_id)
    label, value, is_error, _ = format_badge_data(poll)
    png_content = render_png_badge(label, value, is_error=is_error)

    return Response(
        content=png_content,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=60, s-maxage=60"},
    )
