import json
import random
import tweepy
import tempfile
import os.path
import flickrapi
import requests
from io import BytesIO
import logging

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

from PIL import Image, ImageFont, ImageDraw

from secret import *
from config import *

from colors import *
from utils import *

logging.basicConfig()

class Match(object):
    """A "matching" color from the source image. 
       color_obj: An instance of colormath.color_objects.LabColor suitable for color math
       num_points: The number of points in the source image represented by this color 
       freq: The frequency of that color in the source image, as a percentage"""
    
    def __init__(self, tile, color_obj, num_points, freq=None, color_name=None):
        self.tile = tile
        self.color_obj = color_obj
        self.num_points = num_points
        self.freq = freq
        self.color_name = color_name
        
    def __str__(self):
        return self.tile

    def __repr__(self):
        return self.__str__()

def _auth():
    """Authorize the service with Twitter"""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)


def post_tweet(tweet, card):
    """Post to twitter with the given tweet and card image as attachment"""
    with tempfile.TemporaryFile() as fp:
        card.save(fp, format='PNG')

        logging.info("Posting message {}".format(tweet))
        api.update_with_media('image.png', status=tweet, file=fp)


def build_color_map(tile_dir):
    color_map = {}
    for filename in os.listdir(tile_dir):
        _file = tile_dir + '/' + filename
        primary = colorz(_file, n=1)
        for m in primary:
            c = sRGBColor(*m[0], is_upscaled=True)
            lab_c = convert_color(c, LabColor)
            color_map[_file] = lab_c
    return color_map


def identify_colors(tile_dir, colors_to_match):
    matches = []
    logging.info("Building color map...")
    color_map = build_color_map(tile_dir)
    logging.info("Comparing {} color map values...".format(len(color_map)))
    for c2 in colors_to_match:
        color = c2[0]
        num_points = c2[1]
        best_match = None
        best_match_value = 1000.0
        for c1 in color_map:
            delta_e = delta_e_cie2000(color_map[c1], color)
            if delta_e < best_match_value:
                best_match_value = delta_e
                best_match = c1
        match = Match(tile=best_match, color_obj=color_map[best_match], num_points=num_points, freq=None)
        matches.append(match)
        del color_map[best_match]
        
    return matches


def allocate_colors(matches):
    """For the array of matching colors, build a new array that represents their relative allocations.
    As a side effect, modifies `matches` to add the percentages to each color.
    """
    # Allocate the colors by percentage to individual tiles
    total_points = sum([int(m.num_points) for m in matches])

    # Derive the percentage representation in the color set, throwing out any that are too rarely
    # represented to be displayable in our 10x10 grid
    for m in matches:
        logging.info("Total points {} / num points {} for {}".format(total_points, m.num_points, m.tile))
        
        alloc = int(m.num_points / total_points * 100)
        m.freq = alloc 
            
    for m in matches[:]:
        if m.freq == 0:
            matches.remove(m)

    # Sometimes the sums don't total 100 because we dropped out low representation items, so add those back
    sum_counts = sum(x.freq for x in matches)
    remainder = 100 - sum_counts
    matches.sort(key = lambda x: x.freq)
    matches.reverse()
    matches[-1].freq += remainder
    return matches


def generate_tiles(matches):
    # Now build a weighted list of tiles
    tiles = []
    for m in matches:
        for _ in range(0, m.freq):
            tiles.append(m.tile)

    logging.info("Created an array of {} tiles".format(len(tiles)))
    
    return tiles


def build_grid(matches, tiles):
    """Build a 10x10 grid of the resulting colors; returns a canvas object with the images laid out"""

    # Set up the grid
    grid_img = Image.new('RGB', (GRID_WIDTH * TILE_WIDTH, GRID_HEIGHT * TILE_WIDTH), color=(255,255,255))
    for row in range(0, GRID_WIDTH):
        for col in range(0, GRID_HEIGHT):
            tile = tiles[-1]
            im = Image.open(tile)
            im = rotate_randomly(im)
            grid_img.paste(im, box=(row * TILE_WIDTH, col * TILE_WIDTH))
            if len(tiles) > 1:
                tiles.pop()
    grid_img = rotate_randomly(grid_img)
    return grid_img


