# -*- coding: utf-8 -*-

from pygameframework import Game
from pygameframework import GridWindow
from pygameframework import Color
from pygameframework import AsciiTileSheet
from pygameframework import Coordinate
from pygameframework import Direction
from pygameframework import Job
import sys

class AsciiTileLocator(object):
    sheet = None
    @classmethod
    def provide(cls, new_sheet):
        cls.sheet = new_sheet

    @classmethod
    def get_tile(cls, glyph, color):
        return cls.sheet.get_tile(glyph, color)

class Terrain(object):
    (WALKABLE,) = range(1)
    def __init__(self, glyph, color):
        self._graphic = AsciiTileLocator.get_tile(glyph, color)
        self._property = set()

    def walkable(self):
        self._property.add(self.WALKABLE)
        return self

    def is_walkable(self):
        return self.WALKABLE in self._property

    def lender(self, screen, coordinate):
        screen.draw(coordinate, self._graphic)

class TerrainMap(object):
    def __init__(self, width, height):
        floor = Terrain('.', Color.SILVER).walkable()
        self._terrain = [[floor for x in range(width)] for y in range(height)]

    def render(self, screen):
        for y, line in enumerate(self._terrain):
            for x, tile in enumerate(line):
                tile.lender(screen, Coordinate(x, y))

    def put(self, terrain, coordinate):
        x, y = coordinate.xy()
        self._terrain[y][x] = terrain

    def is_walkable(self, coordinate):
        x, y = coordinate.xy()
        return self._terrain[y][x].is_walkable()

class ActorMap(object):
    def __init__(self, width, height):
        self._actor = dict()
        self._coordinate = dict()

    def pickup(self, coordinate):
        actor = self._actor[coordinate]
        del self._actor[coordinate]
        del self._coordinate[actor]
        return actor

    def actor(self, coordinate):
        if coordinate in self._actor:
            return self._actor[coordinate]
        return None

    def coordinate_of(self, actor):
        try:
            return self._coordinate[actor]
        except KeyError:
            return None

    def put(self, coordinate, actor):
        self._actor[coordinate] = actor
        self._coordinate[actor] = coordinate

    def render(self, screen):
        for pos, actor in self._actor.items():
            actor.render(pos, screen)

    def to_coordinate(self, actor, direction):
        c = self._coordinate[actor]
        return c + direction

    def move_actor(self, actor, direction):
        c = self._coordinate[actor]
        self.put(c+direction, self.pickup(c))

class Actor(object):
    SPEED_UNIT = 0.01
    WAIT_TIME_MAX = 1.0
    WAIT_TIME_MIN = 0.05
    def __init__(self, graphic):
        self._graphic = graphic
        self._walk_wait_time = 0.1

    def render(self, position, screen):
        screen.draw(position, self._graphic)

    def walk_wait_time(self):
        return self._walk_wait_time

    def speed_down(self):
        if self._walk_wait_time < self.WAIT_TIME_MAX:
            self._walk_wait_time += self.SPEED_UNIT

    def speed_up(self):
        if self._walk_wait_time > self.WAIT_TIME_MIN:
            self._walk_wait_time -= self.SPEED_UNIT

class MapHandler(object):
    _actor_map = None
    _terrain_map = None

    @classmethod
    def initialize(cls):
        cls._actor_map = ActorMap(80, 20)
        cls._terrain_map = TerrainMap(80, 20)

class DungeonGenerator(MapHandler):
    def __init__(self):
        MapHandler.__init__(self)

    def generate(self):
        wall = Terrain('#', Color.SILVER)
        self._terrain_map.put(wall, Coordinate(3, 4))

class PlayerHandler(object):
    _handlers = []

    @classmethod
    def set_handlers(self, handlers):
        self._handlers = handlers

    @classmethod
    def update(self, controllers, keyboard):
        for handler, controller in zip(self._handlers, controllers):
            handler.handle(controller, keyboard)

    @classmethod
    def change_handle(self, old_handle, new_handle):
        for i, handle in enumerate(self._handlers):
            if handle != old_handle: continue
            self._handlers[i] = new_handle
            break

class Activable(object):
    def __init__(self, state=True):
        self._is_active = state

    def is_active(self):
        return self._is_active

    def is_inactive(self):
        return not self.is_active()

    def active(self):
        self._is_active = True

    def inactive(self):
        self._is_active = False

