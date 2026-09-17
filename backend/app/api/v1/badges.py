from fastapi import APIRouter, Response

router = APIRouter()

@router.get("/{poll_id}.svg")
def get_poll_badge(poll_id: str, title: str = "Poll", votes: int = 0):
    """
    Renders a cached SVG badge for GitHub READMEs (PRD §4.4).
    """
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="130" height="20" role="img" aria-label="{title}: {votes} votes">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="130" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <rect width="65" height="20" fill="#555"/>
    <rect x="65" width="65" height="20" fill="#4c1"/>
    <rect width="130" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text x="335" y="140" transform="scale(.1)" fill="#fff" textLength="500">{title}</text>
    <text x="965" y="140" transform="scale(.1)" fill="#fff" textLength="500">{votes} votes</text>
  </g>
</svg>"""
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=60, s-maxage=60"}
    )
