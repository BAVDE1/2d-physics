import math
import time

from constants import *
from Vec2 import Vec2
from objects import Object


# done: ripples spawned on object collision of water surface. Object velocity & mass affects ripple behaviour (strength, speed)
# todo: apply water force & drag on submerged object
# todo: have material density & object mass affect under-water forces


MIN_RIPPLE_SPEED = 8.0
BASE_RIPPLE_SPEED = 15.0
BASE_SPEED_MUL = 4.0

MAX_VEL_LENGTH = 250.0
MAX_MASS = 1000
MIN_STRENGTH = 2.0
MAX_STRENGTH = 5.0


class Ripple:
    """ Generates the block order that a ripple will travel (in both directions) """
    def __init__(self, strength: float, start_inx: int, max_inx: int, speed: float, direction: int):
        self.direction: int = direction  # < -1, < 0 >, 1 >
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

        margin: float = size * 1
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

        self.a = None
        self.b = None

    def re_scale_size(self):
        """ Re-scale the size of water based on num of blocks generated & its re-calculate bounds """
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

    def create_ripple(self, block_inx: int, obj: Object, moving_horizontal: bool = False):
        """ Calculate necessary values for the new ripple & spawn if strong enough """
        bias_velocity = Vec2(obj.velocity.x / 2, obj.velocity.y)  # more dependant on y
        strength: float = (min(bias_velocity.length(), MAX_VEL_LENGTH) / MAX_VEL_LENGTH) * 10.0
        strength_threshold = 0.5
        if moving_horizontal:
            strength_threshold *= 2  # more velocity required to ripple

        # skip if too little velocity
        if strength < strength_threshold:
            return

        direction = 0
        mass_perc = min(obj.mass, MAX_MASS) / MAX_MASS  # mass / max mass
        min_strength = float(MIN_STRENGTH)
        max_strength = float(MAX_STRENGTH)
        if moving_horizontal:  # reduce strength
            min_strength -= 1
            max_strength -= (3 - (mass_perc * 3))

        strength: float = clamp(strength, min_strength, max_strength)
        speed: float = MIN_RIPPLE_SPEED + (strength * 2) - (2 - mass_perc * 2)

        # offset ripple starting point
        if moving_horizontal:
            y = self.pos.y - obj.pos.y
            x = -(obj.get_radius() - abs(y))
            on_radius: Vec2 = Vec2(x, y).normalise_self(x_only=True)
            on_radius.x *= obj.get_radius()

            direction = int((obj.velocity.x > 0) * 2 - 1)  # set direction: -1 or 1
            if direction > 0:  # flip side
                on_radius.x = -on_radius.x

            block_inx = self.get_block_index(obj.pos.x + on_radius.x)
        self.queue_ripple(block_inx, strength=strength, speed=speed, direction=direction)

    def queue_ripple(self, block_inx: int, strength=MAX_STRENGTH, speed=BASE_RIPPLE_SPEED, direction=0):
        """ Add new ripple to the ripple queue. Inserts at beginning of queue """
        sp_mul = BASE_SPEED_MUL + (BASE_SPEED_MUL - self.blocks_size)
        self.queued_ripples.insert(0, Ripple(strength, block_inx, len(self.blocks), speed * max(1.0, sp_mul), direction))

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

    def get_block_index(self, x: float):
        """ Get block index on x pos """
        inx = math.floor((x - self.pos.x) / self.blocks_size)
        return clamp(inx, 0, len(self.blocks) - 1)

    def resolve_collision(self, obj: Object) -> tuple[bool, bool, bool, float]:
        """ Called when object is within the loose bounds of the water """
        has_sent_ripple = False
        is_touching = obj.is_touching_water
        is_submerged = is_point_in_rect(obj.pos, self.pos, self.pos + self.size)
        is_fully_submerged = obj.is_fully_submerged

        block_inx: int = self.get_block_index(obj.pos.x)
        block: WaterBlock = self.blocks[clamp(block_inx, 0, len(self.blocks) - 1)]
        top: float = block.coll_bounds.top
        btm: float = block.coll_bounds.bottom

        # check below object
        lower: float = obj.pos.y + obj.get_radius()
        if lower > top and not is_touching and not is_submerged:
            is_touching = has_sent_ripple = True
            self.create_ripple(block_inx, obj)
        elif lower < top:
            is_touching = False

        # check above obj if pos below surface
        if not has_sent_ripple and is_submerged:
            upper: float = obj.pos.y - obj.get_radius()
            if upper < btm and is_fully_submerged:
                is_fully_submerged = has_sent_ripple = False
                self.create_ripple(block_inx, obj)
            elif upper > btm:
                is_touching = is_fully_submerged = True

        # object in water surface (moving horizontally)
        if not has_sent_ripple and (is_touching or is_submerged) and not is_fully_submerged:
            self.create_ripple(block_inx, obj, moving_horizontal=True)

        depth = clamp(obj.pos.y - self.pos.y, 0.0, self.size.y)
        return is_touching, is_submerged, is_fully_submerged, depth

    def check_collision(self, objects: list[Object]):
        """ Checks for objects near water and resolves collisions on nearby objects """
        for obj in objects:
            if not obj.static:
                is_touching = is_submerged = is_fully_submerged = False
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

        self.update_all_ripples()
        self.add_queued_ripples()

    def render(self, screen: pg.Surface):
        pg.draw.rect(screen, Colours.DARKER_GREY, pg.Rect(self.bounds_pos.get(), self.bounds_size.get()), 2)
        pg.draw.rect(screen, Colours.DARK_GREY, pg.Rect(self.pos.get(), self.size.get()), 2)
        for b in self.blocks:
            b.render(screen)
        if self.a and self.b:
            pg.draw.line(screen, Colours.RED, self.a.get(), (self.a + self.b).get())
