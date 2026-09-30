
from app.models.schemas import (
    ComicPanel,
    OutlineResponse,
    StoryResponse,
)


def build_comic_layout(
    outline: OutlineResponse,
    story: StoryResponse,
    image_urls: list[str],
) -> list[ComicPanel]:

    story_by_number = {
        item.panel_number: item
        for item in story.panels
    }

    layout = []

    for index, panel in enumerate(
        outline.panels
    ):

        story_panel = story_by_number.get(
            panel.panel_number
        )

        if story_panel is None:

            raise ValueError(
                "Missing story content for "
                f"panel {panel.panel_number}."
            )

        if index >= len(image_urls):

            raise ValueError(
                "Missing generated image "
                "for a panel."
            )

        layout.append(
            ComicPanel(
                panel_number=panel.panel_number,
                title=panel.title,
                scene_description=(
                    panel.scene_description
                ),
                image_prompt=panel.image_prompt,
                image_url=image_urls[index],
                caption=story_panel.caption,
                narration=story_panel.narration,
                dialogue=story_panel.dialogue,
            )
        )

    return layout