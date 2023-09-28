import pickle
from functools import cache
from PIL import ImageFont, Image, ImageDraw


@cache
def load_font(font_path: str, size: int) -> ImageFont:
    return ImageFont.truetype(font_path, size)


def deserialize(client_renderer: ImageDraw.ImageDraw, font_path: str, response_bytes: bytes) -> Image:
    """This is the ENTIRE deserialization func"""
    response_commands = pickle.loads(response_bytes)
    for cmd in response_commands:
        func = getattr(client_renderer, cmd['func'])
        if 'font' in cmd['kwargs']:
            _, _, fsize = cmd['kwargs']['font']
            cmd['kwargs']['font'] = load_font(font_path, fsize)
        func(*cmd['args'], **cmd['kwargs'])
