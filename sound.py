# -*- coding: utf-8 -*-
from pygameframework import Sound

class SoundEffect(object):
    @classmethod
    def play_touch(cls):
        Sound.play('data/touch.ogg')

    @classmethod
    def play_join(cls):
        Sound.play('data/join.ogg')

    @classmethod
    def play_bgm(cls):
        Sound.play_bgm('data/bgm.ogg')
