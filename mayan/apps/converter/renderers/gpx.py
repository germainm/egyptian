"""
Page of a GPS track (GPX file): map of its tracks, routes and waypoints over
map tiles, with its name, date, distance, duration and elevation gain.

The tiles come from the tile server of the setting (OpenStreetMap by default,
or the map of the Itinéraires app). Only the zoom level and the tile numbers
of the area of the track are sent to it. Without tile server, or when it does
not answer, the track is drawn on a plain background.
"""
from datetime import datetime, timezone
import hashlib
import html
import io
import logging
import math
import re
import time

from PIL import Image, ImageDraw

from . import (
    PAGE_INK, PAGE_INK_MUTED, PAGE_MARGIN, PAGE_RULE, clean_text,
    draw_lines, format_duration_words, get_font, new_page, wrap_text
)

logger = logging.getLogger(name=__name__)

GPX_MAXIMUM_SIZE = 64 * 1024 * 1024

PAGE_WIDTH = 1600
PAGE_HEIGHT = 1200
MAP_TOP = 230
MAP_PADDING = 50
TILE_SIZE = 256
TILE_CACHE_TIME = 7 * 24 * 3600
TILE_MAXIMUM_SIZE = 2 * 1024 * 1024
TILE_TIMEOUT = 10
TILES_TIME_BUDGET = 40
TILES_FAILURES_MAXIMUM = 4
MAP_BACKGROUND = (238, 240, 244)
TRACK_COLOR = (214, 33, 66, 255)
ROUTE_COLOR = (29, 63, 168, 255)
START_COLOR = (31, 122, 77, 255)
END_COLOR = (179, 38, 30, 255)
WAYPOINT_LABELS_MAXIMUM = 30
EARTH_RADIUS = 6371008.8
MERCATOR_LATITUDE_MAXIMUM = 85.05112878


def _local_name(tag):
    return tag.rsplit('}', 1)[-1] if isinstance(tag, str) else ''


def _child_text(element, name):
    for child in element:
        if _local_name(child.tag) == name:
            return (child.text or '').strip()
    return ''


def _parse_time(text):
    if not text:
        return None
    try:
        value = datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def _parse_point(element):
    try:
        latitude = float(element.get('lat'))
        longitude = float(element.get('lon'))
    except (TypeError, ValueError):
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None
    elevation = _child_text(element, 'ele')
    try:
        elevation = float(elevation) if elevation else None
    except ValueError:
        elevation = None
    return {
        'latitude': latitude, 'longitude': longitude, 'elevation': elevation,
        'time': _parse_time(_child_text(element, 'time')),
        'name': _child_text(element, 'name'),
    }


