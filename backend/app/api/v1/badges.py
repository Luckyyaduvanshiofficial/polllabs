from fastapi import APIRouter, Response
from app.core.dependencies import PocketBaseDep

router = APIRouter(prefix="/badges", tags=["Badges"])

def render_svg_badge(label: str, value: str, is_error: bool = False) -> str:
    """CPU-bound SVG badge generation (Shields.io style)."""
    val_color = "#e05d44" if is_error else "#4c1"
    width = max(110, len(label) * 8 + len(value) * 8 + 30)
    label_width = len(label) * 8 + 15
    val_width = width - label_width

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}: {value}">
  <linearGradient id="b" x2="0" y2="100%">
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
  </g>
</svg>"""

@router.get("/{poll_id}.svg")
async def get_poll_badge(poll_id: str, pb: PocketBaseDep) -> Response:
    """
    Renders a live SVG badge for GitHub READMEs (PRD §4.4).
    Cached with short TTL to avoid regenerating on every README view.
    """
    poll = await pb.get_poll(poll_id)
    if not poll:
        svg_content = render_svg_badge("poll", "not found", is_error=True)
    else:
        title = poll.get("title", "poll")
        short_title = title if len(title) <= 20 else f"{title[:18]}…"
        total_votes = poll.get("total_votes", 0)
        svg_content = render_svg_badge(short_title, f"{total_votes} votes")

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=60, s-maxage=60"},
    )
