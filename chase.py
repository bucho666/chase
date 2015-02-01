# -*- coding: utf-8 -*-
from pygameframework import Game
from pygameframework import GridWindow
from pygameframework import Color
from pygameframework import AsciiTileSheet
from pygameframework import Coordinate
from pygameframework import Direction
from pygameframework import Key
from pygameframework import Schedule
from pygameframework import Sound
import sys
import random

class SoundEffect(object):
    @classmethod
    def play_touch(cls):
        Sound.play('touch.ogg')

    @classmethod
    def play_join(cls):
        Sound.play('join.ogg')

    @classmethod
    def play_bgm(cls):
        Sound.play_bgm('bgm.ogg')

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
        self._properties = set()

    def walkable(self):
        self._properties.add(self.WALKABLE)
        return self

    def is_walkable(self):
        return self.WALKABLE in self._properties

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

    def walkable_coordinates(self):
        for y, line in enumerate(self._terrain):
            for x, tile in enumerate(line):
                if self._terrain[y][x].is_walkable():
                    yield Coordinate(x, y)

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

    def count_actors(self):
        return len(self._actor)

    def actors(self):
        for actor in self._actor.values():
            yield actor

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

class InvisibleSkill(object):
    def __init__(self, actor):
        self._actor = actor
        self._active = False

    def active(self):
        if self._active: return
        self._actor.be_invisible()
        self._active = True

    def inactive(self):
        self._actor.be_visible()
        self._active = False

class DashSkill(object):
    def __init__(self, actor):
        self._actor = actor
        self._active = False

    def active(self):
        if self._active: return
        self._actor.running()
        self._active = True

    def inactive(self):
        self._actor.walking()
        self._active = False

class Actor(object):
    WAIT_TIME_MAX = 16
    WAIT_TIME_MIN = 0
    PLAYER_COLOR = (Color.RED, Color.AQUA, Color.YELLOW, Color.LIME)
    CHASER_GLYPH, RUNNER_GLYPH = ('&', '@')
    def __init__(self, player_id):
        self._sprite = Sprite(self.RUNNER_GLYPH, self.PLAYER_COLOR[player_id])
        self._status = Status()
        self._skill = InvisibleSkill(self._status)

    def render(self, screen, position):
        if self._status.is_invisible(): return
        self._sprite.render(screen, position)

    def is_chaser(self):
        return self._status.is_chaser()

    def be_chaser(self):
        self._sprite.change_glyph(self.CHASER_GLYPH)
        self._status.be_chaser()
        self.change_skill(DashSkill(self._status))

    def is_runner(self):
        return self.is_chaser()

    def be_runner(self):
        self._sprite.change_glyph(self.RUNNER_GLYPH)
        self._status.be_runner()
        self.change_skill(InvisibleSkill(self._status))

    def wait(self):
        self._status.wait_walk_frame()

    def is_waiting(self):
        return self._status.is_waiting()

    def touch(self, other):
        if self._status.is_runner(): return
        SoundEffect.play_touch()
        self.be_runner()
        other.be_chaser()
        other.freeze()

    def freeze(self, frame=150):
        self._status.wait(frame)
        self.flush(Color.BLACK, frame=frame, interval=5)

    def flush(self, color, interval=3, frame=150):
        flushing = Flushing(self._sprite, color, interval)
        Schedule(frame).action(flushing.update).last(flushing.stop)

    def use_skill(self):
        self._skill.active()

    def unuse_skill(self):
        self._skill.inactive()

    def change_skill(self, new_skill):
        self._skill.inactive()
        self._skill = new_skill

class Status(object):
    CHASER, WAIT, INVISIBLE, FORCE_VISIBLE = range(4)
    def __init__(self):
        self._properties = Property([self.CHASER, self.WAIT, self.INVISIBLE, self.FORCE_VISIBLE])
        self._walk_wait_frame = 3
        self._life = 100

    def wait_walk_frame(self):
        self.wait(self._walk_wait_frame)

    def life(self):
        return self._life

    def damage(self, value):
        self._life -= value
        if self._life < 0: self._life = 0

    def be_invisible(self):
        self._properties.set_properties(self.INVISIBLE)

    def be_visible(self):
        self._properties.unset_properties(self.INVISIBLE)

    def is_invisible(self):
        return self._properties.is_active(self.INVISIBLE)

    def walking(self):
        self._walk_wait_frame = 2

    def running(self):
        self._walk_wait_frame = 1

    def be_chaser(self):
        self._properties.set_properties(self.CHASER)

    def be_runner(self):
        self._properties.unset_properties(self.CHASER)

    def is_chaser(self):
        return self._properties.is_active(self.CHASER)

    def is_runner(self):
        return not self.is_chaser()

    def wait(self, wait_frame):
        self._properties.set_properties(self.WAIT)
        Schedule(wait_frame).last(self.no_wait)

    def no_wait(self):
        self._properties.unset_properties(self.WAIT)

    def is_waiting(self):
        return self._properties.is_active(self.WAIT)

    def be_no_force_visible(self):
        self._properties.unset_properties(self.FORCE_VISIBLE)

    def is_force_visible(self):
        return self._properties.is_active(self.FORCE_VISIBLE)

