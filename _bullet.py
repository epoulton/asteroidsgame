import numpy
import pygame


class Bullet:
    """
    The bullet class implements the bullets sprites' dynamics and
    behaviour.
    """

    # Dynamics properties
    default_muzzle_speed = 100  # pixels / second

    # Display properties
    default_diameter = 5  # pixels

    # Gameplay behavior properties
    default_lifespan = 5  # seconds

    def __init__(
            self,
            gun_position,
            gun_velocity,
            gun_direction,
            color,
            config=None):
        """
        Initialize the bullet according to the given arguments.

        gun_position (iterable of ints) represents the gun's position
        in pixels (display surface coordinates) at the moment of firing.

        gun_velocity (iterable of floats) represents the gun's velocity
        in pixels / second (display surface coordinates) at the moment
        of firing.

        gun_direction (iterable of floats) represents the gun's
        direction vector (display surface coordinates) at the moment of
        firing.

        color (tuple of ints) represents the RGB values of the color in
        which the bullet should be drawn.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        self._r = numpy.array(gun_position)
        self._color = color
        self._config = config

        if config is not None:
            self._diameter = int(config['BULLET']['diameter'])
            self._muzzle_speed = float(config['BULLET']['muzzle speed'])
            self._lifespan = float(config['BULLET']['lifespan'])
        else:
            self._diameter = Bullet.default_diameter
            self._muzzle_speed = Bullet.default_muzzle_speed
            self._lifespan = Bullet.default_lifespan

        self._v = gun_velocity + self._muzzle_speed * gun_direction

        self._image = pygame.Surface((self._diameter, self._diameter))
        self._image.set_colorkey('black')
        pygame.draw.circle(
            self._image,
            self._color,
            (self._diameter / 2, self._diameter / 2),
            self._diameter / 2)

        self._alive = True
        self._age = 0

    @property
    def position(self):
        """
        Return the position of the bullet.
        """
        return self._r

    @position.setter
    def position(self, x):
        """
        Set the position of the bullet.

        x (iterable of ints) is the new position of the bullet.
        """
        self._r = numpy.array(x)

    def tick(self, dt):
        """
        Update the position and status of the bullet in preparation to
        draw the next frame.

        dt (float) is the time interval between subsequent frames.
        """

        self._r += self._v * dt
        self._age += dt

        if self._age >= self._lifespan:
            self.explode()

    def draw(self, surface):
        """
        Draw the bullet to the specified surface.

        surface (PyGame Surface object) is the surface to which the
        bullet will be drawn.
        """

        x = self._r[0] - self._image.get_width() / 2
        y = self._r[1] - self._image.get_height() / 2
        surface.blit(self._image, (x, y))

    def get_size(self):
        """
        Return the size of the ship image as a tuple of ints
        representing the width and height in pixels.
        """

        # This method is a candidate for converting into a public
        # property.
        return self._image.get_size()

    def is_alive(self):
        """
        Return a boolean representing whether the bullet is currently
        alive.
        """

        # This method is a candidate for converting into a public
        # property.
        return self._alive

    def explode(self):
        """
        Execute necessary behaviour upon the bullet exploding.
        """

        self._alive = False
