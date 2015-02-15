# -*- coding: utf-8 -*-
class AsciiTileLocator(object):
    sheet = None
    @classmethod
    def provide(cls, new_sheet):
        cls.sheet = new_sheet

    @classmethod
    def get_tile(cls, glyph, color):
        return cls.sheet.get_tile(glyph, color)
