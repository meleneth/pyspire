#!/usr/bin/env python
from pyspire import Size, Vec2, PySpire, Sprite
from pyspire.animation import Bump, Sweep

# Simple registries
targets = {"sprites": {}, "indicators": {}}
sprites, indicators = targets["sprites"], targets["indicators"]

animation = PySpire(size=Size(1920, 1080), base_filename="output/cmake_animation")
animation.bus.on("animation.done", lambda **kw: setattr(animation, "done", True))

def make_sprite(sprite_name, bg_image, fg_image, position):
    s = animation.add_sprite(sprite_name)
    bg = s.add_image(bg_image)
    fg = s.add_image(fg_image)
    fg.center(bg)
    s.position = position
    sprites[sprite_name] = s
    return s

def compile_indicator_for(sprite):
    # Overlay layer we’ll “wipe” with Sweep
    image = sprite.add_image("compiling.png")
    sweep = Sweep(
        target=image,
        container_width=sprite.get_width(),
        duration_s=1.0,
    )
    animation.add_animation(sweep)
    return sweep

def make_bump(source, target):
    bump = Bump(source, target, forward_time_s=0.5, hold_time_s=0.1, return_time_s=0.5)
    animation.add_animation(bump)
    return bump

# Scene
make_sprite("gpp",              "program.png", "g++.png",              Vec2(50, 50))
make_sprite("main_src",         "source.png",  "main_src.png",         Vec2(50, 300))
make_sprite("secondary_src",    "source.png",  "secondary_src.png",    Vec2(50, 550))
make_sprite("secondary_header", "source.png",  "secondary_header.png", Vec2(800, 550))
make_sprite("some_program",     "source.png",  "secondary_header.png", Vec2(50, 800))

# predeclares for visibility
def on_main_src_paused(*, sprite: Sprite, sweep: Sweep):
    pass

def compile_secondary_source():
    pass

# **** -> **** g++ bumps main_src
initial_bump = make_bump(sprites["gpp"], sprites["main_src"])

# **** -> **** main_src compiles, pauses
def on_main_src_bump_contact(**kwargs):
    sweep = compile_indicator_for(sprites["main_src"])
    indicators['main_src'] = sweep
    sweep.queue_event_in(0.25 * 1.0, "pause_me", sprite=sprites["main_src"], sweep=sweep)
    sweep.bus.on("pause_me", lambda **kw: on_main_src_paused(**kw))
    sweep.bus.on("sweep_completed", lambda **kw: animation.bus.emit("animation.done"))

initial_bump.bus.on("bump_contact", on_main_src_bump_contact)

# **** -> **** main_src bumps secondary_header
def on_main_src_paused(*, sprite: Sprite, sweep: Sweep):
    bump = make_bump(sprite, sprites["secondary_header"])
    sweep.toggle_paused()
    sprite.replace_layer_image(2, "compile frozen.png")
    bump.bus.on("bump_contact", lambda **kw: compile_secondary_source(sprite, sweep))

# **** -> **** secondary_header compiles
def re_bump(sprite, bump_target, notify_target):
    bump = make_bump(sprite, bump_target)
    bump.bus.on("bump_completed", lambda **kw: notify_target.toggle_paused())

def compile_secondary_source(bump_target, notify_target):
    sweep = compile_indicator_for(sprites["secondary_header"])
    sweep.bus.on("sweep_completed", lambda **kw: re_bump(sprites["secondary_header"], bump_target, notify_target))

# **** -> **** secondary_header bumps main_src
# **** -> **** main_src finishes compiling
# **** -> **** main_src bumps secondary_src
# **** -> **** secondary_src compiles, pauses
# **** -> **** secondary_src bumps secondary_header
# **** -> **** secondary_header compiles
# **** -> **** secondary_header bumps secondary_src
# **** -> **** secondary_src spawns some_program
# **** -> **** secondary_src bumps some_program

animation.render_until_done()