def parse_gpx(data):
    """Tracks (lists of segments), routes and waypoints of the GPX data."""
    if len(data) > GPX_MAXIMUM_SIZE:
        raise ValueError(
            'GPX file too large ({} MB).'.format(len(data) // 1024 // 1024)
        )
    try:
        from defusedxml import ElementTree
    except ImportError:
        # The expat parser of Python does not load external entities and
        # limits entity expansion.
        from xml.etree import ElementTree

    root = ElementTree.fromstring(data)
    result = {'name': '', 'tracks': [], 'routes': [], 'waypoints': []}
    for element in root:
        name = _local_name(element.tag)
        if name == 'metadata':
            result['name'] = result['name'] or _child_text(element, 'name')
        elif name == 'trk':
            segments = []
            for segment in element:
                if _local_name(segment.tag) != 'trkseg':
                    continue
                points = [
                    point for point in (
                        _parse_point(child) for child in segment
                        if _local_name(child.tag) == 'trkpt'
                    ) if point
                ]
                if points:
                    segments.append(points)
            if segments:
                result['tracks'].append(
                    {'name': _child_text(element, 'name'), 'segments': segments}
                )
        elif name == 'rte':
            points = [
                point for point in (
                    _parse_point(child) for child in element
                    if _local_name(child.tag) == 'rtept'
                ) if point
            ]
            if points:
                result['routes'].append(
                    {'name': _child_text(element, 'name'), 'points': points}
                )
        elif name == 'wpt':
            point = _parse_point(element)
            if point:
                result['waypoints'].append(point)
    return result


def _distance(point_a, point_b):
    latitude_a = math.radians(point_a['latitude'])
    latitude_b = math.radians(point_b['latitude'])
    delta_latitude = latitude_b - latitude_a
    delta_longitude = math.radians(point_b['longitude'] - point_a['longitude'])
    a = (
        math.sin(delta_latitude / 2) ** 2 + math.cos(latitude_a) *
        math.cos(latitude_b) * math.sin(delta_longitude / 2) ** 2
    )
    return 2 * EARTH_RADIUS * math.asin(min(1, math.sqrt(a)))


def get_summary(gpx):
    lines = []
    for track in gpx['tracks']:
        lines.extend(track['segments'])
    for route in gpx['routes']:
        lines.append(route['points'])
    distance = sum(
        _distance(line[index], line[index + 1])
        for line in lines for index in range(len(line) - 1)
    )
    points = [point for line in lines for point in line]
    times = [point['time'] for point in points if point['time']]
    elevations = [
        point['elevation'] for point in points if point['elevation'] is not None
    ]
    gain = sum(
        max(0, elevations[index + 1] - elevations[index])
        for index in range(len(elevations) - 1)
    )
    name = gpx['name'] or next(
        (
            item['name'] for item in gpx['tracks'] + gpx['routes']
            if item['name']
        ), ''
    )
    return {
        'name': name, 'distance': distance, 'points': len(points),
        'start': min(times) if times else None,
        'end': max(times) if times else None,
        'elevation_gain': gain if elevations else None,
        'elevation_minimum': min(elevations) if elevations else None,
        'elevation_maximum': max(elevations) if elevations else None,
    }


def _project(latitude, longitude, zoom):
    """Web Mercator pixel coordinates of a point, at the zoom level."""
    latitude = max(
        -MERCATOR_LATITUDE_MAXIMUM, min(MERCATOR_LATITUDE_MAXIMUM, latitude)
    )
    scale = TILE_SIZE * 2 ** zoom
    x = (longitude + 180) / 360 * scale
    sin_latitude = math.sin(math.radians(latitude))
    y = (
        0.5 - math.log((1 + sin_latitude) / (1 - sin_latitude)) / (4 * math.pi)
    ) * scale
    return x, y


def _choose_zoom(points, width, height, maximum_zoom):
    if len({(point['latitude'], point['longitude']) for point in points}) < 2:
        return min(maximum_zoom, 15)
    for zoom in range(maximum_zoom, -1, -1):
        projected = [
            _project(point['latitude'], point['longitude'], zoom)
            for point in points
        ]
        xs = [x for x, _ in projected]
        ys = [y for _, y in projected]
        if (
            max(xs) - min(xs) <= width - 2 * MAP_PADDING and
            max(ys) - min(ys) <= height - 2 * MAP_PADDING
        ):
            return zoom
    return 0


class TileFetcher:
    def __init__(self, url, user_agent):
        import requests

        self.url = url
        self.session = requests.Session()
        self.session.headers['User-Agent'] = user_agent
        self.failures = 0
        self.deadline = time.monotonic() + TILES_TIME_BUDGET
        self.count = 0

    def get(self, zoom, x, y):
        if self.failures >= TILES_FAILURES_MAXIMUM or time.monotonic() > self.deadline:
            return None
        try:
            url = self.url.format(
                z=zoom, x=x, y=y, s='abc'[(x + y) % 3], r=''
            )
        except (IndexError, KeyError, ValueError) as exception:
            # A placeholder that Leaflet options would fill ({apikey}).
            logger.warning(
                'Map tile address not usable: %s; %s', self.url, exception
            )
            self.failures = TILES_FAILURES_MAXIMUM
            return None
        cache_key = 'converter_map_tile_{}'.format(
            hashlib.sha256(url.encode()).hexdigest()
        )
        data = None
        try:
            from django.core.cache import cache
            data = cache.get(cache_key)
        except Exception:
            cache = None

        if data is None:
            try:
                with self.session.get(
                    url, timeout=TILE_TIMEOUT, stream=True,
                    allow_redirects=False
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    if response.status_code != 200 or not content_type.startswith('image/'):
                        raise ValueError(
                            'HTTP {} {}'.format(response.status_code, content_type)
                        )
                    data = response.raw.read(
                        TILE_MAXIMUM_SIZE + 1, decode_content=True
                    )
                if len(data) > TILE_MAXIMUM_SIZE:
                    raise ValueError('tile too large')
            except Exception as exception:
                self.failures += 1
                logger.warning('Map tile not loaded: %s; %s', url, exception)
                return None
            self.count += 1
            if cache:
                try:
                    cache.set(cache_key, data, TILE_CACHE_TIME)
                except Exception:
                    pass
        try:
            tile = Image.open(fp=io.BytesIO(data))
            tile.load()
            return tile.convert(mode='RGB')
        except Exception as exception:
            logger.warning('Map tile not readable: %s; %s', url, exception)
            return None


def _draw_basemap(width, height, origin_x, origin_y, zoom, fetcher):
    canvas = Image.new(mode='RGB', size=(width, height), color=MAP_BACKGROUND)
    if not fetcher:
        return canvas, False
    tiles_loaded = 0
    tile_count = 2 ** zoom
    first_x = int(origin_x // TILE_SIZE)
    first_y = int(origin_y // TILE_SIZE)
    last_x = int((origin_x + width - 1) // TILE_SIZE)
    last_y = int((origin_y + height - 1) // TILE_SIZE)
    for tile_y in range(first_y, last_y + 1):
        if not 0 <= tile_y < tile_count:
            continue
        for tile_x in range(first_x, last_x + 1):
            tile = fetcher.get(zoom=zoom, x=tile_x % tile_count, y=tile_y)
            if tile:
                canvas.paste(
                    im=tile, box=(
                        int(tile_x * TILE_SIZE - origin_x),
                        int(tile_y * TILE_SIZE - origin_y)
                    )
                )
                tiles_loaded += 1
    return canvas, bool(tiles_loaded)


def _draw_scale(draw, x, y, latitude, zoom):
    meters_per_pixel = (
        2 * math.pi * 6378137 * math.cos(math.radians(latitude)) /
        (TILE_SIZE * 2 ** zoom)
    )
    target = meters_per_pixel * 200
    magnitude = 10 ** math.floor(math.log10(target))
    length = max(
        (step * magnitude for step in (1, 2, 5) if step * magnitude <= target),
        default=magnitude
    )
    pixels = int(length / meters_per_pixel)
    label = '{:g} km'.format(length / 1000) if length >= 1000 else '{:g} m'.format(length)
    font = get_font(size=22)
    draw.rectangle(
        xy=(x - 10, y - 34, x + pixels + 14, y + 14), fill=(255, 255, 255, 210)
    )
    draw.line(xy=((x, y), (x + pixels, y)), fill=PAGE_INK + (255,), width=4)
    for tick in (x, x + pixels):
        draw.line(xy=((tick, y - 10), (tick, y)), fill=PAGE_INK + (255,), width=3)
    draw.text(xy=(x, y - 34), text=label, font=font, fill=PAGE_INK + (255,))


def render_gpx_page(data, tile_url, tile_attribution, maximum_zoom, user_agent):
    gpx = parse_gpx(data=data)
    summary = get_summary(gpx=gpx)
    image, draw = new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    content_width = PAGE_WIDTH - 2 * PAGE_MARGIN

    # Header: name and figures of the track, for the reader and the OCR.
    font_title = get_font(size=50, style='bold')
    title = summary['name'] or 'GPS track'
    y = draw_lines(
        draw=draw, xy=(PAGE_MARGIN, PAGE_MARGIN - 10),
        lines=wrap_text(
            draw=draw, text=clean_text(title), font=font_title,
            width=content_width, maximum_lines=1
        ), font=font_title, spacing=1.2
    )
    figures = []
    if summary['start']:
        figures.append(summary['start'].strftime('%Y-%m-%d %H:%M UTC'))
    if summary['distance']:
        figures.append('{:.2f} km'.format(summary['distance'] / 1000))
    if summary['start'] and summary['end'] and summary['end'] > summary['start']:
        figures.append(
            format_duration_words(
                (summary['end'] - summary['start']).total_seconds()
            )
        )
    if summary['elevation_gain'] is not None:
        figures.append(
            '+{:.0f} m ({:.0f} – {:.0f} m)'.format(
                summary['elevation_gain'], summary['elevation_minimum'],
                summary['elevation_maximum']
            )
        )
    figures.append('{} points'.format(summary['points']))
    font_figures = get_font(size=32)
    y = draw_lines(
        draw=draw, xy=(PAGE_MARGIN, y + 4),
        lines=wrap_text(
            draw=draw, text=' · '.join(figures), font=font_figures,
            width=content_width, maximum_lines=1
        ), font=font_figures, fill=PAGE_INK_MUTED
    )
    names = [point['name'] for point in gpx['waypoints'] if point['name']]
    if names:
        font_names = get_font(size=26)
        draw_lines(
            draw=draw, xy=(PAGE_MARGIN, y + 4),
            lines=wrap_text(
                draw=draw, text='Waypoints: ' + ', '.join(
                    clean_text(name, maximum_length=60) for name in names
                ), font=font_names, width=content_width, maximum_lines=1
            ), font=font_names, fill=PAGE_INK_MUTED
        )

    # Map.
    map_width = content_width
    map_height = PAGE_HEIGHT - MAP_TOP - PAGE_MARGIN
    lines = [
        (segment, TRACK_COLOR) for track in gpx['tracks']
        for segment in track['segments']
    ] + [(route['points'], ROUTE_COLOR) for route in gpx['routes']]
    all_points = [point for line, _ in lines for point in line] + gpx['waypoints']
    if not all_points:
        draw.rectangle(
            xy=(PAGE_MARGIN, MAP_TOP, PAGE_MARGIN + map_width, MAP_TOP + map_height),
            outline=PAGE_RULE, width=3
        )
        draw.text(
            xy=(PAGE_MARGIN + 40, MAP_TOP + 40), text='No point in the GPX file.',
            font=get_font(size=32), fill=PAGE_INK_MUTED
        )
        del draw
        return image

    zoom = _choose_zoom(
        points=all_points, width=map_width, height=map_height,
        maximum_zoom=maximum_zoom
    )
    projected = [
        _project(point['latitude'], point['longitude'], zoom)
        for point in all_points
    ]
    center_x = (min(x for x, _ in projected) + max(x for x, _ in projected)) / 2
    center_y = (min(y for _, y in projected) + max(y for _, y in projected)) / 2
    origin_x = center_x - map_width / 2
    origin_y = center_y - map_height / 2

    fetcher = TileFetcher(url=tile_url, user_agent=user_agent) if tile_url else None
    basemap, has_tiles = _draw_basemap(
        width=map_width, height=map_height, origin_x=origin_x,
        origin_y=origin_y, zoom=zoom, fetcher=fetcher
    )

    # The lines are drawn at twice the size, then reduced: smooth edges.
    factor = 2
    overlay = Image.new(
        mode='RGBA', size=(map_width * factor, map_height * factor),
        color=(0, 0, 0, 0)
    )
    overlay_draw = ImageDraw.Draw(overlay)

    def to_pixels(point):
        x, y = _project(point['latitude'], point['longitude'], zoom)
        return ((x - origin_x) * factor, (y - origin_y) * factor)

    for line, color in lines:
        pixels = [to_pixels(point) for point in line]
        if len(pixels) > 1:
            overlay_draw.line(
                xy=pixels, fill=(255, 255, 255, 230), width=11 * factor,
                joint='curve'
            )
            overlay_draw.line(xy=pixels, fill=color, width=6 * factor, joint='curve')

    def marker(point, color, radius):
        x, y = to_pixels(point)
        radius *= factor
        overlay_draw.ellipse(
            xy=(x - radius, y - radius, x + radius, y + radius), fill=color,
            outline=(255, 255, 255, 255), width=3 * factor
        )

    for point in gpx['waypoints']:
        marker(point=point, color=ROUTE_COLOR, radius=8)
    if lines:
        marker(point=lines[0][0][0], color=START_COLOR, radius=12)
        marker(point=lines[-1][0][-1], color=END_COLOR, radius=12)

    overlay = overlay.resize(
        size=(map_width, map_height), resample=Image.Resampling.LANCZOS
    )
    basemap = basemap.convert(mode='RGBA')
    basemap.alpha_composite(overlay)
    map_draw = ImageDraw.Draw(basemap)

    font_label = get_font(size=22, style='bold')
    for point in gpx['waypoints'][:WAYPOINT_LABELS_MAXIMUM]:
        if not point['name']:
            continue
        x, y = (value / factor for value in to_pixels(point))
        label = clean_text(point['name'], maximum_length=40)
        map_draw.text(
            xy=(x + 14, y - 13), text=label, font=font_label,
            fill=PAGE_INK + (255,), stroke_width=3,
            stroke_fill=(255, 255, 255, 255)
        )

    _draw_scale(
        draw=map_draw, x=24, y=map_height - 24,
        latitude=sum(point['latitude'] for point in all_points) / len(all_points),
        zoom=zoom
    )
    note = clean_text(tile_attribution) if has_tiles else (
        'Map background unavailable' if tile_url else 'No map background'
    )
    if note:
        font_note = get_font(size=20)
        width = map_draw.textlength(note, font=font_note)
        map_draw.rectangle(
            xy=(map_width - width - 20, map_height - 34, map_width, map_height),
            fill=(255, 255, 255, 210)
        )
        map_draw.text(
            xy=(map_width - width - 10, map_height - 30), text=note,
            font=font_note, fill=PAGE_INK_MUTED + (255,)
        )

    image.paste(im=basemap.convert(mode='RGB'), box=(PAGE_MARGIN, MAP_TOP))
    draw.rectangle(
        xy=(
            PAGE_MARGIN - 1, MAP_TOP - 1, PAGE_MARGIN + map_width,
            MAP_TOP + map_height
        ), outline=PAGE_RULE, width=2
    )
    if fetcher:
        logger.debug('GPX page: %d map tiles downloaded.', fetcher.count)
    del draw
    return image


def html_to_text(value):
    """Plain text of an attribution written in HTML for Leaflet."""
    return html.unescape(re.sub(r'<[^>]+>', '', value or ''))
