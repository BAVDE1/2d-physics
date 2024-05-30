import math
import time

from constants import *
from Vec2 import Vec2
from objects import Object


# todo: ripples spawned on object collision of water surface. Object velocity & mass affects ripple behaviour (strength, speed)
# todo: apply water force & drag on submerged object
# todo: have material density & object mass affect under-water forces


BASE_RIPPLE_SPEED = 15
BASE_SPEED_MUL = 4


class Ripple:
    """ Generates the block order that a ripple will travel (in both directions) """
    def __init__(self, strength: float, start_inx: int, max_inx: int, speed: float):
        self.strength: float = strength
        self.strength_decay: float = 0.98
        self.ripple_speed: float = 1 / speed

        self.start_inx: int = start_inx
        self.max_inx: int = max_inx

        self.generated_order: list = self.generate_order()
        self.on_ripple: int = -1

        self.strength_cut_off: float = 1

        self.last_progressed: float = time.time()
        self.accumulated_dt: float = 0

    def generate_order(self) -> list:
        """ Generates the order in which the ripple will travel. Returns list of indexes of the blocks """
        sn = self.start_inx
        li = [[sn]]  # first ripple already there
        for number in range(1, self.max_inx):
            rhs = sn + number
            lhs = sn - number
            seg = []
            if rhs < self.max_inx:
                seg.append(rhs)
            if lhs > -1:
                seg.append(lhs)
            if len(seg):
                li.append(seg)
        return li

    def get_next(self) -> list[int]:
        """ Get next blocks to add a ripple to """
        self.on_ripple += 1
        self.strength *= self.strength_decay

        num_blocks_left = len(self.generated_order)
        too_weak = self.strength < self.strength_cut_off
        val = None if num_blocks_left == 0 or too_weak else self.generated_order.pop(0)

        return [val, self.on_ripple]


class BlockSine:
    """ One ripple handled for one block """
    def __init__(self, strength):
        self.strength: float = strength

        self.started_time: float = time.time()
        self.max_time_alive: float = 0.8

    def get_sine(self):
        """ Return sine value for block """
        time_alive = time.time() - self.started_time
        time_left = self.max_time_alive - time_alive

        perc_completed = time_left / self.max_time_alive
        freq = 18 + (self.strength / 2)  # between 18 - 22
        sine = (self.strength * perc_completed) * math.sin(freq * time_alive)
        return sine if time_left >= 0 else None


class WaterBlock:
    def __init__(self, water, pos: Vec2, size: int, inx: int):
        self.water: Water = water
        self.inx: int = inx

        self.rect: pg.Rect = pg.Rect(pos.get(), [size] * 2)
        self.prev_rect: pg.Rect = self.rect.copy()
        self.og_display_rect: pg.Rect = pg.Rect(self.rect)

        margin: float = size * 1.5
        self.coll_bounds: pg.Rect = pg.Rect(self.rect.x, self.rect.y - margin / 2,
                                            self.rect.w, self.rect.h + margin)
        self.mouse_in: bool = False
        self.block_sines: list[BlockSine] = []
        self.max_sines: int = 10

    def new_sine(self, strength, offset):
        """ Create a fresh ripple for the block, places at start of list """
        if strength > 0 and len(self.block_sines) < self.max_sines:
            s = BlockSine(strength)
            s.started_time -= offset
            self.block_sines.insert(0, s)

    def update(self):
        self.prev_rect = self.rect
        new_r = pg.Rect(self.og_display_rect)

        # add sines to y pos
        for i, sine in enumerate(self.block_sines):
            val = sine.get_sine()
            if val is None:
                del self.block_sines[i]
                continue

            val = val / (i + 1)  # diminish older sines (so there's no insane stacking)
            new_r.y -= val
        self.rect = new_r

    def render(self, screen: pg.Surface):
        # display cube
        pg.draw.rect(screen, Colours.RED, self.coll_bounds)
        if self.prev_rect != self.rect:
            pg.draw.rect(screen, Colours.BLUE, self.prev_rect)  # behind block
        pg.draw.rect(screen, Colours.LIGHT_BLUE, self.rect)


