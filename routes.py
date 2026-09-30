from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import HTMLResponse

from fastapi.templating import (
    Jinja2Templates,
)

from app.config import get_settings

from app.models.schemas import (
    ImageTestRequest,
    PromptRequest,
)

from app.services.exporters import (
    save_pdf,
)

from app.services.gemini_flash import (
    generate_outline,
)

from app.services.gemini_pro import (
    generate_story,
)

from app.services.image_generator import (
    generate_image,
)

from app.services.layout_builder import (
    build_comic_layout,
)


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


def _make_request(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> PromptRequest:

    try:

        return PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


def _generate_comic(
    request_data: PromptRequest,
):

    settings = get_settings()

    # Step 1
    outline = generate_outline(
        request_data,
        settings
    )

    # Step 2
    story = generate_story(
        request_data,
        outline,
        settings
    )

    # Step 3
    image_urls = []

    for panel in outline.panels:

        image_url = generate_image(
            panel.image_prompt,
            panel.panel_number,
            settings,
        )

        image_urls.append(
            image_url
        )

    # Step 4
    layout = build_comic_layout(
        outline,
        story,
        image_urls,
    )

    # Step 5
    title = (
        f"{request_data.character_name}: "
        f"{request_data.story_prompt[:60]}"
    )

    pdf_url = save_pdf(
        title,
        layout,
        settings,
    )

    return (
        title,
        layout,
        pdf_url,
    )


@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(
    request: Request,
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "max_prompt_length":
                get_settings()
                .max_prompt_length
        },
    )


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...),
):

    request_data = _make_request(
        story_prompt,
        character_name,
        setting,
        tone,
        art_style,
    )

    try:

        title, layout, pdf_url = (
            _generate_comic(
                request_data
            )
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc),

                "form":
                    request_data.model_dump(),

                "max_prompt_length":
                    get_settings()
                    .max_prompt_length,
            },
            status_code=502,
        )

    return templates.TemplateResponse(
        request=request,
        name="comic_preview.html",
        context={
            "title": title,
            "layout": layout,
            "pdf_url": pdf_url,
        },
    )


@router.post(
    "/generate-comic/json"
)
async def generate_comic_json(
    payload: PromptRequest,
):

    try:

        title, layout, pdf_url = (
            _generate_comic(
                payload
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "title": title,

        "panels": [
            panel.model_dump()
            for panel in layout
        ],

        "pdf_url": pdf_url,
    }


@router.post(
    "/test-image"
)
async def test_image(
    payload: ImageTestRequest,
):

    try:

        image_url = generate_image(
            payload.prompt,
            panel_number=0,
            settings=get_settings(),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return {
        "image_url": image_url
    }


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
    pdf_url: str | None = None,
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_url": pdf_url
        },
    )