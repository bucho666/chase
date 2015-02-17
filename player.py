# -*- coding: utf-8 -*-
from stage import StageHandler
from actor import ActorMap
from sound import SoundEffect
from pygameframework import Color
from pygameframework import Direction

class PlayerHandler(object):
    (READY, WALK) = range(2)
    _handlers = []
    _handle_map = dict()

    @classmethod
    def initialize(cls, actor_list):
        cls._handle_map[cls.READY] = [ReadyMode(actor) for actor in actor_list]
        cls._handle_map[cls.WALK] = [WalkMode(actor) for actor in actor_list]
        cls._handlers = list(cls._handle_map[cls.READY])

    @classmethod
    def reset(cls):
        for handler in cls._handlers:
            handler.change_ready_mode()

    @classmethod
    def update(cls, controllers, keyboard):
        for handler, controller in zip(cls._handlers, controllers):
            handler.handle(controller, keyboard)

    def change_ready_mode(self):
        self._change_handle(PlayerHandler.READY)

    def change_walk_mode(self):
        self._change_handle(PlayerHandler.WALK)

    def _change_handle(self, new_handle_id):
        for i, handle in enumerate(PlayerHandler._handlers):
            if handle != self: continue
            PlayerHandler._handlers[i] = PlayerHandler._handle_map[new_handle_id][i]
            PlayerHandler._handlers[i].initialize()
            break

class WalkCommand(StageHandler):
    def __init__(self, actor):
        StageHandler.__init__(self)
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

class WalkMode(PlayerHandler, StageHandler):
    def __init__(self, actor):
        StageHandler.__init__(self)
        self._actor = actor
        self._walk = WalkCommand(actor)

    def initialize(self):
        if self._actor_map.count_actors() is 0:
            self._actor.be_chaser()
        if self._actor_map.count_actors() is 1:
            SoundEffect.play_bgm()
        self._actor_map.put(self.choice_random_open_coordinate(), self._actor)
        for actor in self._actor_map.actors():
            if actor is self._actor: continue
            if not actor.is_chaser(): continue
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
        # TODO ChaiserのLifeを一定間隔で下落させる。

class ReadyMode(PlayerHandler, StageHandler):
    def __init__(self, actor):
        self._actor = actor

    def initialize(self):
        StageHandler.remove_actor(self._actor)

    def handle(self, controller, keyboard=None):
        down_keys =  controller.down_keys()
        if 'start' not in down_keys: return
        SoundEffect.play_join()
        self._actor.be_playing()
        self.change_walk_mode()
