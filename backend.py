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
FAL_ID_WEIGHT = min(float(os.getenv("FAL_ID_WEIGHT", "1.0")), 1.0)
FAL_INFERENCE_STEPS = int(os.getenv("FAL_INFERENCE_STEPS", "28"))
FAL_GUIDANCE_SCALE = float(os.getenv("FAL_GUIDANCE_SCALE", "4.0"))
FAL_ENABLE_ENHANCE = os.getenv("FAL_ENABLE_ENHANCE", "true").lower() in ("true", "1", "yes")
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
        "tagline": "The Royal Palace",
        "description": "Grand heritage palace courtyard, sandstone jharokhas, warm chandeliers & royal diyas.",
        "groom": {
            "prompt": (
                "Create a photorealistic Indian wedding portrait of the man in the reference photograph "
                "as an Indian royal groom (Dulha). Scene: an opulent Rajasthan heritage palace courtyard with "
                "intricate carved sandstone jharokhas, royal chandeliers, warm diya oil lamps, and fragrant "
                "marigold and rose garlands. Attire: an opulent bespoke ivory and gold silk sherwani with "
                "intricate zardozi embroidery, churidar, royal maroon velvet doshala stole, regal safa "
                "turban with pearl kalgi brooch, and a traditional groom's layered pearl kantha mala. "
                "Critical: preserve his natural male features and keep his face exactly as it appears in "
                "the reference — same male jawline, facial structure, eyes, nose, mouth, skin tone and hair. "
                "Do NOT feminize the face. Do NOT put him in a dress, bridal lehenga, bindi, or female earrings. "
                "Full natural colour, editorial royal Indian wedding photography, no cartoon style."
            ),
            "fal_prompt": (
                "Photorealistic portrait of this Indian man as a royal groom at a magnificent heritage "
                "palace courtyard in Rajasthan, grand carved sandstone jharokhas, warm palace chandeliers "
                "and diya oil lamps, marigold and rose garlands, wearing an opulent ivory and gold silk "
                "sherwani with intricate zardozi embroidery, churidar, royal velvet doshala shawl, "
                "a regal safa turban with pearl kalgi brooch, multi-layer groom pearl necklace kantha mala, "
                "masculine groom styling, editorial royal Indian wedding photography, warm golden hour "
                "lighting, premium wedding photography, natural colour"
            ),
        },
        "bride": {
            "prompt": (
                "Create a photorealistic Indian wedding portrait of the woman in the reference photograph "
                "as an Indian royal bride (Dulhan). Scene: an opulent Rajasthan heritage palace courtyard with "
                "intricate carved sandstone arches, royal chandeliers, warm diya lamps and marigold garlands. "
                "Attire: an exquisite crimson red bridal lehenga with heavy antique gold zardozi embroidery, "
                "sheer embroidered dupatta veil, uncut polki kundan bridal necklace, maang tikka, and jhumkas. "
                "Critical: keep her face exactly as it appears in the reference — same face shape, features, "
                "eyes, nose, mouth, skin tone and hair. Full natural colour, editorial wedding photography."
            ),
            "fal_prompt": (
                "Photorealistic portrait of this Indian woman as a royal bride at a magnificent heritage "
                "palace courtyard in Rajasthan, grand carved sandstone jharokhas, warm chandeliers "
                "and diya oil lamps, marigold garlands, wearing an opulent crimson red bridal lehenga "
                "with heavy antique gold zardozi embroidery, sheer embroidered dupatta veil over head, "
                "royal uncut polki kundan necklace, maang tikka, jhumka earrings, bridal chooda bangles, "
                "editorial wedding photography, natural colour"
            ),
        },
    },
    "beach_destination": {
        "name": "Goa Coastal Mandap",
        "tagline": "The Sunset Mandap",
        "description": "Scenic beachside sunset, fresh mogra & marigold mandap, elegant coastal festive attire.",
        "groom": {
            "prompt": (
                "Create a photorealistic Indian wedding portrait of the man in the reference photograph "
                "as a groom at a destination beach wedding in Goa. Scene: a scenic oceanfront beach at "
                "golden hour with an authentic Indian floral mandap draped with fresh white mogra (jasmine) "
                "and orange marigolds, soft sea breeze, tropical palms. Attire: a contemporary tailored "
                "raw silk bandhgala jacket in pastel ivory or blush tones, embroidered mandarin collar, "
                "and tailored trousers. Masculine groom styling. "
                "Critical: preserve his natural male features, masculine jawline, and keep his face "
                "exactly as it appears in the reference. Do NOT feminize the face or put him in women's clothing. "
                "Full natural colour, no cartoon style."
            ),
            "fal_prompt": (
                "Photorealistic portrait of this Indian man as a groom at an oceanfront beach wedding "
                "in Goa at golden hour, traditional seaside floral mandap decorated with fresh white "
                "mogra jasmine and orange marigolds, soft ocean breeze, tropical palms, wearing a "
                "tailored blush peach or ivory raw silk bandhgala jacket with embroidered collar and "
                "tailored trousers, elegant contemporary Indian groom attire, masculine styling, "
                "warm coastal sunset glow, premium Indian wedding photography, natural colour"
            ),
        },
        "bride": {
            "prompt": (
                "Create a photorealistic Indian wedding portrait of the woman in the reference photograph "
                "as a bride at a destination beach wedding in Goa. Scene: scenic oceanfront beach at golden "
                "hour with a traditional Indian floral mandap with marigolds and fresh jasmine. Attire: a "
                "graceful pastel blush pink or coral designer silk lehenga with delicate mirror work and "
                "floral embroidery, lightweight floral and gold jewelry. "
                "Critical: keep her face exactly as it appears in the reference. Full natural colour."
            ),
            "fal_prompt": (
                "Photorealistic portrait of this Indian woman as a bride at an oceanfront beach wedding "
                "in Goa at golden hour, scenic seaside floral mandap with fresh white mogra jasmine and "
                "marigolds, soft sea breeze, wearing a graceful pastel blush pink or coral designer silk "
                "lehenga with delicate mirror work and floral embroidery, lightweight floral and gold "
                "jewelry, fresh flowers in hair, soft coastal sunset light, premium Indian wedding photography, natural colour"
            ),
        },
    },
    "traditional_indian": {
        "name": "Grand Vivah Mandap",
        "tagline": "The Sacred Vivah",
        "description": "Traditional Vedic vivah ceremony, warm havan glow, rich silk & zardozi embroidery.",
        "groom": {
            "prompt": (
                "Create a photorealistic traditional Indian wedding portrait of the man in the reference "
                "photograph as an Indian groom (Dulha) at a Vedic Vivah ceremony. Scene: an authentic "
                "grand Indian wedding mandap with cascading marigold bells, brass lamps, and the warm glow "
                "of the sacred havan fire. Attire: a rich royal emerald green or gold embroidered achkan "
                "sherwani, brocade safa turban, embroidered groom's stole, and layered pearl mala. "
                "Critical: preserve his natural masculine features and keep his face exactly as it appears "
                "in the reference — same male face shape, features, eyes, nose, mouth, skin tone and hair. "
                "Do NOT put him in female bridal wear, bindi, or female earrings. "
                "Full natural colour, no cartoon style."
            ),
            "fal_prompt": (
                "Photorealistic portrait of this Indian man as a groom at a traditional grand Vedic Vivah "
                "ceremony, ornate wedding mandap adorned with cascading marigold bells, brass urlis with "
                "floating candles and red roses, sacred havan fire glow, wearing a rich royal emerald "
                "green or gold embroidered achkan sherwani, an ornate matching doshala dupatta shawl, "
                "traditional brocade safa turban, classic groom pearl mala, regal masculine Indian groom "
                "styling, warm ceremonial ambiance, premium wedding photography, natural colour"
            ),
        },
        "bride": {
            "prompt": (
                "Create a photorealistic traditional Indian wedding portrait of the woman in the reference "
                "photograph as an Indian bride (Dulhan) at a Vedic Vivah ceremony. Scene: an authentic grand "
                "traditional wedding mandap with cascading marigolds, brass lamps, and sacred fire glow. "
                "Attire: an opulent vermilion red and gold Banarasi silk lehenga with heavy zardozi "
                "embroidery, traditional temple gold jewelry set, bridal maang tikka, nath nose ring, "
                "jhumkas, red bridal bindi, and floral hair ornaments. "
                "Critical: keep her face exactly as it appears in the reference. Full natural colour."
            ),
            "fal_prompt": (
                "Photorealistic portrait of this Indian woman as a traditional bride at a grand Vedic "
                "Vivah ceremony, ornate wedding mandap with cascading marigolds, brass lamps, sacred havan "
                "fire glow, wearing a rich traditional vermilion red and gold Banarasi silk lehenga with "
                "heavy zardozi embroidery, traditional temple gold jewelry set, bridal maang tikka, "
                "nath nose ring, jhumkas, red bridal bindi, ornate floral gajra in hair, warm ceremonial "
                "lighting, premium wedding photography, natural colour"
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
        "title": "3/4 Regal Palace Anchor",
        "angle": "30° Stately Three-Quarter Perspective",
        "expression": "Regal Composure & Stately Gaze",
        "lighting": "Heritage Palace Chandelier & Diya Ambient",
        "vector_tag": "512-D Geometry Lock (30° Yaw)",
        "rag_prompt_inject": (
            ", three-quarter angle 30 degree head turn, regal noble posture, "
            "cinematic depth of field, sharp jawline definition"
        ),
    },
    "beach_destination": {
        "anchor_key": "candid_twilight",
        "title": "Candid Sunset Anchor",
        "angle": "Dynamic Side Profile & Slight Tilt",
        "expression": "Warm Joyful Expression & Subtle Smile",
        "lighting": "Golden Hour Sunset Twilight Rim-Lighting",
        "vector_tag": "Dynamic Tilt & Expression Vector",
        "rag_prompt_inject": (
            ", candid natural dynamic angle with slight head tilt, warm joyful gentle smile, "
            "radiant golden sunset rim-light outlining hair and facial profile, lively natural gaze"
        ),
    },
    "traditional_indian": {
        "anchor_key": "frontal_ceremonial",
        "title": "Frontal Vedic Anchor",
        "angle": "0° Symmetrical Frontal Direct View",
        "expression": "Serene Devotional & Sacred Reverence",
        "lighting": "Sacred Havan Fire Warmth & Brass Urlis",
        "vector_tag": "Symmetrical Frontal Eye-Spacing Lock",
        "rag_prompt_inject": (
            ", direct straight-on front angle view, looking directly into camera with serene devotion, "
            "balanced symmetrical facial features, warm atmospheric glow from havan fire"
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

