import pygame
import numpy.linalg

import _asteroid
import _hud
import _ship

# Flags to return to the game manager indicating whether the game has
# been lost or is continuing.
PLAYING = 'playing'
OVER = 'over'


class Game:
    """
    The game object handles all gameplay mechanics such as sprites and
    scoring.
    """

    # Default gameplay properties
    default_initial_lives = 3
    default_asteroids_count = 3
    default_fragments_count = 2
    default_respawn_period = 3  # seconds

    # The game handles no user events at the moment. All user events not
    # handled by the game manager are passed through to the ship.
    event_types_handled = _ship.Ship.events_handled

    def __init__(self, window_size, foreground_color, config=None):
        """
        Initialize the game, consistent with the interactive display.

        window_size (tuple of ints) represents the width and height of
        the interactive display window.

        foreground_color (tuple of ints) represents the RGB values of
        the color in which the game should be drawn.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        self._window_size = window_size
        self._foreground_color = foreground_color
        self._config = config

        if config is not None:
            self._initial_lives = int(config['GAME']['initial lives'])
            self._asteroids_count = int(config['GAME']['asteroids count'])
            self._fragments_count = int(
                config['GAME']['asteroid fragments count'])
            self._respawn_period = float(config['GAME']['respawn period'])
        else:
            self._initial_lives = Game.default_initial_lives
            self._asteroids_count = Game.default_asteroids_count
            self._fragments_count = Game.default_fragments_count
            self._respawn_period = Game.default_respawn_period

        self._ship_spawn_parameters = {
            'position': (self._window_size[0] / 2, self._window_size[1] / 2),
            'velocity': (0, 0),
            'direction': (0, -1),
            'angular velocity': 0}

        self._ship = _ship.Ship(
            self._ship_spawn_parameters['position'],
            self._ship_spawn_parameters['velocity'],
            self._ship_spawn_parameters['direction'],
            self._ship_spawn_parameters['angular velocity'],
            self._foreground_color,
            self._config)

        self._score = _hud.TextCounter(
            'ne',
            (self._window_size[0], 0),
            'Score: {0}',
            0,
            self._foreground_color,
            self._config)
        self._level = _hud.TextCounter(
            'se',
            self._window_size,
            'Level: {0}',
            1,
            self._foreground_color,
            self._config)
        self._respawn_timer = _hud.TextCounter(
            'nc',
            (self._window_size[0] / 2, 0),
            'Respawn in {0:.0f}',
            self._respawn_period,
            self._foreground_color,
            self._config)
        self._lives = _hud.HorizontalGlyphCounter(
            'nw',
            (0, 0),
            self._ship.prototype,
            self._initial_lives - 1)

        self._asteroids = self._spawn_asteroids()
        self._bullets = []

        # self._image is initialized here, and then made read only by
        # the public image property.
        self._image = pygame.Surface(self._window_size)
        self._image.set_colorkey('black')

    @property
    def image(self):
        """
        Return a copy of the game image.
        """
        return self._image.copy()

    def tick(self, dt):
        """
        Update the position and status of the game (and all sprites) in
        preparation to draw the next frame.

        dt (float) is the time interval between subsequent frames.
        """

        # Handle collisions between sprites.
        self._handle_asteroid_bullet_collisions()
        self._handle_asteroid_ship_collisions()

        # Update all sprite positions, including boundary crossings.
        self._ship.tick(dt)
        self._handle_boundary_crossings(self._ship)

        for bullet in self._bullets:
            bullet.tick(dt)
            self._handle_boundary_crossings(bullet)

        for asteroid in self._asteroids:
            asteroid.tick(dt)
            self._handle_boundary_crossings(asteroid)

        # Increment the level and spawn new asteroids if they have all
        # been destroyed.
        any_asteroids_alive = any(
            [asteroid.is_alive() for asteroid in self._asteroids])

        if not any_asteroids_alive:
            if self._ship.is_alive() or self._lives.count > 0:
                self._level.count += 1
                self._asteroids = self._spawn_asteroids()

        # Decrement the respawn timer and spawn a new ship if
        # appropriate, or end the game.
        self._respawn_timer.count -= dt

        if not self._ship.is_alive() and self._respawn_timer.count <= 1:
            if self._lives.count <= 0:
                return OVER
            else:
                self._lives.count -= 1
                self._ship = _ship.Ship(
                    self._ship_spawn_parameters['position'],
                    self._ship_spawn_parameters['velocity'],
                    self._ship_spawn_parameters['direction'],
                    self._ship_spawn_parameters['angular velocity'],
                    self._foreground_color,
                    self._config)

        return PLAYING

    def draw(self, surface):
        """
        Draw the game (and all sprites) to the specified surface.

        surface (PyGame Surface object) is the surface to which the game
        will be drawn.
        """

        # Erase the game surface.
        self._image.fill('black')

        # Draw all living sprites to the game surface.
        if self._ship.is_alive():
            self._ship.draw(self._image)

        for bullet in self._bullets:
            if bullet.is_alive():
                bullet.draw(self._image)

        for asteroid in self._asteroids:
            if asteroid.is_alive():
                asteroid.draw(self._image)

        # Draw the persistent widgets to the game surface.
        for widget in [self._score, self._level, self._lives]:
            widget.draw(self._image)

        # If appropriate, draw the respawn timer to the game surface.
        if not self._ship.is_alive() and self._lives.count > 0:
            self._respawn_timer.draw(self._image)

        # Draw the game surface to the screen (the surfaced passed by
        # the game manager).
        surface.blit(self._image, (0, 0))

    def handle_event(self, event):
        """
        Handle user generated PyGame event passed to the game by the
        game manager.

        event (PyGame event object) is the event to which the game must
        react.
        """

        if event.type in self._ship.events_handled:
            response = self._ship.handle_event(event)

            # Currently, the only event to which the ship responds is
            # when a bullet has been fired. The ship's event response
            # format has been designed so that it may be extended to
            # additional events in the future.
            if response and response[0] == _ship.BULLET_FIRED:
                self._bullets.append(response[1])

    def _handle_asteroid_bullet_collisions(self):
        # TODO: Revise to implement pixel perfect collision detection.
        living_bullets = [
            bullet for bullet in self._bullets if bullet.is_alive()]
        living_asteroids = [
            asteroid for asteroid in self._asteroids if asteroid.is_alive()]

        for bullet in living_bullets:
            for asteroid in living_asteroids:
                separation = numpy.linalg.norm(
                    bullet.position - asteroid.position)

                if separation <= asteroid.diameter / 2:
                    self._asteroids += asteroid.explode(self._fragments_count)
                    bullet.explode()
                    self._score.count += 1

    def _handle_asteroid_ship_collisions(self):
        # TODO: Revise to implement pixel perfect collision detection.
        if not self._ship.is_alive():
            return

        living_asteroids = [
            asteroid for asteroid in self._asteroids if asteroid.is_alive()]

        for asteroid in living_asteroids:
            separation = numpy.linalg.norm(
                self._ship.position - asteroid.position)

            if separation <= asteroid.diameter / 2:
                self._ship.explode()
                self._asteroids += asteroid.explode(self._fragments_count)
                self._respawn_timer.count = self._respawn_period

    def _handle_boundary_crossings(self, sprite):
        if not sprite.is_alive():
            return

        width, height = sprite.get_size()

        if sprite.position[0] < -width / 2:
            sprite.position = (
                self._window_size[0] + width / 2, sprite.position[1])

        elif sprite.position[0] > self._window_size[0] + width / 2:
            sprite.position = (-width / 2, sprite.position[1])

        if sprite.position[1] < -height / 2:
            sprite.position = (
                sprite.position[0], self._window_size[1] + height / 2)

        elif sprite.position[1] > self._window_size[1] + height / 2:
            sprite.position = (sprite.position[0], -height / 2)

    def _spawn_asteroids(self):
        new_asteroids = []

        for _ in range(self._asteroids_count):
            diameter = _asteroid.Asteroid.generate_diameter()

            while True:
                position = _asteroid.Asteroid.generate_position(
                    self._window_size)
                separation = numpy.linalg.norm(self._ship.position - position)

                if self._ship.is_alive() and separation <= diameter / 2:
                    continue
                else:
                    break

            # The following equation ensures the asteroids' base speed
            # is multiplied by 0.1 for each level completed.
            speed_multiplier = (self._level.count + 9) / 10

            velocity = _asteroid.Asteroid.generate_velocity()

            new_asteroids.append(_asteroid.Asteroid(
                diameter,
                position,
                speed_multiplier * velocity,
                self._foreground_color))

        return new_asteroids