class Water:
    def __init__(self, pos: Vec2, size: Vec2, block_size=4):
        margin = Vec2(0, 20)
        self.pos: Vec2 = pos
        self.size: Vec2 = size

        # loose collision bounds
        self.bounds_pos: Vec2 = pos.clone() - margin
        self.bounds_size: Vec2 = size.clone() + margin
        self.bounds_centre_pos: Vec2 = Vec2()
        self.bounds_bottom_right: Vec2 = Vec2()

        self.blocks_size: int = block_size
        self.blocks: list[WaterBlock] = self.generate_blocks()

        self.ripples: list[Ripple] = []
        self.queued_ripples: list[Ripple] = []
        self.max_ripples: int = 22
        self.allowed_ripple_rebound: int = 10  # allows rebound if less than x ripples exist

        self.re_scale_size()

    def re_scale_size(self):
        """ Re-scale the size of water & its re-calculate bounds """
        x_size = self.blocks_size * len(self.blocks)
        self.size.x = x_size
        self.bounds_size.x = x_size

        self.bounds_centre_pos = self.bounds_pos + self.bounds_size / 2
        self.bounds_bottom_right = self.bounds_pos + self.bounds_size

    def generate_blocks(self) -> list[WaterBlock]:
        """ Generates the blocks for the water, from left to right """
        li = []
        num_blocks = math.ceil(self.size.x / self.blocks_size)

        for i in range(num_blocks):
            pos = Vec2(self.pos.x + (self.blocks_size * i), self.pos.y)
            li.append(WaterBlock(self, pos, self.blocks_size, i))
        return li

    def create_ripple(self, block_inx: int, obj: Object):
        """ Calculate necessary values for the new ripple & add to queue if strong enough """

    def queue_ripple(self, block_inx: int, strength=5.0, speed: float = BASE_RIPPLE_SPEED):
        """ Add new ripple to the ripple queue. Inserts at beginning of queue """
        mul = BASE_SPEED_MUL + (BASE_SPEED_MUL - self.blocks_size)
        self.queued_ripples.insert(0, Ripple(strength, block_inx, len(self.blocks), speed * max(1, mul)))

    def update_ripple(self, ripple, ripple_inx, offset) -> bool:
        """ Progress ripple, giving sines and spawning rebound ripples if needed. Returns whether ripple was kept """
        ripple_nums, on_ripple = ripple.get_next()
        if ripple_nums is None:
            del self.ripples[ripple_inx]
            return False

        # give next block new ripple
        for inx in ripple_nums:
            self.blocks[inx].new_sine(ripple.strength, offset)

            # rebound ripple if few enough ripples exist (and not old enough)
            on_water_edge = (inx == 0 or inx == len(self.blocks) - 1)
            if on_ripple > 0 and len(self.ripples) < self.allowed_ripple_rebound and on_water_edge:
                self.queue_ripple(inx, ripple.strength)
        return True

    def update_all_ripples(self):
        """
        Progress every ripple
        Iterations are how many times the r should be progressed. Based on how much time since the r was last updated, and the r's speed.
        """
        for i, ripple in enumerate(self.ripples):
            ripple.accumulated_dt += time.time() - ripple.last_progressed
            iterations = math.floor(ripple.accumulated_dt / ripple.ripple_speed)

            for it in range(iterations):
                offset = ripple.ripple_speed * (iterations - it)
                if not self.update_ripple(ripple, i, offset):
                    break  # stop iterating if deleted

            ripple.last_progressed = time.time()
            ripple.accumulated_dt -= ripple.ripple_speed * iterations

    def add_queued_ripples(self):
        """ Add queued ripples to ripples list """
        if len(self.queued_ripples):
            self.ripples = self.queued_ripples + self.ripples
            self.queued_ripples.clear()

    def resolve_collision(self, obj: Object) -> tuple[bool, bool, bool, float]:
        """ Called when object is within the bounds of the water """
        is_touching = obj.is_touching_water
        is_submerged = is_point_in_rect(obj.pos, self.pos, self.pos + self.size)
        is_fully_submerged = obj.is_fully_submerged

        block_inx: int = math.floor((obj.pos.x - self.pos.x) / self.blocks_size)
        block: WaterBlock = self.blocks[clamp(block_inx, 0, len(self.blocks) - 1)]

        # check below object
        lower_point: Vec2 = obj.pos + Vec2(0, obj.get_radius())
        if lower_point.y > block.rect.top and not obj.is_touching_water and not is_submerged:
            is_touching = True
            self.create_ripple(block_inx, obj)
        elif lower_point.y < block.rect.top:
            is_touching = False

        # check above obj
        if is_submerged:
            upper_point: Vec2 = obj.pos - Vec2(0, obj.get_radius())
            if upper_point.y < block.rect.bottom and obj.is_fully_submerged:
                is_fully_submerged = False
                self.create_ripple(block_inx, obj)
            elif upper_point.y > block.rect.bottom:
                is_fully_submerged = True

        depth = clamp(obj.pos.y - self.pos.y, 0.0, self.size.y)
        return is_touching, is_submerged, is_fully_submerged, depth

    def check_collision(self, objects: list[Object]):
        """ Checks for objects near water and resolves collisions on nearby objects """
        for obj in objects:
            if not obj.static:
                is_touching = False
                is_submerged = False
                is_fully_submerged = False

                in_loose_bounds = is_point_in_rect(obj.pos, self.bounds_pos, self.bounds_bottom_right)

                if in_loose_bounds:
                    is_touching, is_submerged, is_fully_submerged, depth = self.resolve_collision(obj)
                    obj.water_depth = depth

                obj.is_touching_water = is_touching
                obj.is_submerged = is_submerged
                obj.is_fully_submerged = is_fully_submerged

    def update(self):
        for b in self.blocks:
            b.update()
        self.add_queued_ripples()
        self.update_all_ripples()

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, Colours.DARKER_GREY, pg.Rect(self.bounds_pos.get(), self.bounds_size.get()), 2)
        pg.draw.rect(screen, Colours.DARK_GREY, pg.Rect(self.pos.get(), self.size.get()), 2)
        for b in self.blocks:
            b.render(screen)
