from jinja2 import Environment, FileSystemLoader

# Create a Jinja2 environment with a file system loader
env = Environment(loader=FileSystemLoader('./template'))

# Load the main template
template = env.get_template('index.j2')

# Define data (if needed)
import datetime as dt
import pytz
from view import CalendarViewModel, WeatherViewModel
from cal import CalEvent


tz = pytz.timezone('America/Los_Angeles')
nowish = dt.datetime.now(tz)

def pluralize(singular: str, val: int):
    return singular if val == 1 else singular + 's'


def calc_conversion(range_start: dt.datetime, range_end: dt.datetime, bar_width: int):
    return bar_width / (range_end - range_start).total_seconds()

def calc_left(moment: dt.datetime, range_start: dt.datetime, range_end: dt.datetime, bar_width: int):
    conversion = calc_conversion(range_start, range_end, bar_width)
    (moment - range_start).total_seconds() * conversion



mvvm = CalendarViewModel(
    timezone=tz,
    now=nowish,
    daily_events=[
        CalEvent('Daily Standup', nowish - dt.timedelta(minutes=5), nowish + dt.timedelta(minutes=25), status='CONFIRMED'),
        # CalEvent('Daily Standup', nowish - dt.timedelta(minutes=10), nowish - dt.timedelta(minutes=5), status='CONFIRMED'),
        CalEvent('Vamsi/Liz Lass 1:1', nowish + dt.timedelta(minutes=40), nowish + dt.timedelta(hours=1), status='CONFIRMED'),
        CalEvent('Lunch', nowish + dt.timedelta(hours=1, minutes=20), nowish + dt.timedelta(hours=2), status='CONFIRMED'),
        CalEvent('Trello Townhall', nowish + dt.timedelta(hours=2, minutes=30), nowish + dt.timedelta(hours=3), status='CONFIRMED'),
        
        # CalEvent('IDK', nowish + dt.timedelta(hours=4), nowish + dt.timedelta(hours=5), status='CONFIRMED'),
        # CalEvent('IDK', nowish + dt.timedelta(hours=4), nowish + dt.timedelta(hours=5), status='CONFIRMED'),
        # CalEvent('IDK', nowish + dt.timedelta(hours=4), nowish + dt.timedelta(hours=5), status='CONFIRMED'),
        # CalEvent('IDK', nowish + dt.timedelta(hours=4), nowish + dt.timedelta(hours=5), status='CONFIRMED'),
    ],
    weather=WeatherViewModel('Mostly Sunny', high=27, low=13),
)
for e in (mvvm.daily_events):
    print(e.start_dttm, e.end_dttm)
data = {
    # globals
    'dt': dt,
    'str': str,
    'int': int,
    'abs': abs,
    'enumerate': enumerate,
    'len': len,
    'min': min,
    'max': max,
    'print': print,
    # vars
    'pluralize': pluralize,
    'calc_conversion': calc_conversion,
    'vm': mvvm,
    'max_event_end': lambda: max([e.end_dttm for e in mvvm.daily_events]),
    'min_event_start': lambda: min([e.start_dttm for e in mvvm.daily_events])
}

# print('?', dt.datetime.combine(mvvm.now.date(), dt.time(9, 0), tzinfo=mvvm.timezone))
# print('?', mvvm.timezone.localize(dt.datetime.combine(mvvm.now.date(), dt.time(9, 0))))

# Render the template with the data
rendered_html = template.render(data)

# Print or use the rendered HTML as needed
# print(rendered_html)

with open('./jinja.html', 'w') as f:
    f.write(rendered_html)