class Property(object):
    def __init__(self, properties):
        self._properties = dict()
        for name in properties: self._properties[name] = 0

    def is_active(self, name):
        return self._properties[name] > 0

    def is_inactive(self, name):
        return not self.active(name)

    def set_properties(self, name):
        self._properties[name] += 1

    def unset_properties(self, name):
        if self._properties[name] is 0: return
        self._properties[name] -= 1

class Counter(object):
    def __init__(self, end):
        self._end = end
        self._current = 0

    def tick(self):
        self._current += 1
        self._current %= self._end

    def is_over(self):
        return self._current is 0

class Flushing(object):
    def __init__(self, sprite, color, interval):
        self._sprite = sprite
        self._original_color = sprite.color()
        self._change_color = color
        self._frame_counter = Counter(interval)

    def update(self):
        self._frame_counter.tick()
        if not self._frame_counter.is_over(): return
        if self._sprite.color() is self._original_color:
            self._sprite.change_color(self._change_color)
        else:
            self._sprite.change_color(self._original_color)

    def stop(self):
        self._sprite.change_color(self._original_color)

class Sprite(object):
    def __init__(self, glyph, color):
        self._graphic = AsciiTileLocator.get_tile(glyph, color)
        self._glyph = glyph
        self._color = color

    def color(self):
        return self._color

    def render(self, screen, position):
        screen.draw(position, self._graphic)

    def change_color(self, new_color):
        self._color = new_color
        self._update()

    def change_glyph(self, new_glyph):
        self._glyph = new_glyph
        self._update()

    def _update(self):
        self._graphic = AsciiTileLocator.get_tile(self._glyph, self._color)

class TerrainMapHandler(object):
    _terrain_map = None
    _terrain_db = dict()

    @classmethod
    def load(cls, filename):
        f = open(filename, 'r')
        lines = [line.rstrip('\n') for line in f]
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
        cls._terrain_db[' '] = Terrain(' ', Color.BLACK)

    @classmethod
    def put_terrain(cls, name, coordinate):
        cls._terrain_map.put(cls._terrain_db[name], coordinate)

class MapHandler(TerrainMapHandler):
    _actor_map = None

    @classmethod
    def initialize(cls):
        TerrainMapHandler.initialize()
        cls._actor_map = ActorMap(80, 20)

    def choice_random_open_coordinate(self):
       return random.choice([c for c in self._terrain_map.walkable_coordinates()\
               if not self._actor_map.actor(c)])

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
        self._actor.wait()

class WalkMode(PlayerHandler, MapHandler):
    def __init__(self, actor):
        MapHandler.__init__(self)
        self._actor = actor
        self._walk = WalkCommand(actor)

    def initialize(self):
        if self._actor_map.count_actors() is 0:
            self._actor.be_chaser()
        if self._actor_map.count_actors() is 1:
            SoundEffect.play_bgm()
        self._actor_map.put(self.choice_random_open_coordinate(),
            self._actor)
        for actor in self._actor_map.actors():
            if actor is self._actor: continue
            if actor.is_runner(): continue
            actor.freeze()
        self._actor.flush(Color.WHITE, interval=2, frame=60)
        return self

    def handle(self, controller, keyboard=None):
        self._actor_move(controller.pressed_keys())
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
        if 'skill' in down_keys: self._actor.use_skill()
        else: self._actor.unuse_skill()

class ReadyMode(PlayerHandler):
    def __init__(self, actor):
        self._actor = actor

    def handle(self, controller, keyboard=None):
        down_keys =  controller.pressed_keys()
        if 'start' not in down_keys: return
        SoundEffect.play_join()
        self.change_handle(self, WalkMode(self._actor).initialize())

class Chase(Game, MapHandler):
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
    runner = GameRunner(Chase())\
        .initialize_system()\
        .initialize_screen(640, 480, 16)\
        .initialize_controller(CONTROLLER_NUM, 'config.ini')\
        .set_font('Courier New', 18)\
        .set_fps(30)\
        .set_caption('*** Chase ***')
    runner.run()
