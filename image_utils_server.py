from typing import Tuple
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import pickle


@dataclass
class Box:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def offset(self, x: int, y: int):
        self.x += x
        self.y += y
        return self

    def clone(self):
        return self.__class__(self.x, self.y, self.width, self.height)


class FontHelper:
    def __init__(self, font_path: str):
        self.font_path = font_path
        self.cache: dict[int, ImageFont] = {}

    def get(self, size: int) -> ImageFont:
        if size not in self.cache:
            self.cache[size] = ImageFont.truetype(self.font_path, size)
        return self.cache[size]


@dataclass
class TextSegment:
    message: str
    color: str = None
    underline: bool = False
    layer: ImageDraw.ImageDraw = None


class PillowBackend(ImageDraw.ImageDraw):
    """Intercepts Pillow calls and stores them in memory."""
    def __init__(self, *args, font_helper: FontHelper, render=True, **kwargs):
        """If render is True, then the output is rendered to an image.
        Mostly used for dev/debugging."""
        super().__init__(*args, **kwargs)
        self.memory = []
        self.render = render
        self.font_helper = font_helper
    
    ###############################################
    #                SERIALIZATION
    ###############################################

    def rectangle(self, *args, meta=None, **kwargs):
        self.memory.append(dict(
            func='rectangle',
            args=args,
            kwargs=kwargs,
            meta=meta,
        ))
        if self.render:
            super().rectangle(*args, **kwargs)

    def text(self, *args, font, meta=None, **kwargs):
        # font is a VERY LARGE serializable field, so we shim it.
        font_data = (*font.getname(), font.size)
        self.memory.append(dict(
            func='text',
            args=args,
            kwargs={**kwargs, 'font': font_data},
            meta=meta,
        ))
        if self.render:
            super().text(*args, font=font, **kwargs)

    def serialize(self) -> bytes:
        return pickle.dumps(self.memory)

    ###############################################
    #                    UTILS
    ###############################################

    def text_bb(self, message: str, anchor: str, size=16) -> Box:
        """Gets a bounding-box of text, where (x, y) is the upper-left position."""
        font = self.font_helper.get(size)
        l, t, r, b = self.textbbox((0, 0), message, font=font, anchor=anchor)
        return Box(l, t, r-l, b-t)

    def template_text(self, x: int, y: int, message: str, size=16, color='black', anchor='la', underline=False) -> Box:
        """Templates text."""
        bounds = self.text_bb(message, size=size, anchor=anchor).offset(x, y)
        self.text((x, y), message, font=self.font_helper.get(size), fill=color, anchor=anchor)
        if underline:
            self.underline_box(bounds, color=color)
        return bounds
    
    def outline_box(self, box: Box, color='black', width=1):
        self.rectangle(
            ((box.x, box.y), (box.right, box.bottom)),
            outline=color,
            width=width
        )

    def underline_box(self, box: Box, color='black', width=1):
        underline = box.clone()
        underline.y += underline.height
        underline.height = width
        self.outline_box(underline, color=color, width=width)

    def fill_box(self, box: Box, color='black'):
        self.rectangle(
            ((box.x, box.y), (box.right, box.bottom)),
            fill=color
        )

    def text_series(self, x: int, y: int, segments: list[TextSegment], size=16, 
                    anchor='la', color='black') -> Tuple[Box, list[Box]]:
        """
        Break up a series of messages into seperate render calls on the same line.
        :returns: A global bounding-box, and then an individual bounding box
                per-message.
        """
        global_text = ''.join([s.message for s in segments])
        global_box = self.text_bb(global_text, anchor=anchor, size=size).offset(x, y)
        # correct y-axis due to discrepancies between requested coordinates and
        # actual coordinates. Super annoying.
        correction_box = self.text_bb(global_text, anchor='la', size=size)
        offset_x = global_box.x
        boxes = []
        for segment in segments:
            self.text_bb(segment.message, anchor='la', size=size).offset(x, y)
            segment_color = segment.color if segment.color is not None else color
            dy = global_box.y - correction_box.y + correction_box.height - global_box.height
            layer = segment.layer or self
            curr_box = layer.template_text(
                offset_x, dy, segment.message, 
                color=segment_color, size=size, anchor='la',
                underline=segment.underline,
            )
            boxes.append(curr_box)
            offset_x += curr_box.width
        return global_box, boxes