class WillActive(Job):
    def __init__(self, time, target):
        Job.__init__(self, time)
        self._target = target

    def job(self):
        self._target.active()

class WalkCommand(MapHandler, Activable):
    def __init__(self, actor):
        Activable.__init__(self)
        MapHandler.__init__(self)
        self._actor = actor
        self._run = False

    def set_run_mode(self, mode):
        self._run = mode

    def execute(self, direction):
        if self.is_inactive(): return
        pos = self._actor_map.to_coordinate(self._actor, direction)
        if not self._terrain_map.is_walkable(pos): return
        if self._actor_map.actor(pos): return
        self._actor_map.move_actor(self._actor, direction)
        if not self._run:
            self._wait()

    def _wait(self):
        self.inactive()
        WillActive(self._actor.walk_wait_time(), self)

class WalkMode(PlayerHandler, MapHandler):
    def __init__(self, actor):
        MapHandler.__init__(self)
        self._actor = actor
        self._walk = WalkCommand(actor)

    def initialize(self):
        x = 1
        while self._actor_map.actor(Coordinate(x, 1)): x += 1
        self._actor_map.put(Coordinate(x, 1), self._actor)
        return self

    def handle(self, controller, keyboard=None):
        down_keys =  controller.pressed_keys()
        self._actor_move(down_keys)
        if not keyboard: return
        down_keys =  keyboard.pressed_keys()
        if ord('q') in down_keys: sys.exit()

    def _actor_move(self, down_keys):
        if set(['up', 'left']) <= down_keys: self._walk.execute(Direction.UPPER_LEFT)
        elif set(['up', 'right']) <= down_keys: self._walk.execute(Direction.UPPER_RIGHT)
        elif set(['down', 'left']) <= down_keys: self._walk.execute(Direction.LOWER_LEFT)
        elif set(['down', 'right']) <= down_keys: self._walk.execute(Direction.LOWER_RIGHT)
        elif 'left' in down_keys: self._walk.execute(Direction.LEFT)
        elif 'down' in down_keys: self._walk.execute(Direction.DOWN)
        elif 'up' in down_keys: self._walk.execute(Direction.UP)
        elif 'right' in down_keys: self._walk.execute(Direction.RIGHT)

class ReadyMode(PlayerHandler):
    def __init__(self, actor):
        self._actor = actor

    def handle(self, controller, keyboard=None):
        down_keys =  controller.pressed_keys()
        if 'start' not in down_keys: return
        self.change_handle(self, WalkMode(self._actor).initialize())

class Chace(Game, MapHandler):
    POSITION = Coordinate(0, 0)
    GRID_SIZE = Coordinate(10, 18)
    MAX_PLAYER = 4
    PLAYER_COLOR = (Color.RED, Color.AQUA, Color.LIME, Color.YELLOW)
    def __init__(self):
        Game.__init__(self)
        MapHandler.__init__(self)
        self._window = None
        self._handlers = []

    def initialize(self):
        tile_sheet = AsciiTileSheet().initialize('Courier New', 18)
        AsciiTileLocator.provide(tile_sheet)
        MapHandler.initialize()
        DungeonGenerator().generate()
        actors = [Actor(AsciiTileLocator.get_tile('@', color)) for color in self.PLAYER_COLOR]
        handlers = [ReadyMode(actor) for actor in actors]
        PlayerHandler.set_handlers(handlers)

    def update(self):
        PlayerHandler.update(self._controllers, self._keyboard)

    def set_screen(self, screen):
        self._screen = screen
        self._window = GridWindow(screen, self.POSITION, self.GRID_SIZE)

    def render(self):
        self._screen.fill()
        self._terrain_map.render(self._window)
        self._actor_map.render(self._window)

if __name__ == '__main__':
    from pygameframework.framework import GameRunner
    CONTROLLER_NUM = 4
    runner = GameRunner(Chace())\
        .initialize_system()\
        .initialize_screen(640, 480, 16)\
        .initialize_controller(CONTROLLER_NUM, 'config.ini')\
        .set_font('Courier New', 18)\
        .set_fps(30)\
        .set_caption('チェイス')
    runner.run()
