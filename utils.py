import random

def draw_word_wrap(draw, text,
                   xpos=0, ypos=0,
                   max_width=130,
                   fill=(250,0,0),
                   font=None):
    '''Draw the given ``text`` to the x and y position of the image, using
    the minimum length word-wrapping algorithm to restrict the text to
    a pixel width of ``max_width.``
    '''
    text_size_x, text_size_y = draw.textsize(text, font=font)
    remaining = max_width
    space_width, space_height = draw.textsize(' ', font=font)
    # use this list as a stack, push/popping each line
    output_text = []
    # split on whitespace...
    for word in text.split(None):
        word_width, word_height = draw.textsize(word, font=font)
        if word_width + space_width > remaining:
            output_text.append(word)
            remaining = max_width - word_width
        else:
            if not output_text:
                output_text.append(word)
            else:
                output = output_text.pop()
                output += ' %s' % word
                output_text.append(output)
            remaining = remaining - (word_width + space_width)
    for text in output_text:
        draw.text((xpos, ypos), text, font=font, fill=fill)
        ypos += text_size_y
    return ypos

def draw_text_center(draw, text, width=800, ypos=0, fill=(0, 0, 0), font=None):
    """Center text on the canvas. Returns the yoffset that it drew. If the text is too long to fit,
    cut it in half and call itself again."""
    # TODO make this recursive, right now it'll only cut the text in half once
    
    text_size_x, text_size_y = draw.textsize(text, font=font)
    if text_size_x > width:
        words = text.split(' ')
        next_text = ' '.join(words[int(len(words) / 2):])
        text = ' '.join(words[0:int(len(words) /2)]) + '\n' + next_text
        
        
    # Run the text size calculation again in case we modified the string above
    text_size_x, text_size_y = draw.textsize(text, font=font)
    draw.multiline_text(((width - text_size_x) / 2, ypos), text, fill=fill, font=font, align='center')
    return text_size_y

def rotate_randomly(im):
    return im.rotate(random.choice([0, 90, 180, 360]))    
    
    
