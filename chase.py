# -*- coding: utf-8 -*-

from pygameframework import Game
from pygameframework import GridWindow
from pygameframework import Color
from pygameframework import AsciiTileSheet
from pygameframework import Coordinate
from pygameframework import Direction
from pygameframework import Key
from pygameframework import Schedule
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
            actor.render(screen, pos)

    def to_coordinate(self, actor, direction):
        c = self._coordinate[actor]
        return c + direction

    def move_actor(self, actor, direction):
        c = self._coordinate[actor]
        self.put(c+direction, self.pickup(c))

class Actor(object):
    SPEED_UNIT = 1
    WAIT_TIME_MAX = 16
    WAIT_TIME_MIN = 0
    PLAYER_COLOR = (Color.RED, Color.AQUA, Color.YELLOW, Color.LIME)
    def __init__(self, player_id):
        self._player_id = player_id
        tile = AsciiTileLocator.get_tile('@', self.PLAYER_COLOR[self._player_id])
        self._sprite = Sprite(tile)
        self._walk_wait_frame = 3
        self._is_chaser = False
        self._visible = True
        self._waiting = False

    def render(self, screen, position):
        if not self._visible: return
        self._sprite.render(screen, position)

    def invisible(self):
        if not self.is_chaser(): return
        self._visible = False

    def visible(self):
        self._visible = True

    def is_visible(self):
        return self._visible

    def flashing(self, interval):
        self._sprite = FlashingSprite(self._sprite.graphic(), interval)

    def clear_render_effect(self):
        self._sprite = Sprite(self._sprite.graphic(), interval)

    def wait_walk(self):
        self.wait(self._walk_wait_frame)

    def speed_down(self):
        if self._walk_wait_frame < self.WAIT_TIME_MAX:
            self._walk_wait_frame += self.SPEED_UNIT

    def speed_up(self):
        if self._walk_wait_frame > self.WAIT_TIME_MIN:
            self._walk_wait_frame -= self.SPEED_UNIT

    def is_chaser(self):
        return self._is_chaser

    def be_chaser(self):
        tile = AsciiTileLocator.get_tile('&', self.PLAYER_COLOR[self._player_id])
        self._sprite.set_graphic(tile)
        self._is_chaser = True

    def be_runner(self):
        tile = AsciiTileLocator.get_tile('@', self.PLAYER_COLOR[self._player_id])
        self._sprite.set_graphic(tile)
        self._is_chaser = False

    def wait(self, wait_frame):
        self.waiting()
        Schedule(wait_frame).action(self.waiting).last(self.no_waiting)

    def waiting(self):
        self._waiting = True

    def no_waiting(self):
        self._waiting = False

    def is_waiting(self):
        return self._waiting

    def touch(self, other):
        if not self.is_chaser(): return
        self.be_runner()
        other.be_chaser()
        fleeze_tick = 150
        other.wait(fleeze_tick)
        Schedule(fleeze_tick).action(Flashing(other, 3).tick).last(other.visible)

class Flashing(object):
    def __init__(self, actor, interval):
        self._actor = actor
        self._interval = interval
        self._elapse = 0

    def tick(self):
        self._elapse += 1
        if self._elapse < self._interval: return
        self._elapse = 0
        if self._actor.is_visible(): self._actor.invisible()
        else: self._actor.visible()

class Sprite(object):
    def __init__(self, graphic):
        self._graphic = graphic

    def set_graphic(self, graphic):
        self._graphic = graphic

    def graphic(self):
        return self._graphic

    def render(self, screen, position):
        screen.draw(position, self._graphic)

class FlashingSprite(Sprite):
    def __init__(self, graphic, interval):
        Sprite.__init__(self, graphic)
        self._interval = interval

    def render(self, screen, position):
        screen.draw(position, self._graphic)

class TerrainMapHandler(object):
    _terrain_map = None
    _terrain_db = dict()

    @classmethod
    def load(cls, filename):
        f = open(filename, 'r')
        lines = [line.strip() for line in f]
        w, h = len(lines[0]), len(lines)
        cls._terrain_map = TerrainMap(w, h)
        for y, line in enumerate(lines):
            for x, glyph in enumerate(line):
                cls.put_terrain(glyph, Coordinate(x, y))
        f.close()

    @classmethod
    def initialize(cls):
        cls._terrain_map = TerrainMap(80, 20)
        cls._initialize_db()

    @classmethod
    def _initialize_db(cls):
        cls._terrain_db['.'] = Terrain('.', Color.SILVER).walkable()
        cls._terrain_db['#'] = Terrain('#', Color.SILVER)

    @classmethod
    def put_terrain(cls, name, coordinate):
        cls._terrain_map.put(cls._terrain_db[name], coordinate)

class MapHandler(TerrainMapHandler):
    _actor_map = None

    @classmethod
    def initialize(cls):
        TerrainMapHandler.initialize()
        cls._actor_map = ActorMap(80, 20)

class DungeonGenerator(TerrainMapHandler):
    def __init__(self):
        TerrainMapHandler.__init__(self)

    def generate(self):
        self.put_terrain('#', Coordinate(3, 4))

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

class WalkCommand(MapHandler):
    def __init__(self, actor):
        MapHandler.__init__(self)
        self._actor = actor
        self._run = False

    def set_run_mode(self, mode):
        self._run = mode

    def execute(self, direction):
        if self._actor.is_waiting(): return
        pos = self._actor_map.to_coordinate(self._actor, direction)
        if not self._terrain_map.is_walkable(pos): return
        other = self._actor_map.actor(pos)
        if other:
            self._actor.touch(other)
            return
        self._actor_map.move_actor(self._actor, direction)
        self._actor.wait_walk()

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
        self._actor_move(controller.pressed_keys())
        self._actor_action(controller.down_keys())
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

    def _actor_action(self, down_keys):
        if 'speed_up' in down_keys: self._actor.speed_up()
        if 'speed_down' in down_keys: self._actor.speed_down()

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
    def __init__(self):
        Game.__init__(self)
        MapHandler.__init__(self)
        self._window = None
        self._handlers = []

    def initialize(self):
        tile_sheet = AsciiTileSheet().initialize('Courier New', 18)
        AsciiTileLocator.provide(tile_sheet)
        MapHandler.initialize()
        TerrainMapHandler.load('map.data')
        DungeonGenerator().generate()
        actors = [Actor(player_id) for player_id in range(self.MAX_PLAYER)]
        actors[0].be_chaser() # TODO
        handlers = [ReadyMode(actor) for actor in actors]
        PlayerHandler.set_handlers(handlers)

    def update(self):
        if Key.ESCAPE in self._keyboard.pressed_keys(): sys.exit()
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
        .set_caption('*** Chace ***')
    runner.run()
