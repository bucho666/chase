# -*- coding: utf-8 -*-
from tile import AsciiTileLocator

class Sprite(object):
    def __init__(self, glyph, color):
        self._graphic = AsciiTileLocator.get_tile(glyph, color)
        self._glyph = glyph
        self._color = color
        self._original_color = color

    def color(self):
        return self._color

    def render(self, screen, position):
        screen.draw(position, self._graphic)

    def change_color(self, new_color):
        self._color = new_color
        self._update()

    def color_changed(self):
        return self._original_color != self._color

    def reset_color(self):
        self.change_color(self._original_color)

    def change_glyph(self, new_glyph):
        self._glyph = new_glyph
        self._update()

    def _update(self):
        self._graphic = AsciiTileLocator.get_tile(self._glyph, self._color)




