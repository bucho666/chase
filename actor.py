# -*- coding: utf-8 -*-
from pygameframework import Color
from pygameframework import Schedule
from sound import SoundEffect
from sprite import Sprite
from counter import Counter
from pygameframework import Direction

class ActorMap(object):
    def __init__(self):
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

    def remove_actor(self, actor):
        if not self.coordinate_of(actor): return
        coordinate = self._coordinate[actor]
        del self._actor[coordinate]
        del self._coordinate[actor]

class Actor(object):
    WAIT_TIME_MAX = 16
    WAIT_TIME_MIN = 0
    PLAYER_COLOR = (Color.RED, Color.AQUA, Color.YELLOW, Color.LIME)
    CHASER_GLYPH, RUNNER_GLYPH = ('&', '@')
    def __init__(self, player_id):
        self._sprite = Sprite(self.RUNNER_GLYPH, self.PLAYER_COLOR[player_id])
        self._status = Status()
        self._skill = InvisibleSkill(self._status)
        self._player_id = player_id + 1

    def reset(self):
        self._status = Status()
        self.be_runner()

    def __str__(self):
        return '%dP %s' % (self._player_id, str(self._status))

    def status(self):
        return self._status

    def life(self):
        return self._status.life()

    def render(self, screen, position):
        if self._status.is_invisible(): return
        self._sprite.render(screen, position)

    def render_status(self, screen, position):
        line = str(self._status)
        color = self._sprite.color()
        screen.write('[%sP] %s' % (self._player_id, line), position, color)

    def be_playing(self):
        self._status.be_playing()

    def is_playing(self):
        return self._status.is_playing()

    def is_dead(self):
        return self._status.is_dead()

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
        other.damage(10)
        other.freeze()

    def damage(self, value):
        self._status.damage(value)

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
    PLAYING, CHASER, WAIT, INVISIBLE, FORCE_VISIBLE = range(5)
    def __init__(self):
        self._properties = Property(
                [self.PLAYING, self.CHASER, self.WAIT, self.INVISIBLE, self.FORCE_VISIBLE])
        self._walk_wait_frame = 3
        self._life = 10

    def __str__(self):
        if self._properties.is_active(self.PLAYING):
            return 'Life: %-3d' % self._life
        return 'press start key'

    def life(self):
        return self._life

    def wait_walk_frame(self):
        self.wait(self._walk_wait_frame)

    def is_dead(self):
        return self._life is 0

    def damage(self, value):
        self._life -= value
        if self._life < 0: self._life = 0

    def be_playing(self):
        self._properties.set_properties(self.PLAYING)

    def is_playing(self):
        return self._properties.is_active(self.PLAYING)

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

class Actors(object):
    # TODO Rankingクラス作成
    _colors = (Color.YELLOW, Color.WHITE, Color.SILVER, Color.GRAY)

    def __init__(self, members):
        self._members = members

    def exists_deadman(self):
        for member in self._members:
            if member.is_dead():
                return True
        return False

    def reset(self):
        for member in self._members:
            member.reset()

    def render_ranking(self, screen, pos):
        for color, line in self.ranking_list():
            screen.write(line, pos, color,)
            pos += Direction.DOWN

    def ranking_list(self):
        # TODO クラス化？
        result = []
        tag = ('TOP', '2nd', '3rd', '4th')
        rank = 0
        current_life = None
        for member in sorted(self._members, key=lambda m: m.life(), reverse=True):
            if not member.is_playing(): continue
            life = member.life()
            if current_life is not None and current_life != life: rank += 1
            line = '[%s] %s' % (tag[rank], str(member))
            result.append((self._colors[rank], line))
            current_life = life
        return result

class Skill(object):
    def __init__(self, actor, interval):
        self._actor = actor
        self._active = False
        self._counter = Counter(interval)

    def active(self):
        if not self._active:
            self._apply()
            self._active = True
        self._counter.tick()
        if self._counter.is_over(): self._actor.damage(1)

    def inactive(self):
        self._not_apply()
        self._active = False
        self._counter.reset()

class InvisibleSkill(Skill):
    def __init__(self, actor):
        Skill.__init__(self, actor, 40)

    def _apply(self):
        self._actor.be_invisible()

    def _not_apply(self):
        self._actor.be_visible()

class DashSkill(Skill):
    def __init__(self, actor):
        Skill.__init__(self, actor, 40)

    def _apply(self):
        self._actor.running()

    def _not_apply(self):
        self._actor.walking()

class Flushing(object):
    def __init__(self, sprite, color, interval):
        self._sprite = sprite
        self._change_color = color
        self._frame_counter = Counter(interval)

    def update(self):
        self._frame_counter.tick()
        if not self._frame_counter.is_over(): return
        if self._sprite.color_changed():
            self._sprite.reset_color()
        else:
            self._sprite.change_color(self._change_color)

    def stop(self):
        self._sprite.reset_color()