def draw_card(grid_img, matches, keyword_text):
    """Draw the main card, paste on the grid, and set up the text"""
    card = Image.new('RGB', (CARD_WIDTH, CARD_HEIGHT), color=(255,255,255))

    # Draw the background, randomly flipping it for recto/verso variety
    bg = Image.open('images/bg.jpg')
    bg = bg.rotate(random.choice([0, 180]))
    card.paste(bg)

    # Place the grid on the canvas
    card.paste(grid_img, box=(0,0))

    # Draw the header
    draw = ImageDraw.Draw(card)    
    header_font = ImageFont.truetype('fonts/' + FONT, size=HEADER_FONT_SIZE)
    header_height = draw_text_center(draw, text=keyword_text.upper(),
                                     width=CARD_WIDTH - CARD_MARGIN,
                                     ypos=CARD_MARGIN + (GRID_HEIGHT * TILE_WIDTH),
                                     fill=FONT_COLOR,
                                     font=header_font)

    font = ImageFont.truetype('fonts/' + FONT, size=FONT_SIZE)

    # Sort them in descending order by population    
    matches.sort(key = lambda x: x.freq)
    matches.reverse()

    height = draw.textsize("Aygj", font=font)[1]  # Text with cap-height + descenders
    for i, match in enumerate(matches):
        label = match.color_name
        number = str(match.freq)
        width, _ = draw.textsize(label, font=font)
        logging.info("Drawing label {}:{} with height {}".format(label, number, height))
        
        x = TABLE_MARGIN
        y = (CARD_MARGIN * 2) + (GRID_HEIGHT * TILE_WIDTH) + header_height + (i * height) 
        draw.text((x, y), label, fill=FONT_COLOR, font=font)

        # Now draw the related number, aligned right this time
        number_width = draw.textsize(number, font=font)[0]
        x = CARD_WIDTH - TABLE_MARGIN - number_width 
        draw.text((x, y), str(number), fill=FONT_COLOR, font=font)

        # Now draw the ellipses starting from `width + margin` and ending at `card_width - width`
        char_padding = int(width / len(label))
        pos = TABLE_MARGIN + width + char_padding
        end_pos =  CARD_WIDTH - TABLE_MARGIN - number_width - (char_padding * 2)
        ellipse = " . "
        ellipse_width = draw.textsize(ellipse, font=font)[0]
        while pos < end_pos:
            pos = int(10 * round(float(pos) / 10))  # Round to the nearest nth pixel
            draw.text((pos, y), ellipse, fill=FONT_COLOR, font=font)
            pos += ellipse_width
            
    # For some reason she makes these sum to 100
    number = '__'
    number_width = draw.textsize(number, font=font)[0]
    x = CARD_WIDTH - (TABLE_MARGIN) - number_width
    y += height
    y = y - (height / 2)
    draw.text((x, y), number, fill=FONT_COLOR, font=font)    

    number = '100'
    number_width = draw.textsize(number, font=font)[0]
    y += height 
    draw.text((x, y), number, fill=FONT_COLOR, font=font)        
    return card


def generate_color_name_list(matches, colorfile=COLORFILE):

    # Sort them by frequency (highest to lowest) so we allocate the "best" names to the
    # most-represented colors
    matches.sort(key = lambda x: x.freq)
    matches.reverse()
    
    color_names = named_colorset(colorfile) 
    for match in matches:
        color = match.color_obj
        best_match = None
        best_match_value = 1000.0
        for c2 in color_names:
            delta_e = delta_e_cie2000(c2['obj'], color)
            if delta_e < best_match_value:
                best_match_value = delta_e
                best_match = c2
        logging.info("Think {} is the best name for {}".format(best_match['color'], match.tile))
        match.color_name = best_match['color'] 
        color_names.remove(best_match)        
        
    return matches

def get_flickr_image_by_keyword(keyword):
    """Given a keyword, search Flickr for it and return a slightly-random result as a file descriptor"""
    logging.info("Getting {} from Flickr".format(keyword))
    flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, format='etree')
    result = flickr.photos.search(per_page=100,
                                  text=keyword,
                                  tag_mode='all',
                                  content_type=1,
                                  tags=keyword,
                                  extras='url_o,url_l',
                                  sort='relevance')
    # Randomize the result set
    img_url = None
    photos = [p for p in result[0]]
    while img_url is None and len(photos) > 0:
        photo = photos[0]
        img_url = photo.get('url_o') or photo.get('url_l')
        photos.pop()
    if not img_url:
        raise Exception("Couldn't find a Flickr result for %s" % keyword)
    logging.info(img_url)
    img_file = requests.get(img_url, stream=True)
    return BytesIO(img_file.content)

if __name__ == '__main__':
    api = _auth()

    #input_image = sys.argv[1]
    keyword = random.choice(json.load(open('objects.json'))['objects'])
    input_image = get_flickr_image_by_keyword(keyword)
    
    colors = colorz(input_image, n=NUM_COLORS_TO_MATCH)
    colors_lab = [(convert_color(sRGBColor(*c[0], is_upscaled=True), LabColor), c[1]) for c in colors]

    matches = identify_colors('tiles', colors_lab)
    logging.info("Found {} matches".format(len(matches)))
    
    matches = allocate_colors(matches)
    
    tiles = generate_tiles(matches)
    
    grid = build_grid(matches, tiles)
    matches = generate_color_name_list(matches)
    keyword_text = "Color analysis from " + keyword
    card = draw_card(grid, matches, keyword_text)
    
    if card:
        post_tweet(keyword_text, card)
