import configparser
import pygame
import pygame_menu

import _game

# Flags to track the current state of the game and enable switching
# between menu interfaces and gameplay.
WELCOME = 'welcome'
PLAYING = 'playing'
PAUSED = 'paused'
END = 'end'
EXIT = 'exit'


class AsteroidsGame:
    """
    A Python game inspired by the classic arcade game Asteroids.
    """

    # Default display properties
    default_window_size = (1000, 562)  # pixels
    default_frame_rate = 30  # frames / second
    default_background_color = 'black'
    default_foreground_color = 'white'

    def __init__(self, config=None):
        """
        Initialize the game with the desired gameplay configuration.

        config (ConfigParser object) optionally contains the necessary
        gameplay parameters.
        If config is not given, default values will be used.
        All necessary fields must be present in the config file; no
        handling is done for missing fields.
        """

        self._config = config

        if self._config is not None:
            self._window_size = (int(config['DISPLAY']['width']),
                                 int(config['DISPLAY']['height']))
            self._frame_rate = int(config['DISPLAY']['frame rate'])
            self._background_color = config['DISPLAY']['background color']
            self._foreground_color = config['DISPLAY']['foreground color']
        else:
            self._window_size = AsteroidsGame.default_window_size
            self._frame_rate = AsteroidsGame.default_frame_rate
            self._background_color = AsteroidsGame.default_background_color
            self._foreground_color = AsteroidsGame.default_foreground_color

        icon = pygame.image.load('icon.png')
        pygame.display.set_icon(icon)

        self._surface = pygame.display.set_mode(self._window_size)
        pygame.display.set_caption('Asteroids')

        menu_theme = pygame_menu.themes.Theme(
            background_color=pygame.colordict.THECOLORS[self._background_color],
            menubar_close_button=False,
            title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_NONE,
            title_font=pygame_menu.font.FONT_8BIT,
            widget_font=pygame_menu.font.FONT_8BIT)

        self._welcome_menu = pygame_menu.Menu(
            0.9 * self._window_size[1],
            0.9 * self._window_size[0],
            'ASTEROIDS',
            mouse_motion_selection=True,
            theme=menu_theme)
        self._controls_menu = pygame_menu.Menu(
            0.9 * self._window_size[1],
            0.9 * self._window_size[0],
            'CONTROLS',
            mouse_motion_selection=True,
            theme=menu_theme)
        self._about_menu = pygame_menu.Menu(
            0.9 * self._window_size[1],
            0.9 * self._window_size[0],
            'ABOUT',
            mouse_motion_selection=True,
            theme=menu_theme)
        self._pause_menu = pygame_menu.Menu(
            0.5 * self._window_size[1],
            0.5 * self._window_size[0],
            'PAUSED',
            mouse_motion_selection=True,
            theme=menu_theme)
        self._game_over_menu = pygame_menu.Menu(
            0.9 * self._window_size[1],
            0.9 * self._window_size[0],
            'GAME OVER',
            mouse_motion_selection=True,
            theme=menu_theme)

        # Helper function that gets bound to the menu button actions.
        def set_next_state(next_state):
            self._next_state = next_state

        self._welcome_menu.add_button('PLAY', set_next_state, PLAYING)
        self._welcome_menu.add_button('CONTROLS', self._controls_menu)
        self._welcome_menu.add_button('ABOUT', self._about_menu)
        self._welcome_menu.add_button('EXIT', set_next_state, EXIT)

        controls_text = (
            'Press the UP key to accelerate forward',
            'Press the LEFT and RIGHT keys to accelerate rotationally',
            'Press the SPACE key to fire a bullet',
            'Press the P key to pause the game')
        controls_font_size = 16

        # TODO: Change the font to make the text more readable.
        for substring in controls_text:
            # noinspection PyTypeChecker
            self._controls_menu.add_label(
                substring,
                font_size=controls_font_size)

        self._controls_menu.add_button('BACK', pygame_menu.events.BACK)

        about_text = (
            'This Asteroids game was created as a learning exercise by '
            'epoulton. It is published under the MIT open source license, '
            'copyright 2020. "asteroid" icon by Mat fine from '
            'thenounproject.com.')
        about_font_size = 16

        # TODO: Change the font to make the text more readable.
        # noinspection PyTypeChecker
        self._about_menu.add_label(
            about_text,
            max_char=-1,
            font_size=about_font_size)
        self._about_menu.add_button('BACK', pygame_menu.events.BACK)

        self._pause_menu.add_button('RESUME', set_next_state, PLAYING)
        self._pause_menu.add_button('END GAME', set_next_state, END)

        self._game_over_menu.add_button('REPLAY', set_next_state, WELCOME)
        self._game_over_menu.add_button('EXIT', set_next_state, EXIT)

        self._map_states_menus = {
            WELCOME: self._welcome_menu,
            PAUSED: self._pause_menu,
            END: self._game_over_menu}

        self._game = None

        # _state property re-initializes self._game when set to WELCOME.
        self._state = WELCOME
        self._next_state = self._state

        self._clock = pygame.time.Clock()

    @property
    def _state(self):
        return self._private_state

    @_state.setter
    def _state(self, x):
        self._private_state = x

        if self._private_state == WELCOME:
            self._game = _game.Game(
                self._window_size,
                self._foreground_color,
                self._config)

    def play(self):
        """
        Begin interactive gameplay.
        """

        while self._state != EXIT:
            # Erase the surface.
            self._surface.fill(self._background_color)

            # Draw the relevant images to the surface.
            if self._state in self._map_states_menus:
                if self._state == PAUSED:
                    # The pause screen features a darkened image of the
                    # current frozen game state drawn behind the menu.
                    background = self._game.image
                    background.set_alpha(64)
                    self._surface.blit(background, (0, 0))

                self._map_states_menus[self._state].draw(self._surface)

            elif self._state == PLAYING:
                self._game.draw(self._surface)

            pygame.display.update()

            # Handle user generated events.
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._next_state = EXIT

                # The 'P' key pauses the game.
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self._next_state = PAUSED

                elif event.type in self._game.event_types_handled:
                    # None of the events handled by the game need to
                    # return a value to the game manager. It's possible
                    # this won't always be the case, and the following
                    # call will need to handle a return value.
                    self._game.handle_event(event)

            # Update the on-screen graphics entities.
            if self._state in self._map_states_menus:
                self._map_states_menus[self._state].update(events)

            elif self._state == PLAYING:
                # The Game.tick() method returns a flag to indicate the
                # outcome of the game during the update. Flags are
                # defined in the _game module.
                outcome = self._game.tick(1 / self._frame_rate)

                if outcome == _game.OVER:
                    self._next_state = END

            # Continue to the next frame and update self._state.
            self._clock.tick(self._frame_rate)

            if self._next_state != self._state:
                self._state = self._next_state


if __name__ == '__main__':
    game_config = configparser.ConfigParser()
    game_config.read('config.ini')

    pygame.init()
    AsteroidsGame(game_config).play()
