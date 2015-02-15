# -*- coding: utf-8 -*-
import random
from terrain import TerrainMapHandler
from actor import ActorMap

class StageHandler(TerrainMapHandler):
    _actor_map = None

    @classmethod
    def initialize(cls):
        TerrainMapHandler.initialize()
        cls._actor_map = ActorMap()

    def choice_random_open_coordinate(self):
       return random.choice([c for c in self._terrain_map.walkable_coordinates()\
               if not self._actor_map.actor(c)])

    @classmethod
    def remove_actor(cls, actor):
        cls._actor_map.remove_actor(actor)

