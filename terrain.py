# -*- coding: utf-8 -*-
from pygameframework import AsciiTileSheet
from pygameframework import Color
from pygameframework import Coordinate
from tile import AsciiTileLocator

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
