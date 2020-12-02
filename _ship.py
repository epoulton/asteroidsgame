import numpy
import numpy.linalg
import pygame

import _bullet

# Flags to return to the game when handling events. Currently, the only
# event requiring a response is when a bullet is fired.
BULLET_FIRED = 'bullet fired'


class Ship:
    """
    The ship class implements the player controlled ship, such as
    steering, collision behaviour, and firing bullets.
    """

    # Dynamics properties
    default_linear_acceleration = 100  # pixels / second**2
    default_angular_acceleration = 2 * numpy.pi  # radians / second**2

    # Display properties
    default_length = 30  # pixels
    default_width = 30  # pixels
    default_edge_width = 2  # pixels

    # Gameplay behavior properties.
    default_reload_period = 1  # second

    # List containing the pygame events that the ship handles.
    events_handled = [pygame.KEYDOWN, pygame.KEYUP]

    def __init__(
            self,
            position,
            velocity,
            direction,
            angular_velocity,
            color,
            config=None):
        """
        Initialize the ship according to the given arguments.

        position (iterable of ints) represents the ship's initial
        position in pixels (display surface coordinates).

        velocity (iterable of floats) represents the ship's initial
        velocity in pixels / second (display surface coordinates).

        direction (iterable of floats) represents the ship's initial
        direction vector in display surface coordinates.

        angular_velocity (float) represents the ships initial angular
        velocity in radians / second (clockwise positive).

        color (tuple of ints) represents the RGB values of the color in
        which the ship should be drawn.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        self._r_cm = numpy.array([position[0], position[1], 0])
        self._v_cm = numpy.array([velocity[0], velocity[1], 0])
        self._u_nose_cm = numpy.array([direction[0], direction[1], 0])
        self._omega = numpy.array([0, 0, angular_velocity])

        self._color = color
        self._config = config

        if config is not None:
            self._length = int(config['SHIP']['length'])
            self._width = int(config['SHIP']['width'])
            self._edge_width = int(config['SHIP']['edge width'])
            self._a = float(config['SHIP']['linear acceleration'])
            self._alpha = float(config['SHIP']['angular acceleration'])
            self._reload_period = float(config['SHIP']['reload period'])
        else:
            self._length = Ship.default_length
            self._width = Ship.default_width
            self._edge_width = Ship.default_edge_width
            self._a = Ship.default_linear_acceleration
            self._alpha = Ship.default_angular_acceleration
            self._reload_period = Ship.default_reload_period

        vertices = [
            (self._length, self._width / 2),
            (0, 0),
            (self._length / 3, self._width / 2),
            (0, self._width)]

        # Prototype surface that will be transformed for display at each
        # frame.
        self.prototype = pygame.Surface((self._length, self._width))
        self.prototype.set_colorkey('black')
        pygame.draw.polygon(
            self.prototype,
            self._color,
            vertices,
            self._edge_width)

        # The image surface is initialized and updated in the tick
        # method to reflect the ship's current direction.
        self._image = None

        # Counters to track the state of the main and steering
        # thrusters. By using -1, 0, and 1 rather than True and False,
        # the variables can be used directly in the dynamics equations
        # as well as encode the direction of angular acceleration.
        # For the main thrusters, 0 = inactive, 1 = active.
        self._thrusting = 0

        # For the steering thrusters, -1 = counterclockwise
        # acceleration, 0 = inactive, 1 = clockwise acceleration.
        self._steering = 0

        self._reloading = 0
        self._alive = True

        # Initialize self._image with its initial rotation.
        self.tick(0)

    @property
    def position(self):
        """
        Return the position of the ship.
        """
        return self._r_cm[:2]

    @position.setter
    def position(self, x):
        """
        Set the position of the ship.

        x (iterable of ints) representing the new position of the ship.
        """
        self._r_cm = numpy.array([x[0], x[1], 0])

    def tick(self, dt):
        """
        Update the position and status of the ship in preparation to
        draw the next frame.

        dt (float) is the time interval between subsequent frames.
        """

        # noinspection PyProtectedMember
        def rates_of_change(state):
            """
            A helper function that accepts the current dynamic state of
            the ship and returns the instantaneous rate of change of
            each parameter. Mathematically, dy/dt = rates_of_change(y).

            """

            r_cm, v_cm, u_nose_cm, omega = numpy.split(state, (3, 6, 9))

            d_dt_r_cm = v_cm
            d_dt_v_cm = self._thrusting * self._a * u_nose_cm
            d_dt_u_nose_cm = numpy.cross(omega, u_nose_cm)
            d_dt_omega = self._steering * self._alpha * numpy.array([0, 0, 1])

            return numpy.concatenate(
                (d_dt_r_cm, d_dt_v_cm, d_dt_u_nose_cm, d_dt_omega))

        # Update ship's dynamics using the 4th order explicit
        # Runge-Kutta method of approximating initial value problems.
        initial_state = numpy.concatenate(
            (self._r_cm, self._v_cm, self._u_nose_cm, self._omega))

        k1 = rates_of_change(initial_state)
        k2 = rates_of_change(initial_state + dt * k1 / 2)
        k3 = rates_of_change(initial_state + dt * k2 / 2)
        k4 = rates_of_change(initial_state + dt * k3)

        new_state = (initial_state + 1 / 6 * dt * (k1 + 2 * k2 + 2 * k3 + k4))

        (self._r_cm, self._v_cm, self._u_nose_cm, self._omega) = numpy.split(
            new_state,
            (3, 6, 9))

        # Without re-normalizing, the unit vector self._direction tends
        # to slowly shorten as the ship spins. The shorter unit vector
        # proportionally reduces the ship's linear acceleration. I
        # suspect this is a machine precision issue rather than an
        # algebra error. For now, simply re-normalize.
        # TODO: Look into this in the future.
        self._u_nose_cm /= numpy.linalg.norm(self._u_nose_cm)

        # Update self._image to reflect the ship's direction.
        theta = numpy.degrees(numpy.arctan2(
            self._u_nose_cm[1],
            self._u_nose_cm[0]))
        self._image = pygame.transform.rotate(self.prototype, -theta)

        self._reloading -= dt

    def draw(self, surface):
        """
        Draw the ship to the specified surface.

        surface (PyGame Surface object) is the surface to which the ship
        will be drawn.
        """

        x = self._r_cm[0] - self._image.get_width() / 2
        y = self._r_cm[1] - self._image.get_height() / 2
        surface.blit(self._image, (x, y))

    def get_size(self):
        """
        Return the size of the ship image as a tuple of ints
        representing the width and height in pixels.
        """

        # This method is a candidate for converting into a public
        # property.
        return self._image.get_size()

    def handle_event(self, event):
        """
        Handle user generated PyGame event passed to the ship by the
        game.

        event (PyGame event object) is the event to which the ship must
        react.
        """

        response = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._thrusting = 1

            elif event.key == pygame.K_LEFT:
                self._steering -= 1

            elif event.key == pygame.K_RIGHT:
                self._steering += 1

            elif event.key == pygame.K_SPACE:
                if self._reloading <= 0:
                    response = self.fire_bullet()

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self._thrusting = 0

            elif event.key == pygame.K_LEFT:
                self._steering += 1

            elif event.key == pygame.K_RIGHT:
                self._steering -= 1

        return response

    def fire_bullet(self):
        """
        Instantiate and fire a bullet from the nose of the ship.
        """

        self._reloading = self._reload_period

        r_gun = self._r_cm + self._length / 2 * self._u_nose_cm
        v_gun = (self._v_cm + self._length / 2
                 * numpy.cross(self._omega, self._u_nose_cm))

        bullet = _bullet.Bullet(
            r_gun[:2],
            v_gun[:2],
            self._u_nose_cm[:2],
            self._color,
            self._config)

        return BULLET_FIRED, bullet

    def is_alive(self):
        """
        Return a boolean representing whether the ship is currently
        alive.
        """

        # This method is a candidate for converting into a public
        # property.
        return self._alive

    def explode(self):
        """
        Execute necessary behaviour upon the ship exploding.
        """
        self._alive = False
