import numpy
import numpy.linalg
import numpy.random
import pygame
import scipy.optimize

rng = numpy.random.default_rng()


class Asteroid:
    """
    The asteroid class implements the asteroid sprites' dynamics and
    behaviour.
    """

    # Asteroids spawn with random exponentially distributed diameters.
    # Asteroids smaller than minimum_diameter are not hazardous to the
    # ship and do not spawn. Diameters are measured in pixels.
    default_minimum_diameter = 30
    default_median_diameter = 60

    # Asteroids spawn with random exponentially distributed velocities,
    # measured in pixels / second.
    default_minimum_speed = 0
    default_median_speed = 50

    # Following an explosion, some fraction of the asteroid's area has
    # been destroyed. area_fraction is the fraction of the asteroid's
    # initial area that survives in the form of fragments.
    # Mathematically,
    # sum(fragment_areas) = area_fraction * asteroid_area.
    default_area_ratio = 0.75

    # Following an explosion, some energy has been added to the system,
    # stored in the form of fragments. Mathematically,
    # sum(fragment_energies) = energy_fraction * asteroid_energy
    default_energy_ratio = 1.1

    # Display properties.
    default_edge_width = 2  # pixels

    @staticmethod
    def generate_diameter(config=None):
        """
        Randomly generate a diameter according to the configured
        distribution parameters.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        if config is not None:
            d_min = int(config['ASTEROID']['minimum diameter'])
            d_med = int(config['ASTEROID']['median diameter'])
        else:
            d_min = Asteroid.default_minimum_diameter
            d_med = Asteroid.default_median_diameter

        beta = (d_med - d_min) / numpy.log(2)
        return rng.exponential(beta) + d_min

    @staticmethod
    def generate_position(window_size):
        """
        Randomly generate a position within the specified window.

        window_size (tuple of ints) represents the width and height of
        the interactive display window.
        """

        return numpy.array(window_size) * rng.uniform(0, 1, 2)

    @staticmethod
    def generate_velocity(config=None):
        """
        Randomly generate a velocity according to the configured
        distribution parameters.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        if config is not None:
            s_min = float(config['ASTEROID']['minimum speed'])
            s_med = float(config['ASTEROID']['median speed'])
        else:
            s_min = Asteroid.default_minimum_speed
            s_med = Asteroid.default_median_speed

        beta = (s_med - s_min) / numpy.log(2)
        speed = rng.exponential(beta) + s_min

        direction = rng.uniform(0, 1, 2)
        direction /= numpy.linalg.norm(direction)

        return speed * direction

    def __init__(self, diameter, position, velocity, color, config=None):
        """
        Initialize the asteroid according to the given arguments.

        diameter (int) is the diameter of the asteroid in pixels.

        position (tuple of ints) is the initial position of the asteroid
        in pixels (display surface coordinates).

        velocity (tuple of floats) is the initial velocity of the
        asteroid in pixels / second (display surface coordinates).

        color (tuple of ints) represents the RGB values of the color in
        which the asteroid should be drawn.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        self.diameter = diameter
        self._r = numpy.array(position)
        self._v = numpy.array(velocity)
        self._color = color
        self._config = config

        if config is not None:
            self._edge_width = int(config['ASTEROID']['edge width'])
            self._area_ratio = float(config['ASTEROID']['area ratio'])
            self._energy_ratio = float(config['ASTEROID']['energy ratio'])
            self._minimum_diameter = int(
                config['ASTEROID']['minimum diameter'])
        else:
            self._edge_width = Asteroid.default_edge_width
            self._area_ratio = Asteroid.default_area_ratio
            self._energy_ratio = Asteroid.default_energy_ratio
            self._minimum_diameter = Asteroid.default_minimum_diameter

        self._image = pygame.Surface((self.diameter, self.diameter))
        self._image.set_colorkey('black')

        pygame.draw.circle(self._image, self._color,
                           (self.diameter / 2, self.diameter / 2),
                           self.diameter / 2, self._edge_width)

        self._alive = True

    @property
    def position(self):
        """
        Return the position of the asteroid.
        """
        return self._r

    @position.setter
    def position(self, x):
        """
        Set the position of the asteroid.

        x (iterable of ints) is the new position of the asteroid.
        """
        self._r = numpy.array(x)

    def tick(self, dt):
        """
        Update the position and status of the asteroid in preparation to
        draw the next frame.

        dt (float) is the time interval between subsequent frames.
        """

        self._r += self._v * dt

    def draw(self, surface):
        """
        Draw the asteroid to the specified surface.

        surface (PyGame Surface object) is the surface to which the
        asteroid will be drawn.
        """

        x = self._r[0] - self._image.get_width() / 2
        y = self._r[1] - self._image.get_height() / 2
        surface.blit(self._image, (x, y))

    def get_size(self):
        """
        Return the size of the ship image as a tuple of ints
        representing the width and height in pixels.
        """

        return self._image.get_size()

    def is_alive(self):
        """
        Return a boolean representing whether the asteroid is currently
        alive.
        """

        return self._alive

    def explode(self, fragments_count):
        """
        Execute necessary behaviour upon the asteroid exploding.

        fragments_count (int) is the number of fragments to generate
        upon exploding.
        """
        self._alive = False

        diameter_ratio = numpy.sqrt(self._area_ratio / fragments_count)
        if self.diameter < self._minimum_diameter / diameter_ratio:
            return []

        else:
            # noinspection PyProtectedMember
            def system_of_equations(v):
                """
                A helper function that accepts a vector of fragment
                velocities and returns a closeness measure of whether
                they satisfy the equations defined within. This function
                is intended to be passed to the nonlinear system solver.
                """
                # Conservation of momentum in the x and y directions
                com = numpy.empty((2,))
                for kk in range(len(com)):
                    com[kk] = (self._v[kk]
                               - numpy.sum(v[kk:: 2]) / fragments_count)

                # Speeds vector - norm of each velocity pair in v
                s = numpy.array([numpy.linalg.norm(v[2 * kk: 2 * kk + 2])
                                 for kk in range(fragments_count)])

                # Conservation of energy
                coe = (self._energy_ratio
                       * numpy.linalg.norm(self._v) ** 2
                       - self._area_ratio
                       / fragments_count
                       * numpy.sum(s ** 2))
                coe = numpy.array([coe])

                # Equal velocities constraints
                ev = numpy.empty((fragments_count - 1,))
                for kk in range(len(ev)):
                    ev[kk] = s[kk] - s[kk + 1]

                # Equal angles constraint
                ea = numpy.empty((fragments_count - 2,))
                for kk in range(len(ea)):
                    ea[kk] = (numpy.dot(v[2 * kk: 2 * kk + 2],
                                        v[2 * (kk + 1): 2 * (kk + 1) + 2])
                              - numpy.dot(v[2 * (kk + 1): 2 * (kk + 1) + 2],
                                          v[2 * (kk + 2): 2 * (kk + 2) + 2]))

                return numpy.concatenate((com, coe, ev, ea))

            # Solve for the fragment velocities by solving a system of
            # nonlinear equations.
            v0 = numpy.zeros((2 * fragments_count,))
            sol = scipy.optimize.root(system_of_equations, v0)

            fragments = [Asteroid(diameter_ratio * self.diameter,
                                  self._r,
                                  (0, 0),
                                  self._color,
                                  self._config)
                         for _ in range(fragments_count)]

            for k in range(len(fragments)):
                fragments[k]._v = sol.x[2 * k: 2 * k + 2]

            return fragments
