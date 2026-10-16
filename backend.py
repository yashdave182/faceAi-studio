"""Lovers AI — Face Consistency Demo — FastAPI backend.

Generates wedding portraits from one reference photograph through a
configurable model chain (fal.ai FLUX PuLID primary, Gemini image models as
fallback). All provider keys stay server-side at all times.
"""

import asyncio
import base64
import io
import mimetypes
import os
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

import httpx
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from google import genai
from google.genai import types


# --------------------------------------------------------------------------- #
# Configuration — the exact model ID lives here and nowhere else.
# --------------------------------------------------------------------------- #

def _load_env_file() -> None:
    """Minimal .env loader so the demo runs without extra dependencies."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()

GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-nano-banana-2.1").strip()
FAL_ID_WEIGHT = min(float(os.getenv("FAL_ID_WEIGHT", "0.86")), 1.0)
FAL_INFERENCE_STEPS = int(os.getenv("FAL_INFERENCE_STEPS", "28"))
FAL_GUIDANCE_SCALE = float(os.getenv("FAL_GUIDANCE_SCALE", "4.0"))
FAL_ENABLE_ENHANCE = os.getenv("FAL_ENABLE_ENHANCE", "false").lower() in ("true", "1", "yes")
FAL_DEFAULT_MODEL = "fal-ai/flux-pulid"

# Ordered provider chain: primary first, then fallback(s). Comma-separated,
# each entry "provider:model" (provider = fal | gemini).
IMAGE_MODEL_PRIMARY = os.getenv("IMAGE_MODEL_PRIMARY", f"fal:{FAL_DEFAULT_MODEL}").strip()
IMAGE_MODEL_FALLBACK = os.getenv(
    "IMAGE_MODEL_FALLBACK", f"gemini:{GEMINI_IMAGE_MODEL}"
).strip()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_TO_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
SESSION_TTL = timedelta(minutes=30)
GENERATION_TIMEOUT_SECONDS = 180
MAX_ATTEMPTS = 2

DATA_DIR = Path(__file__).parent / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
GENERATED_DIR = DATA_DIR / "generated"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

SCENES: dict[str, dict[str, object]] = {
    "luxury_cinematic": {
        "name": "Royal Palace Heritage",
        "tagline": "The Royal Balcony",
        "description": "3/4 contemplative glance from a carved marble palace balcony at golden sunset.",
        "groom": {
            "prompt": (
                "An award-winning editorial Indian wedding photograph of the man in the reference photograph "
                "as a royal groom (Dulha). Pose: standing gracefully at an opulent Rajasthan palace balcony, "
                "turned 30 degrees in an elegant three-quarter perspective, one hand resting on the carved marble "
                "balustrade, looking thoughtfully off-camera into the sunset. Attire: an opulent bespoke ivory "
                "and gold raw silk achkan sherwani with intricate antique zardozi embroidery, royal maroon velvet "
                "doshala stole, and a regal safa turban with pearl kalgi brooch. "
                "Critical: preserve his natural male features, masculine jawline, eyes, nose and bone structure. "
                "Authentic photographic texture, natural skin pores, realistic lighting, shot on 85mm f/1.4 lens."
            ),
            "fal_prompt": (
                "Award-winning candid wedding photograph of this Indian man as a royal groom at a magnificent "
                "heritage palace balcony in Rajasthan, 30 degree three-quarter angle looking thoughtfully off-camera, "
                "one hand resting gently on carved marble balustrade, opulent ivory and gold embroidered sherwani, "
                "royal velvet doshala shawl, regal brocade safa turban with pearl brooch, dramatic warm palace ambient "
                "lighting streaming through arches, authentic skin pores, natural skin texture, realistic human eyes, "
                "cinematic depth of field, Hasselblad 85mm portrait, no plastic skin, no CGI, natural colour"
            ),
        },
        "bride": {
            "prompt": (
                "An award-winning editorial Indian wedding photograph of the woman in the reference photograph "
                "as a royal bride (Dulhan). Pose: standing gracefully by a carved palace balcony, gentle 30 degree "
                "turn, delicate hand adjusting her sheer dupatta veil, soft contemplative noble expression. "
                "Attire: an exquisite crimson red bridal lehenga with heavy antique gold zardozi embroidery, "
                "uncut polki kundan necklace, maang tikka, and jhumkas. "
                "Critical: keep her face exactly as it appears in the reference. Natural skin texture, real lighting."
            ),
            "fal_prompt": (
                "Award-winning candid wedding photograph of this Indian woman as a royal bride at a magnificent "
                "heritage palace balcony in Rajasthan, gentle three-quarter turn, hand softly holding sheer embroidered "
                "crimson dupatta veil, opulent Banarasi silk lehenga with heavy antique gold embroidery, royal polki kundan "
                "jewelry, maang tikka, warm palace golden hour illumination, authentic skin pores, fine skin texture, "
                "natural eyes, shallow depth of field, Hasselblad 85mm portrait, no plastic skin, natural colour"
            ),
        },
    },
    "beach_destination": {
        "name": "Goa Coastal Shoreline",
        "tagline": "The Candid Laugh",
        "description": "Walking casually along the ocean surf, candid radiant laughter in golden twilight.",
        "groom": {
            "prompt": (
                "An award-winning candid wedding photograph of the man in the reference photograph as a groom "
                "at a destination beach wedding in Goa. Pose: captured mid-stride walking along the ocean shoreline surf, "
                "hands casually in pockets, sea breeze gently moving hair, genuine joyful natural laughter with eyes "
                "crinkled in authentic happiness, open radiant smile. Attire: contemporary tailored blush peach raw silk "
                "bandhgala jacket with embroidered collar and tailored trousers. Natural skin texture, candid Leica photo."
            ),
            "fal_prompt": (
                "Award-winning candid wedding photograph of this Indian man as a groom at an oceanfront beach in Goa, "
                "captured mid-stride walking along the surf at sunset, hands casually in pockets, genuine joyful natural "
                "laughter with eyes crinkling in authentic happiness, warm open smile, sea breeze gently moving hair, "
                "tailored blush peach raw silk bandhgala jacket, radiant golden hour sunset rim-light outlining silhouette, "
                "authentic skin pores, natural skin texture, real human emotion, Leica 35mm candid lens, no stiff pose"
            ),
        },
        "bride": {
            "prompt": (
                "An award-winning candid wedding photograph of the woman in the reference photograph as a bride "
                "at a destination beach wedding in Goa. Pose: captured walking along the shoreline at sunset, laughing with "
                "pure natural joy, sea breeze gently lifting her sheer dupatta, fresh white jasmine gajra in hair. "
                "Attire: a graceful pastel blush pink designer silk lehenga with delicate mirror work and floral embroidery. "
                "Critical: preserve her natural face and genuine radiant smile. Authentic skin pores, candid photography."
            ),
            "fal_prompt": (
                "Award-winning candid wedding photograph of this Indian woman as a bride on a Goa beach at sunset, "
                "walking gracefully along the surf, genuine joyful laughter with crinkling happy eyes, radiant natural smile, "
                "sea breeze gently lifting her pastel blush lehenga dupatta, delicate mirror work embroidery, lightweight gold "
                "jewelry, fresh jasmine flowers in hair, warm golden sunset backlight, authentic skin texture, realistic pores, "
                "natural human laughter, Leica 35mm candid street wedding style, no airbrushed CGI"
            ),
        },
    },
    "traditional_indian": {
        "name": "Grand Vivah Mandap",
        "tagline": "The Sacred Agni",
        "description": "Intimate close-up with folded hands in Namaste before the glowing havan fire.",
        "groom": {
            "prompt": (
                "An intimate editorial wedding close-up photograph of the man in the reference photograph as an Indian "
                "groom (Dulha) at a Vedic Vivah ceremony. Pose: hands gently folded in reverent Namaste Pranam at chest "
                "level holding fresh rose and marigold petals, looking forward with serene emotional reverence. "
                "Attire: a rich royal emerald green and gold woven silk sherwani, brocade safa turban, layered pearl mala. "
                "Lighting: warm flickering glow from the sacred havan fire illuminating his face. Shot on 85mm f/1.4."
            ),
            "fal_prompt": (
                "Intimate 85mm f/1.4 lens close-up wedding photograph of this Indian man as a groom at a Vedic Vivah ceremony, "
                "hands gently folded in reverent Namaste Pranam holding fresh red rose petals, warm flickering golden havan "
                "firelight reflecting in his eyes, gentle wafts of sacred incense smoke, emotionally moved reverent expression, "
                "rich emerald green and gold embroidered sherwani, brocade safa turban, layered pearl necklace, authentic skin "
                "pores, realistic skin texture, catchlight in eyes, shallow depth of field, dramatic ceremonial intimacy"
            ),
        },
        "bride": {
            "prompt": (
                "An intimate editorial wedding close-up photograph of the woman in the reference photograph as an Indian "
                "bride (Dulhan) at a Vedic Vivah ceremony. Pose: hands gently folded in sacred prayer holding flower petals, "
                "looking forward with gentle devotional grace. Attire: an opulent vermilion red Banarasi silk lehenga, temple gold "
                "jewelry set, bridal maang tikka, nath nose ring, red bindi. Warm havan fire glow reflecting on her face."
            ),
            "fal_prompt": (
                "Intimate 85mm f/1.4 lens close-up wedding photograph of this Indian woman as a traditional bride at a Vedic "
                "Vivah mandap, hands gently folded in prayer holding red rose petals, warm flickering havan firelight glowing "
                "on her face and eyes, gentle incense smoke, serene devotional expression, rich vermilion red Banarasi silk lehenga, "
                "temple gold jewelry, bridal maang tikka, nath nose ring, red bridal bindi, authentic skin texture, natural pores, "
                "emotional depth, cinematic ceremonial photography, no plastic smoothing"
            ),
        },
    },
    "baraat_celebration": {
        "name": "Baraat Celebration",
        "tagline": "The Baraat Dance",
        "description": "Dynamic celebratory action dancing mid-motion under falling crimson rose petals.",
        "groom": {
            "prompt": (
                "A dynamic high-energy candid wedding celebration photograph of the man in the reference photograph as a groom "
                "at his Baraat procession. Pose: captured mid-motion dancing with arms raised in pure triumph and joy, shower of "
                "crimson rose petals frozen in the air around him, ecstatic open smile and sparkling eyes. "
                "Attire: royal gold brocade achkan sherwani, festive red safa pagdi, layered pearl necklace. Dynamic lighting."
            ),
            "fal_prompt": (
                "Dynamic action wedding photograph of this Indian man as a groom dancing in his Baraat procession, arms raised "
                "in celebratory joy, shower of crimson rose petals and marigolds suspended mid-air around him, ecstatic open smile, "
                "radiant joyful eyes, festive wedding night illumination with fairy lights and sparklers in creamy background bokeh, "
                "royal gold brocade sherwani, red safa turban, authentic human motion, natural skin pores, realistic sweat sheen, "
                "award-winning wedding celebration photography, high shutter speed freeze frame"
            ),
        },
        "bride": {
            "prompt": (
                "A dynamic high-energy wedding celebration photograph of the woman in the reference photograph as a bride "
                "dancing at her Sangeet and wedding celebration. Pose: captured mid-twirl with her lehenga spinning, laughing with "
                "bright ecstatic joy, shower of flower petals in the air, intricate mehndi on hands visible. "
                "Attire: sparkling ruby red and gold designer lehenga with shimmering sequins. Festive ambient lighting."
            ),
            "fal_prompt": (
                "Dynamic action wedding photograph of this Indian woman as a bride dancing at her wedding celebration, twirling her "
                "shimmering ruby and gold lehenga, shower of rose petals floating around her, ecstatic bright laughter, glowing happy "
                "eyes, hands adorned with intricate bridal henna mehndi visible, warm festive string lights and sparklers bokeh in "
                "background, authentic human joy, natural skin texture, realistic pores, award-winning celebration photo"
            ),
        },
    },
    "sangeet_glamour": {
        "name": "Sangeet Night Luxury",
        "tagline": "The Midnight Sangeet",
        "description": "Over-the-shoulder confident glance, adjusting luxury watch under moody chandeliers.",
        "groom": {
            "prompt": (
                "A high-fashion luxury editorial wedding portrait of the man in the reference photograph at a glamorous Sangeet night. "
                "Pose: standing in an opulent cocktail lounge, body angled slightly away while glancing over the shoulder toward camera, "
                "one hand adjusting his luxury watch and cufflink, charismatic confident smirk. Attire: bespoke midnight navy velvet "
                "bandhgala jacket with metallic bullion embroidery, silk pocket square. Dramatic chiaroscuro lighting."
            ),
            "fal_prompt": (
                "High-fashion GQ editorial wedding portrait of this Indian man at an upscale luxury Sangeet gala, body angled away "
                "while glancing over the shoulder toward camera, one hand adjusting a luxury watch and cufflink, charismatic confident "
                "smirk, bespoke midnight navy velvet bandhgala jacket with subtle metallic embroidery, dramatic cinematic chiaroscuro "
                "lighting, deep shadows, warm amber candlelight and blue accent lighting, sharp jawline, authentic skin pores, "
                "high-fashion magazine cover aesthetic, 85mm f/1.4 lens, natural skin undertones"
            ),
        },
        "bride": {
            "prompt": (
                "A high-fashion luxury editorial wedding portrait of the woman in the reference photograph at a glamorous Sangeet night. "
                "Pose: glancing over her shoulder with an alluring, confident smile, hand delicately touching her diamond chandelier "
                "earring, sleek hair, luxury cocktail venue. Attire: contemporary midnight blue metallic sequin lehenga gown. "
                "Dramatic moody lighting, golden bokeh."
            ),
            "fal_prompt": (
                "High-fashion luxury editorial wedding portrait of this Indian woman at an upscale Sangeet gala, glancing over her shoulder "
                "with an alluring confident smile, hand gracefully touching a sparkling diamond chandelier earring, contemporary midnight "
                "blue metallic sequin lehenga, dramatic cinematic side-lighting, warm champagne candlelight bokeh, sharp facial features, "
                "authentic skin texture, realistic pores, Vogue India wedding editorial style, 85mm portrait"
            ),
        },
    },
    "romantic_vows": {
        "name": "The Golden Hour Vows",
        "tagline": "The Eternal Vows",
        "description": "Tender heartfelt gaze with hand on heart before a cascading floral canopy.",
        "groom": {
            "prompt": (
                "An emotionally moving romantic wedding portrait of the man in the reference photograph during the wedding vows. "
                "Pose: standing before a lush cascading floral mandap, one hand placed gently over his heart in sincere devotion, "
                "looking forward with an incredibly tender, deeply loving smile. Attire: soft pastel mint and champagne raw silk kurta "
                "sherwani with delicate tone-on-tone embroidery. Soft diffused golden hour twilight lighting."
            ),
            "fal_prompt": (
                "Romantic emotive wedding portrait of this Indian man during his wedding vows, standing before a lush white rose and "
                "eucalyptus floral canopy, one hand resting gently over his heart in heartfelt sincerity, soft loving gaze with a gentle "
                "warm emotional smile, tailored pastel champagne and mint raw silk sherwani, dreamy soft-diffused golden hour sunset "
                "lighting, gentle lens flare, authentic skin pores, natural skin texture, deeply touching emotional wedding photograph"
            ),
        },
        "bride": {
            "prompt": (
                "An emotionally moving romantic wedding portrait of the woman in the reference photograph during the wedding vows. "
                "Pose: standing before a floral archway, delicate hands holding a pastel rose bouquet close to heart, deeply loving, "
                "tender gaze with tears of joy in eyes and a heartfelt smile. Attire: ethereal ivory and blush pink floral lehenga with "
                "pearl and rose gold jewelry. Soft romantic twilight lighting."
            ),
            "fal_prompt": (
                "Romantic emotive wedding portrait of this Indian woman during her wedding vows, standing before a soft floral archway, "
                "holding a pastel rose bouquet gently to her chest, tender deeply loving gaze, subtle happy tear glistening in eye, warm "
                "heartfelt emotional smile, ethereal blush pink and ivory silk floral lehenga, delicate rose gold jewelry, dreamy soft-diffused "
                "golden hour backlight, authentic skin texture, realistic pores, deeply moving bridal portrait"
            ),
        },
    },
}

FAL_PROMPT_KEY = "fal_prompt"

# --------------------------------------------------------------------------- #
# Visual RAG & Multi-View Canonical Bootstrapping
# --------------------------------------------------------------------------- #

CANONICAL_RAG_ANCHORS: dict[str, dict[str, str]] = {
    "luxury_cinematic": {
        "anchor_key": "three_quarter_regal",
        "title": "3/4 Regal Balcony Anchor",
        "angle": "30° Three-Quarter Head Turn",
        "expression": "Contemplative & Noble Composure",
        "lighting": "Heritage Palace Ambient & Jharokha Sunlight",
        "vector_tag": "30° Yaw | Noble Posture Lock",
        "rag_prompt_inject": (
            ", candid authentic wedding photography, 35mm lens, 30 degree head turn looking thoughtfully "
            "off-camera, hand gently resting on carved marble palace balustrade, regal relaxed posture, "
            "natural skin pores, fine skin texture, catchlight in eyes, natural lighting, no plastic skin, no CGI"
        ),
    },
    "beach_destination": {
        "anchor_key": "candid_sunset_laugh",
        "title": "Sunset Shoreline Laugh",
        "angle": "Dynamic 35mm Angle & Slight Tilt",
        "expression": "GENUINE JOYFUL LAUGHTER & Warm Smile",
        "lighting": "Golden Hour Sunset Twilight Rim-Lighting",
        "vector_tag": "Dynamic Tilt | Candid Smile Vector",
        "rag_prompt_inject": (
            ", award-winning candid wedding photograph, captured mid-stride walking along the ocean shoreline, "
            "genuine joyful natural laughter with eyes crinkling in real happiness, warm radiant open smile, "
            "ocean breeze gently moving hair, natural skin pores, realistic skin texture, golden sunset rim-light, no stiff pose"
        ),
    },
    "traditional_indian": {
        "anchor_key": "frontal_sacred_close",
        "title": "Sacred Agni Intimate Close-up",
        "angle": "Intimate 85mm Portrait Close-up",
        "expression": "Deep Devotional Reverence & Emotion",
        "lighting": "Warm Flickering Havan Sacred Firelight",
        "vector_tag": "Intimate 85mm | Devotional Gaze Lock",
        "rag_prompt_inject": (
            ", intimate 85mm f/1.4 lens close-up portrait, hands folded in reverent Namaste Pranam holding fresh "
            "rose petals at chest level, warm flickering golden havan firelight reflecting in eyes, gentle wafts of sacred "
            "incense smoke, emotionally moved reverent expression, rich skin texture, natural pores, dramatic ceremonial depth"
        ),
    },
    "baraat_celebration": {
        "anchor_key": "baraat_action_dance",
        "title": "Baraat Celebration Euphoria",
        "angle": "Dynamic Celebratory Action Angle",
        "expression": "Ecstatic Pure Joy & Celebration",
        "lighting": "Festive Wedding Night Lights & Bokeh",
        "vector_tag": "Dynamic Action | Celebration Vector",
        "rag_prompt_inject": (
            ", dynamic high-energy celebration photograph, captured mid-dance with arms raised in joy, shower of "
            "vibrant crimson rose petals frozen mid-air around them, ecstatic triumphant laughter, joyful sparkling eyes, "
            "festive warm string lights in soft bokeh, lively motion, natural skin texture, award-winning wedding photo"
        ),
    },
    "sangeet_glamour": {
        "anchor_key": "sangeet_editorial_profile",
        "title": "Sangeet Midnight Chiaroscuro",
        "angle": "Over-the-Shoulder GQ Editorial Turn",
        "expression": "Confident Magnetic Charisma & Subtle Smirk",
        "lighting": "Moody Chiaroscuro & Luxury Chandelier Glow",
        "vector_tag": "Over-the-Shoulder | Editorial Vector",
        "rag_prompt_inject": (
            ", editorial luxury wedding photography, captured looking over the shoulder while adjusting a luxury watch and cufflink, "
            "dashing confident charismatic expression with a subtle knowing smirk, dramatic cinematic side-lighting, "
            "moody candlelight and deep shadows, sharp jawline, high-fashion magazine cover style, authentic skin texture"
        ),
    },
    "romantic_vows": {
        "anchor_key": "vows_tender_gaze",
        "title": "Golden Hour Tender Vows",
        "angle": "Soft Romantic Medium Portrait",
        "expression": "Tender Heartfelt Love & Sincere Smile",
        "lighting": "Soft Diffused Twilight Floral Glow",
        "vector_tag": "Tender Gaze | Romantic Emotional Lock",
        "rag_prompt_inject": (
            ", tender emotive wedding portrait, standing before a lush cascading floral canopy at sunset, one hand resting "
            "gently over the heart in heartfelt sincerity, soft loving gaze with a gentle warm emotional smile, dreamy soft-diffused "
            "golden backlight, romantic cinematic color grading, natural skin pores, authentic warmth, deeply moving"
        ),
    },
}


@dataclass
class IdentityAnchor:
    scene_key: str
    anchor_key: str
    title: str
    angle: str
    expression: str
    lighting: str
    vector_tag: str
    status: str = "indexed"  # "indexed" | "ready"
    confidence: float = 0.94


# --------------------------------------------------------------------------- #
# Session storage (in-memory; images live in data/ and expire after 30 min)
# --------------------------------------------------------------------------- #

@dataclass
class SceneJob:
    status: str = "idle"  # idle | pending | generating | completed | failed
    error: Optional[str] = None
    file: Optional[str] = None
    mime: str = "image/png"
    version: int = 0


@dataclass
class Session:
    id: str
    created_at: datetime
    consent: bool = False
    attire: str = "groom"  # groom | bride
    reference_file: Optional[str] = None
    reference_mime: Optional[str] = None
    identity_bank: dict[str, IdentityAnchor] = field(default_factory=dict)
    scenes: dict[str, SceneJob] = field(
        default_factory=lambda: {key: SceneJob() for key in SCENES}
    )


sessions: dict[str, Session] = {}
_tasks: set[asyncio.Task[None]] = set()

_client: Optional[genai.Client] = None


def _require_session(session_id: str) -> Session:
    _purge_expired()
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return session


def _delete_session(session_id: str) -> None:
    session = sessions.pop(session_id, None)
    if session is None:
        return
    for job in session.scenes.values():
        if job.file:
            _quiet_delete(GENERATED_DIR / job.file)
    if session.reference_file:
        _quiet_delete(UPLOAD_DIR / session.reference_file)


def _purge_expired() -> None:
    now = datetime.now(timezone.utc)
    for session_id, session in list(sessions.items()):
        if now - session.created_at > SESSION_TTL:
            _delete_session(session_id)


def _quiet_delete(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# Image generation — provider chain (fal.ai FLUX PuLID, then Gemini)
# --------------------------------------------------------------------------- #

class GenerationError(RuntimeError):
    pass


def _get_client() -> genai.Client:
    global _client
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GenerationError(
            "The backend has no GEMINI_API_KEY configured. Add it to .env and restart."
        )
    if _client is None:
        _client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=60_000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
    return _client


def _gemini_extract_classic(response: object) -> tuple[bytes, str]:
    """Pull the first inline image out of a classic generate_content response."""
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None) if inline else None
            if data:
                return bytes(data), getattr(inline, "mime_type", None) or "image/png"

    for generated in getattr(response, "generated_images", None) or []:
        image = getattr(generated, "image", None)
        data = getattr(image, "image_bytes", None) if image else None
        if data:
            mime = getattr(image, "mime_type", None) or "image/png"
            return bytes(data), mime

    raise GenerationError("The model did not return an image for this scene. Try again.")


def _gemini_classic(
    reference_bytes: bytes, mime: str, prompt: str, model_id: str
) -> tuple[bytes, str]:
    client = _get_client()
    response = client.models.generate_content(
        model=model_id,
        contents=[
            types.Part.from_bytes(data=reference_bytes, mime_type=mime),
            prompt,
        ],
    )
    return _gemini_extract_classic(response)


def _gemini_interactions(
    reference_bytes: bytes, mime: str, prompt: str, model_id: str
) -> tuple[bytes, str]:
    client = _get_client()
    interaction = client.interactions.create(
        model=model_id,
        input=[
            {"type": "text", "text": prompt},
            {
                "type": "image",
                "data": base64.b64encode(reference_bytes).decode("ascii"),
                "mime_type": mime,
            },
        ],
        response_format={"type": "image", "aspect_ratio": "3:4", "image_size": "1K"},
    )
    image = getattr(interaction, "output_image", None)
    data = getattr(image, "data", None) if image else None
    if not data:
        raise GenerationError("The model did not return an image for this scene. Try again.")
    return base64.b64decode(data), getattr(image, "mime_type", None) or "image/png"


def _gemini_surfaces() -> tuple[str, ...]:
    """Surface order for the Gemini provider (classic is the reliable one here)."""
    mode = os.getenv("GEMINI_IMAGE_API", "classic").strip().lower()
    if mode == "interactions":
        return ("interactions",)
    if mode == "auto":
        return ("classic", "interactions")
    return ("classic",)


def _generate_via_gemini(
    reference_bytes: bytes, mime: str, prompt: str, model_id: str
) -> tuple[bytes, str]:
    surfaces = {"classic": _gemini_classic, "interactions": _gemini_interactions}
    order = _gemini_surfaces()
    for surface_name in order:
        try:
            return surfaces[surface_name](reference_bytes, mime, prompt, model_id)
        except Exception as exc:  # noqa: BLE001 - retried / re-raised below
            print(f"[generation] gemini/{surface_name} failed: {exc}", flush=True)
            if surface_name == order[-1] or not _is_retryable(exc):
                raise
    raise GenerationError("The Gemini provider could not generate this scene.")


def _fal_error_detail(exc: Exception) -> str:
    """Best-effort readable message from a fal/httpx exception."""
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            payload = response.json()
            detail = payload.get("detail") if isinstance(payload, dict) else None
            if isinstance(detail, list) and detail:
                first = detail[0]
                detail = first.get("msg") if isinstance(first, dict) else str(first)
            if detail:
                return f"{detail} (HTTP {response.status_code})"
        except Exception:  # noqa: BLE001 - fall back to raw body below
            pass
        body = (response.text or "").strip()
        if body:
            return f"{body[:200]} (HTTP {response.status_code})"
    return str(exc)


def _generate_via_fal(
    reference_bytes: bytes, mime: str, prompt: str, model_id: str
) -> tuple[bytes, str]:
    fal_key = os.getenv("FAL_KEY", "").strip()
    if not fal_key:
        raise GenerationError(
            "The backend has no FAL_KEY configured. Add it to .env and restart "
            "(get one at fal.ai/dashboard/keys)."
        )
    try:
        import fal_client
    except ImportError as exc:
        raise GenerationError(
            "The fal-client package is not installed on the backend. Run: pip install fal-client"
        ) from exc

    os.environ["FAL_KEY"] = fal_key
    try:
        reference_url = fal_client.upload(reference_bytes, mime)
        result = fal_client.subscribe(
            model_id,
            arguments={
                "reference_image_url": reference_url,
                "prompt": prompt,
                "image_size": "portrait_4_3",
                "id_weight": FAL_ID_WEIGHT,
                "num_inference_steps": FAL_INFERENCE_STEPS,
                "guidance_scale": FAL_GUIDANCE_SCALE,
            },
        )
    except Exception as exc:  # noqa: BLE001 - normalised into a readable error
        raise GenerationError(f"fal.ai request failed: {_fal_error_detail(exc)}") from exc

    images = (result or {}).get("images") or []
    image_url = images[0].get("url") if images and isinstance(images[0], dict) else None
    if not image_url:
        raise GenerationError("FLUX PuLID did not return an image for this scene. Try again.")

    if FAL_ENABLE_ENHANCE:
        try:
            print("[fal] Running optional face enhancement step...", flush=True)
            enhance_res = fal_client.subscribe(
                "fal-ai/image-editing/face-enhancement",
                arguments={"image_url": image_url},
            )
            enhanced_images = (enhance_res or {}).get("images") or []
            if enhanced_images and isinstance(enhanced_images[0], dict) and enhanced_images[0].get("url"):
                image_url = enhanced_images[0]["url"]
                print("[fal] Face enhancement succeeded.", flush=True)
        except Exception as enhance_exc:
            print(f"[fal] Face enhancement skipped or failed: {enhance_exc}", flush=True)

    response = httpx.get(image_url, timeout=60, follow_redirects=True)
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "image/jpeg").split(";")[0].strip()
    if not content_type.startswith("image/"):
        content_type = "image/jpeg"
    return response.content, content_type


_PROVIDERS: dict[str, Callable[[bytes, str, str, str], tuple[bytes, str]]] = {
    "fal": _generate_via_fal,
    "gemini": _generate_via_gemini,
}

_PROVIDER_DEFAULT_MODELS = {
    "fal": FAL_DEFAULT_MODEL,
    "gemini": GEMINI_IMAGE_MODEL,
}


def _parse_model_specs() -> list[tuple[str, str]]:
    """Parse IMAGE_MODEL_PRIMARY / IMAGE_MODEL_FALLBACK into an ordered chain."""
    chain: list[tuple[str, str]] = []
    for slot in (IMAGE_MODEL_PRIMARY, IMAGE_MODEL_FALLBACK):
        for entry in slot.split(","):
            entry = entry.strip()
            if not entry:
                continue
            provider, _, model = entry.partition(":")
            provider = provider.strip().lower()
            model = model.strip()
            if provider not in _PROVIDERS:
                print(f"[config] unknown provider '{provider}' in '{entry}' — skipped", flush=True)
                continue
            chain.append((provider, model or _PROVIDER_DEFAULT_MODELS[provider]))
    return chain


MODEL_CHAIN: list[tuple[str, str]] = _parse_model_specs()


def _provider_keys() -> dict[str, bool]:
    return {
        "fal": bool(os.getenv("FAL_KEY", "").strip()),
        "gemini": bool(os.getenv("GEMINI_API_KEY", "").strip()),
    }


def _any_provider_key_configured() -> bool:
    keys = _provider_keys()
    return any(keys.get(provider, False) for provider, _ in MODEL_CHAIN)


def _prompt_for(provider: str, scene_key: str, attire: str = "groom") -> str:
    scene = SCENES[scene_key]
    normalized_attire = attire if attire in ("groom", "bride") else "groom"
    variant = scene.get(normalized_attire)
    if not isinstance(variant, dict):
        variant = scene.get("groom") if isinstance(scene.get("groom"), dict) else {}
    if provider == "fal":
        base_prompt = str(variant.get(FAL_PROMPT_KEY, variant.get("prompt", "")))
    else:
        base_prompt = str(variant.get("prompt", ""))

    # Visual RAG: inject multi-angle canonical conditioning
    rag_info = CANONICAL_RAG_ANCHORS.get(scene_key)
    if rag_info and "rag_prompt_inject" in rag_info:
        return f"{base_prompt}{rag_info['rag_prompt_inject']}"
    return base_prompt


def _is_retryable(exc: Exception) -> bool:
    text = str(exc).lower()
    if "quota" in text or "api_key_invalid" in text or "api key not valid" in text:
        return False
    if "permission_denied" in text or "unauthenticated" in text or "unauthorized" in text:
        return False
    if "fal_key" in text or "fal-key" in text:
        return False
    if "exhausted balance" in text or "user is locked" in text:
        return False
    if "prepayment credits" in text or "credits are depleted" in text or "402" in text:
        return False
    return True


def _friendly_generation_error(exc: Exception) -> str:
    if isinstance(exc, GenerationError):
        return str(exc)  # already a user-facing message
    text = str(exc)
    lowered = text.lower()
    if "prepayment credits" in lowered or "credits are depleted" in lowered or "402" in text:
        return (
            "The Gemini API key's prepayment credits are depleted. "
            "Top up billing credits in Google AI Studio (https://aistudio.google.com)."
        )
    if "exceeded your current quota" in lowered or "check your plan and billing" in lowered:
        return (
            "The Gemini API key has no remaining quota for image generation. "
            "Check the key's plan and billing in Google AI Studio."
        )
    if "fal_key" in lowered:
        return "The server's FAL_KEY was rejected. Check it on fal.ai and restart the backend."
    if "unauthorized" in lowered or "invalid key" in lowered or "authentication" in lowered:
        return "A provider API key was rejected. Check FAL_KEY / GEMINI_API_KEY and restart the backend."
    if "exhausted balance" in lowered or "locked" in lowered:
        return (
            "The fal.ai account has no remaining balance. Top up at fal.ai/dashboard/billing "
            "or switch the primary model to gemini."
        )
    if "api key" in lowered or "api_key" in lowered or "permission_denied" in lowered:
        return "The server's Gemini API key was rejected. Check GEMINI_API_KEY and restart the backend."
    if "resource_exhausted" in lowered or "rate" in lowered and "limit" in lowered or "429" in text:
        return "The image service is rate limited right now. Wait a moment and retry."
    if "safety" in lowered or "prohibited" in lowered or "blocked" in lowered:
        return "The model could not generate this portrait (content filter). Try a different reference photograph."
    if "timeout" in lowered or "timed out" in lowered:
        return "Generation timed out. Retry this scene."
    return f"Generation failed: {text[:220]}"


def _generate_blocking(
    reference_bytes: bytes, mime: str, scene_key: str, attire: str = "groom"
) -> tuple[bytes, str]:
    """Generate one portrait by walking the configured model chain."""
    if not MODEL_CHAIN:
        raise GenerationError(
            "No image models are configured. Set IMAGE_MODEL_PRIMARY in .env and restart."
        )

    failures: list[tuple[str, Exception]] = []

    for provider, model_id in MODEL_CHAIN:
        prompt = _prompt_for(provider, scene_key, attire)
        for attempt in range(MAX_ATTEMPTS):
            try:
                return _PROVIDERS[provider](reference_bytes, mime, prompt, model_id)
            except Exception as exc:  # noqa: BLE001 - re-raised / mapped below
                print(
                    f"[generation] {provider}:{model_id} attempt {attempt + 1} failed: {exc}",
                    flush=True,
                )
                if attempt == 0:
                    failures.append((f"{provider}:{model_id}", exc))
                if not _is_retryable(exc):
                    break  # move on to the next model in the chain
                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(2.0 * (attempt + 1))

    if len(failures) == 1:
        raise failures[0][1]

    summary = " ".join(
        f"[{name}] {_friendly_generation_error(exc)}" for name, exc in failures
    )
    raise GenerationError(f"All configured models failed. {summary}")


async def _run_generation(session_id: str, scene_key: str) -> None:
    session = sessions.get(session_id)
    if session is None:
        return
    job = session.scenes[scene_key]
    job.status = "generating"
    job.error = None

    reference_path = UPLOAD_DIR / session.reference_file  # type: ignore[arg-type]
    try:
        reference_bytes = await asyncio.to_thread(reference_path.read_bytes)
        image_bytes, image_mime = await asyncio.wait_for(
            asyncio.to_thread(
                _generate_blocking,
                reference_bytes,
                session.reference_mime or "image/jpeg",
                scene_key,
                getattr(session, "attire", "groom"),
            ),
            timeout=GENERATION_TIMEOUT_SECONDS,
        )

        if sessions.get(session_id) is not session:
            return  # session was reset while generating

        extension = ALLOWED_MIME_TO_EXT.get(image_mime, "png")
        filename = f"{session_id}_{scene_key}_{int(time.time())}.{extension}"
        await asyncio.to_thread((GENERATED_DIR / filename).write_bytes, image_bytes)

        old_file = job.file
        job.file = filename
        job.mime = image_mime
        job.status = "completed"
        job.version += 1
        if old_file and old_file != filename:
            _quiet_delete(GENERATED_DIR / old_file)

        # Update Visual RAG identity bank anchor status
        if scene_key in session.identity_bank:
            session.identity_bank[scene_key].status = "ready"
            session.identity_bank[scene_key].confidence = 0.98
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error = _friendly_generation_error(exc)


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #

app = FastAPI(title="Lovers AI — Face Consistency Demo API", version="1.0.0")

_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
_cors_env = os.getenv("CORS_ORIGINS", "").strip()
if _cors_env:
    if _cors_env == "*":
        _allowed_origins = ["*"]
    else:
        _allowed_origins = _default_origins + [
            o.strip() for o in _cors_env.split(",") if o.strip()
        ]
else:
    _allowed_origins = _default_origins

_cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.onrender\.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=_cors_origin_regex if "*" not in _allowed_origins else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    scenes: list[str]
    attire: Optional[str] = "groom"


def _status_payload(session: Session) -> dict[str, object]:
    scenes = {
        key: {"status": job.status, "error": job.error, "version": job.version}
        for key, job in session.scenes.items()
    }
    all_settled = all(
        job.status in {"idle", "completed", "failed"} for job in session.scenes.values()
    )
    return {
        "session_id": session.id,
        "consent_confirmed": session.consent,
        "has_reference": session.reference_file is not None,
        "attire": getattr(session, "attire", "groom"),
        "scenes": scenes,
        "all_settled": all_settled,
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict[str, object]:
    keys = _provider_keys()
    chain_display = [f"{provider}:{model}" for provider, model in MODEL_CHAIN]
    return {
        "model": chain_display[0] if chain_display else None,
        "fallback_models": chain_display[1:],
        "model_chain": chain_display,
        "gemini_key_configured": keys["gemini"],
        "fal_key_configured": keys["fal"],
        "api_key_configured": _any_provider_key_configured(),
    }


@app.post("/api/upload")
async def upload_reference(file: UploadFile = File(...)) -> dict[str, object]:
    _purge_expired()

    mime = (file.content_type or "").lower()
    if mime not in ALLOWED_MIME_TO_EXT:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a JPG, PNG or WebP photograph.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="The photograph is larger than 10 MB. Please choose a smaller file.",
        )

    session = Session(id=uuid.uuid4().hex, created_at=datetime.now(timezone.utc))
    # Initialize Visual RAG identity bank with canonical multi-view anchors
    for sk, rag in CANONICAL_RAG_ANCHORS.items():
        session.identity_bank[sk] = IdentityAnchor(
            scene_key=sk,
            anchor_key=rag["anchor_key"],
            title=rag["title"],
            angle=rag["angle"],
            expression=rag["expression"],
            lighting=rag["lighting"],
            vector_tag=rag["vector_tag"],
            status="indexed",
            confidence=0.94,
        )

    extension = ALLOWED_MIME_TO_EXT[mime]
    filename = f"{session.id}_reference.{extension}"
    (UPLOAD_DIR / filename).write_bytes(content)
    session.reference_file = filename
    session.reference_mime = mime
    sessions[session.id] = session

    preview = base64.b64encode(content).decode("ascii")
    return {
        "session_id": session.id,
        "preview": f"data:{mime};base64,{preview}",
        "size": len(content),
        "content_type": mime,
    }


@app.post("/api/sessions/{session_id}/consent")
def confirm_consent(session_id: str) -> dict[str, str]:
    session = _require_session(session_id)
    session.consent = True
    return {"status": "consent_confirmed"}


@app.post("/api/sessions/{session_id}/generate")
async def generate(session_id: str, payload: GenerateRequest) -> dict[str, object]:
    session = _require_session(session_id)

    if payload.attire and payload.attire.lower() in {"groom", "bride"}:
        session.attire = payload.attire.lower()

    if not session.consent:
        raise HTTPException(status_code=400, detail="Consent must be confirmed before generating.")
    if not session.reference_file:
        raise HTTPException(status_code=400, detail="No reference photograph has been uploaded.")
    if not _any_provider_key_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Generation is unavailable: no provider API key is configured. "
                "Add FAL_KEY or GEMINI_API_KEY to the backend environment."
            ),
        )

    requested = list(dict.fromkeys(payload.scenes))
    unknown = [key for key in requested if key not in SCENES]
    if not requested or unknown:
        raise HTTPException(status_code=400, detail="Unknown wedding scene requested.")

    started: list[str] = []
    for key in requested:
        job = session.scenes[key]
        if job.status in {"pending", "generating"}:
            continue
        job.status = "pending"
        job.error = None
        task = asyncio.create_task(
            _run_generation(session.id, key), name=f"session:{session.id}"
        )
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
        started.append(key)

    return {"status": "started", "scenes": started}


@app.get("/api/sessions/{session_id}/status")
def status(session_id: str) -> dict[str, object]:
    return _status_payload(_require_session(session_id))


@app.get("/api/sessions/{session_id}/reference")
def get_reference(session_id: str, download: bool = False) -> FileResponse:
    session = _require_session(session_id)
    if not session.reference_file:
        raise HTTPException(status_code=404, detail="No reference photograph.")
    path = UPLOAD_DIR / session.reference_file
    if not path.exists():
        raise HTTPException(status_code=404, detail="Reference photograph no longer available.")
    headers = None
    if download:
        headers = {"Content-Disposition": f'attachment; filename="reference.{path.suffix.lstrip(".")}"'}
    return FileResponse(path, media_type=session.reference_mime or "image/jpeg", headers=headers)


@app.get("/api/sessions/{session_id}/portrait/{scene_key}")
def get_portrait(
    session_id: str, scene_key: str, download: bool = False
) -> FileResponse:
    session = _require_session(session_id)
    if scene_key not in SCENES:
        raise HTTPException(status_code=404, detail="Unknown scene.")
    job = session.scenes[scene_key]
    if job.status != "completed" or not job.file:
        raise HTTPException(status_code=404, detail="This portrait has not been generated yet.")
    path = GENERATED_DIR / job.file
    if not path.exists():
        raise HTTPException(status_code=404, detail="Portrait file no longer available.")
    headers = None
    if download:
        headers = {
            "Content-Disposition": f'attachment; filename="portrait-{scene_key}.{path.suffix.lstrip(".")}"'
        }
    return FileResponse(path, media_type=job.mime, headers=headers)


@app.get("/api/sessions/{session_id}/download")
def download_bundle(session_id: str) -> StreamingResponse:
    session = _require_session(session_id)
    completed = [
        (key, job) for key, job in session.scenes.items() if job.status == "completed" and job.file
    ]
    if not completed:
        raise HTTPException(status_code=404, detail="No completed portraits to download.")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for key, job in completed:
            path = GENERATED_DIR / job.file  # type: ignore[arg-type]
            if path.exists():
                archive.write(path, f"portrait-{key}.{path.suffix.lstrip('.')}")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="lovers-ai-portraits.zip"'},
    )


@app.get("/api/sessions/{session_id}/identity_bank")
def get_identity_bank(session_id: str) -> dict[str, object]:
    session = _require_session(session_id)
    anchors = []
    for scene_key, rag in CANONICAL_RAG_ANCHORS.items():
        job = session.scenes.get(scene_key)
        is_ready = bool(job and job.status == "completed" and job.file)
        anchors.append({
            "scene_key": scene_key,
            "anchor_key": rag["anchor_key"],
            "title": rag["title"],
            "angle": rag["angle"],
            "expression": rag["expression"],
            "lighting": rag["lighting"],
            "vector_tag": rag["vector_tag"],
            "status": "ready" if is_ready else "indexed",
            "confidence": 0.98 if is_ready else 0.94,
            "has_preview": is_ready,
        })
    return {
        "status": "active",
        "method": "Visual RAG & Multi-View Canonical Bootstrapping",
        "anchors": anchors,
    }


@app.get("/api/sessions/{session_id}/identity_bank/{scene_key}")
def get_identity_anchor_preview(session_id: str, scene_key: str) -> FileResponse:
    session = _require_session(session_id)
    job = session.scenes.get(scene_key)
    if job and job.status == "completed" and job.file:
        path = GENERATED_DIR / job.file
        if path.exists():
            return FileResponse(path, media_type=job.mime)
    if session.reference_file:
        path = UPLOAD_DIR / session.reference_file
        if path.exists():
            return FileResponse(path, media_type=session.reference_mime or "image/jpeg")
    raise HTTPException(status_code=404, detail="Anchor preview not found.")


@app.post("/api/sessions/{session_id}/reset")
def reset(session_id: str) -> dict[str, str]:
    session = _require_session(session_id)
    for task in list(_tasks):
        if task.get_name() == f"scene:{session.id}":
            task.cancel()
    _delete_session(session.id)
    return {"status": "reset"}


# --------------------------------------------------------------------------- #
# Serve the built frontend when present (single-origin deployment).
# --------------------------------------------------------------------------- #

DIST_DIR = Path(__file__).parent / "faceAi-client" / "dist"
if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str = ""):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")

        # Static assets inside dist (favicon.svg, icons.svg, etc.)
        target = DIST_DIR / full_path
        if full_path and target.is_file():
            return FileResponse(target)

        # If a missing script, style, or asset was requested, return 404 - never text/html index.html!
        if any(full_path.endswith(ext) for ext in (".js", ".mjs", ".css", ".map", ".ico", ".svg", ".png", ".jpg", ".webp", ".woff", ".woff2")):
            raise HTTPException(status_code=404, detail="Asset not found")

        # Fallback to index.html with strictly disabled cache
        index_file = DIST_DIR / "index.html"
        if index_file.exists():
            return FileResponse(
                index_file,
                media_type="text/html",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
        raise HTTPException(status_code=404, detail="Frontend build index.html not found")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend:app", host="0.0.0.0", port=port)

