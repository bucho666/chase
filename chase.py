# -*- coding: utf-8 -*-
from pygameframework import Game
from pygameframework import GridWindow
from pygameframework import AsciiTileSheet
from pygameframework import Coordinate
from pygameframework import Key
import sys
from tile import AsciiTileLocator
from terrain import TerrainMapHandler
from actor import Actor
from actor import Actors
from scene import Scene
from scene import RankingScene
from scene import ChaceScene
from stage import StageHandler
from player import PlayerHandler

class StatusWindow(object):
    def __init__(self, actors, position):
        self._actors = actors
        self._position = position

    def render(self, window):
        x, y = self._position.xy()
        for index, actor in enumerate(self._actors):
            actor.render_status(window, Coordinate(x, index+y))

    def add(self, status):
        self._status.append(status)

class Chase(Game, StageHandler):
    POSITION = Coordinate(0, 0)
    GRID_SIZE = Coordinate(10, 18)
    MAX_PLAYER = 4
    def __init__(self):
        Game.__init__(self)
        StageHandler.__init__(self)
        self._screen = None

    def initialize(self, screen):
        tile_sheet = AsciiTileSheet().initialize('Courier New', 18)
        AsciiTileLocator.provide(tile_sheet)
        StageHandler.initialize()
        TerrainMapHandler.load('data/map.data')
        actor_list = [Actor(player_id) for player_id in range(self.MAX_PLAYER)]
        PlayerHandler.initialize(actor_list)
        status_window = StatusWindow(
                [actor for actor in actor_list],\
                Coordinate(0, 18))
        self._screen = window = GridWindow(screen, self.POSITION, self.GRID_SIZE)
        actors = Actors(actor_list)
        Scene.register_chase_scene(ChaceScene(status_window, actors))
        Scene.register_ranking_scene(RankingScene(actors))
        Scene.change_chase_scene()

    def update(self):
        if Key.ESCAPE in self._keyboard.pressed_keys(): sys.exit()
        Scene.update(self._controllers, self._keyboard)

    def render(self):
        Scene.render(self._screen)

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
