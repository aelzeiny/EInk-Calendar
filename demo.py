import datetime as dt
from typing import Tuple
from image_utils_server import PillowBackend, Image, Box, TextSegment, FontHelper
from image_utils_client import deserialize
from PIL import ImageDraw

###############################################
#                    SERVER
###############################################

WIDTH = 800
HEIGHT = 480

PADDING = 8  # See 8-point grid system: https://uxplanet.org/everything-you-should-know-about-8-point-grid-system-in-ux-design-b69cb945b18d

PRIMARY_RED = '#e53031'
SECONDARY_RED = '#ef9798'
PRIMARY_BLACK = 'black'
PRIMARY_BLANK = 'white'

FONT_PATH = './fonts/NotoSans-Regular.ttf'


def server() -> Tuple[bytes, bytes]:
    font_helper = FontHelper(FONT_PATH)
    image = Image.new('RGB', (WIDTH, HEIGHT), PRIMARY_BLANK)
    # seperate black & red layers
    layer = PillowBackend(image, mode=image.mode, font_helper=font_helper)
    red_layer = PillowBackend(image, mode=image.mode, font_helper=font_helper)

    # full card
    full = Box(0, 0, WIDTH, HEIGHT)
    layer.outline_box(full)

    # title box + summary
    event_summary = [
        TextSegment("Vamsi/Liz Lass 1:1 in "),
        TextSegment("40 ", color=PRIMARY_RED, layer=red_layer),
        TextSegment("minutes", underline=True)
    ]
    event_summary_bb, _ = layer.text_series(
        WIDTH / 2, HEIGHT / 2, event_summary, size=25, anchor='ms'
    )

    # Next events
    next_event_summary = [
        TextSegment("Lunch in "),
        TextSegment("1 ", color=SECONDARY_RED, layer=red_layer),
        TextSegment("hour", underline=True),
        TextSegment(" 20 ", color=SECONDARY_RED, layer=red_layer),
        TextSegment("minutes", underline=True)
    ]
    next_event_bb, xs = layer.text_series(
        WIDTH / 2, event_summary_bb.bottom + PADDING * 4, next_event_summary, 
        size=20, anchor='ma', color='gray'
    )
    next_event_summary = [
        TextSegment("Trello Townhall in "),
        TextSegment("2 ", color=SECONDARY_RED, layer=red_layer),
        TextSegment("hours", underline=True),
        TextSegment(" 30 ", color=SECONDARY_RED, layer=red_layer),
        TextSegment("minutes", underline=True)
    ]
    next_event_bb, _ = layer.text_series(
        WIDTH / 2, next_event_bb.bottom + PADDING, next_event_summary, 
        size=20, anchor='ma', color='gray'
    )
    next_bottom = layer.template_text(
    WIDTH / 2, next_event_bb.bottom + PADDING * 4, '+4 more events', 
    size=16, anchor='ma', color=(170, 170, 170)
    )

    # previous event
    prev_event_summary = [
        TextSegment("Daily Standup started "),
        TextSegment("5 ", color=SECONDARY_RED, layer=red_layer),
        TextSegment("minutes", underline=True),
        TextSegment(" ago")
    ]
    prev_event_bb, _ = layer.text_series(
        WIDTH / 2, event_summary_bb.y - PADDING * 4, prev_event_summary, 
        size=20, anchor='md', color='gray'
    )

    # Bar chart
    bar_width = int(WIDTH * .65) # 520 is divisible by 8 (grid)
    bar = Box(WIDTH / 2 - bar_width // 2, next_bottom.bottom + PADDING * 5, bar_width, PADDING / 2)
    layer.fill_box(bar, color='lightgray')

    # Bar graph
    cal_spans = [(50, 100), (300, 30)] # hard-coded for now; dynamic later
    for span_offset, span_width in cal_spans:
        cal_box = Box(bar.x + span_offset, bar.y, span_width, bar.height)
        layer.fill_box(cal_box, color=PRIMARY_BLANK)
        red_layer.fill_box(cal_box, color=SECONDARY_RED)
        red_layer.outline_box(cal_box, color=PRIMARY_BLANK)

    # calendar/weather Header
    today = dt.date.today()
    NUM_DAYS = 14
    WEEKDAY_TOTAL_WIDTH = 560 # magic number divisible by 14 (weekdays) & 8 (grid)
    WEEKDAY_PADDING = WEEKDAY_TOTAL_WIDTH / NUM_DAYS
    WEEKDAY_TOP_PADDING = PADDING * 8

    weekday_offset = WIDTH / 2 - WEEKDAY_TOTAL_WIDTH / 2
    # headers
    layer.template_text(weekday_offset, WEEKDAY_TOP_PADDING, today.strftime("%B %Y"), size=16, anchor='ld')
    layer.template_text(WIDTH / 2 + WEEKDAY_TOTAL_WIDTH / 2 - PADDING, WEEKDAY_TOP_PADDING, "Mostly Sunny • 27° / 13°", size=16, anchor='rd', color='gray')
    # calendar
    for i in range(NUM_DAYS):
        curr = today + dt.timedelta(days=i)
        weekday = curr.strftime("%a")[:2]
        color = 'black' if i == 0 else 'gray'

        if i == 0:
            red_layer.outline_box(Box(weekday_offset, WEEKDAY_TOP_PADDING, WEEKDAY_TOTAL_WIDTH / NUM_DAYS, WEEKDAY_PADDING), color=PRIMARY_RED)
        layer.template_text(weekday_offset + WEEKDAY_PADDING / 2, WEEKDAY_TOP_PADDING, weekday, size=12, anchor='ma', color=color)
        layer.template_text(weekday_offset + WEEKDAY_PADDING / 2, WEEKDAY_TOP_PADDING + PADDING * 2, str(curr.day).zfill(2), size=16, anchor='ma', color=color)
        weekday_offset += WEEKDAY_TOTAL_WIDTH / NUM_DAYS
    return layer.serialize(), red_layer.serialize()

###############################################
#                    CLIENT
###############################################
def client(black_bytes: bytes, red_bytes: bytes) -> Image:
    client_image = Image.new('RGB', (WIDTH, HEIGHT), PRIMARY_BLANK)
    client_black_layer = ImageDraw.Draw(client_image)
    client_red_layer = ImageDraw.Draw(client_image)
    deserialize(client_black_layer, FONT_PATH, black_bytes)
    deserialize(client_red_layer, FONT_PATH, red_bytes)
    return client_image
    

if __name__ == '__main__':
    black_bytes, red_bytes = server()
    print(f'Bytes are sent over the network. Serialization Length:', len(black_bytes) + len(red_bytes), 'bytes')
    print('Client received bytes.')
    image = client(black_bytes, red_bytes)
    image.save('demo.png', format='png')
    print('Client saved `demo.png`')


