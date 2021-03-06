# -*- coding: utf-8 -*-
from pygameframework import Color
from pygameframework import Coordinate
from stage import StageHandler
from player import PlayerHandler
from pygameframework import Scheduler

class Scene(object):
    (TITLE, CHASE, RANKING) = range(3)
    _active_scene = None
    _scenes = dict()

    @classmethod
    def register_title_scene(cls, scene):
        cls._scenes[cls.TITLE] = scene

    @classmethod
    def register_chase_scene(cls, scene):
        cls._scenes[cls.CHASE] = scene

    @classmethod
    def register_ranking_scene(cls, scene):
        cls._scenes[cls.RANKING] = scene

    @classmethod
    def change_title_scene(cls):
        cls.change_scene(cls._scenes[cls.TITLE])

    @classmethod
    def change_chase_scene(cls):
        cls.change_scene(cls._scenes[cls.CHASE])

    @classmethod
    def change_ranking_scene(cls):
        cls.change_scene(cls._scenes[cls.RANKING])

    @classmethod
    def change_scene(cls, new_scene):
        cls._active_scene = new_scene
        Scheduler.clear()

    @classmethod
    def render(cls, screen):
        cls._active_scene.render(screen)

    @classmethod
    def update(cls, controller, keyboard):
        cls._active_scene.update(controller, keyboard)

class TitleScene(Scene):
    def render(self, screen):
        screen.fill()
        screen.write('Chaise', Coordinate(0, 0), Color.OLIVE)

    def update(self, controllers, keyboard):
        colors = (Color.YELLOW, Color.GREEN, Color.BLUE, Color.RED)
        for controller in controllers:
            down_keys = controller.down_keys()
            if not down_keys: continue
            Scene.change_chase_scene()

class RankingScene(Scene):
    def __init__(self, actors):
        self._actors = actors
        self._ranking = actors.ranking()

    def render(self, screen):
        screen.fill()
        screen.write('Ranking', Coordinate(0, 0), Color.OLIVE)
        self._ranking.render(screen, Coordinate(0, 2))
        screen.write('Press [Start]+[Skill] Key', Coordinate(0, 10), Color.YELLOW)

    def update(self, controllers, keyboard):
        for controller in controllers:
            down_keys = controller.pressed_keys()
            if set(['start', 'skill']) != down_keys: continue
            self._actors.reset()
            PlayerHandler.reset()
            Scene.change_chase_scene()

class ChaceScene(StageHandler, Scene):
    def __init__(self, status_window, actors):
        StageHandler.__init__(self)
        self._status_window = status_window
        self._actors = actors

    def update(self, controllers, keyboard):
        PlayerHandler.update(controllers, keyboard)
        if self._actors.exists_deadman():
            Scene.change_ranking_scene()

    def render(self, screen):
        screen.fill()
        self._terrain_map.render(screen)
        self._actor_map.render(screen)
        self._status_window.render(screen)
