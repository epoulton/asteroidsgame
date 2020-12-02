import pygame


class TextCounter:
    """
    A counter class with an associated string representation for drawing
    to surfaces.
    """
    default_font_height = 16  # pixels

    def __init__(
            self,
            anchor,
            location,
            string,
            initial_count,
            color,
            config=None):
        """
        Initialize the counter according to the given arguments.

        anchor (two letter string) indicates the location on the counter
        that is fixed in place relative to a parent surface.

        location (tuple of ints) is the location on the parent surface
        at which to draw the counter.

        string (string) is the text string to be drawn at each frame.
        Each occurrence of "{0}" (with optional format spec) will be
        replaced by the current count value.

        initial_count (number) the initial value of the counter.

        color (tuple of ints) represents the RGB values of the color in
        which the counter should be drawn.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        self._anchor = anchor
        self._location = location
        self._string = string
        self._color = color
        self._config = config

        if config is not None:
            self._font_height = int(config['HUD']['font height'])
        else:
            self._font_height = TextCounter.default_font_height

        self._count = None
        self._image = None

        self._font = pygame.font.Font(None, self._font_height)

        # Assign self._count by property, updating self._image as a
        # side effect.
        self.count = initial_count

    @property
    def count(self):
        """
        Return the current value of the counter.
        """
        return self._count

    @count.setter
    def count(self, x):
        """
        Update the current value of the counter.

        x (number) is the new value of the counter.
        """
        self._count = x
        self._image = self._font.render(
            self._string.format(self._count),
            True,
            self._color)

    def draw(self, surface):
        """
        Draw the counter to the specified surface.

        surface (PyGame Surface object) is the surface to which the
        counter will be drawn.
        """
        if self._anchor[0] == 'n':
            y = self._location[1]

        elif self._anchor[0] == 'c':
            y = self._location[1] - self._image.get_size()[1] / 2

        else:  # self._anchor[0] == 's'
            y = self._location[1] - self._image.get_size()[1]

        if self._anchor[1] == 'w':
            x = self._location[0]

        elif self._anchor[1] == 'c':
            x = self._location[0] - self._image.get_size()[0] / 2

        else:  # self._anchor == 'e'
            x = self._location[0] - self._image.get_size()[0]

        surface.blit(self._image, (x, y))


class HorizontalGlyphCounter:
    """
    A counter class with an associated glyph which is copied in a
    horizontal line to the game surface.
    """

    default_scale = 1

    def __init__(
            self,
            anchor,
            location,
            image,
            initial_count,
            config=None):
        """
        Initialize the counter with the specified arguments.

        anchor (two letter string) indicates the location on the counter
        that is fixed in place relative to a parent surface.

        location (tuple of ints) is the location on the parent surface
        at which to draw the counter.

        image (PyGame Surface object) is the image to be drawn to
        represent the count.

        initial_count (int) the initial value of the counter.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """
        self._anchor = anchor
        self._location = location
        self.count = initial_count
        self._config = config

        if config is not None:
            self._scale = float(config['HUD']['glyph scale'])
        else:
            self._scale = HorizontalGlyphCounter.default_scale

        width, height = image.get_size()
        self._image = pygame.transform.smoothscale(
            image,
            (int(self._scale * width), int(self._scale * height)))

    def draw(self, surface):
        """
        Draw the counter to the specified surface.

        surface (PyGame Surface object) is the surface to which the
        counter will be drawn.
        """
        width, height = self._image.get_size()

        if self._anchor[0] == 'n':
            y = self._location[1]

        elif self._anchor[0] == 'c':
            y = self._location[1] - height / 2

        else:  # self._anchor[0] == 's'
            y = self._location[1] - height

        if self._anchor[1] == 'w':
            x = self._location[0]

        elif self._anchor[1] == 'c':
            x = self._location[0] - self.count * width / 2

        else:  # self._anchor[1] == 'e'
            x = self._location[0] - self.count * width

        for _ in range(self.count):
            surface.blit(self._image, (x, y))
            x += width
