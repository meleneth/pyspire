#!/usr/bin/env python
from enum import Enum

from pyspire import Size, Vec2, PySpire, Sprite
from pyspire.animation import Bump, Sweep, Fade

# Simple registries
targets = {"sprites": {}, "indicators": {}}
sprites, indicators = targets["sprites"], targets["indicators"]

TIMING_SWEEP=1.0
TIMING_SWEEP_PAUSE=0.25
TIMING_FADE=1.5
TIMING_BUMP_FWD=0.5
TIMING_BUMP_HOLD=0.1
TIMING_BUMP_RETURN=0.5

class Layer(Enum):
    BACKGROUND=0
    DIRTY_INDICATOR=1
    TEXT=2
    COMPILING=3

#animation = PySpire(size=Size(1920, 1080), base_filename="output/cmake_animation")
animation = PySpire(size=Size(3840, 2160), base_filename="output/cmake_animation")
animation.bus.on("animation.done", lambda **kw: setattr(animation, "done", True))

def make_program_sprite(sprite_name, bg_image, fg_image, position):
    s = animation.add_sprite(sprite_name)
    bg = s.add_image(bg_image)
    fg = s.add_image(fg_image)
    fg.center(bg)
    s.position = position
    sprites[sprite_name] = s
    return s

def make_src_sprite(sprite_name, bg_image, dirty_image, fg_image, position):
    s = animation.add_sprite(sprite_name)
    bg = s.add_image(bg_image)
    dirty = s.add_image(dirty_image)
    s.layers[Layer.DIRTY_INDICATOR.value].opacity = 1.0
    fg = s.add_image(fg_image)
    fg.center(bg)
    s.position = position
    sprites[sprite_name] = s
    return s

def compile_indicator_for(sprite: Sprite) -> Sweep:
    # Overlay layer we’ll “wipe” with Sweep
    image = sprite.add_image("compiling.png")
    sweep = Sweep(
        target=image,
        container_width=sprite.get_width(),
        duration_s=TIMING_SWEEP,
    )
    animation.add_animation(sweep)
    return sweep

def make_bump(source: Sprite, target: Sprite) -> Bump:
    bump = Bump(source, target,
                forward_time_s=TIMING_BUMP_FWD,
                hold_time_s=TIMING_BUMP_HOLD,
                return_time_s=TIMING_BUMP_RETURN)
    animation.add_animation(bump)
    return bump

# ---------------- Scene ----------------
make_src_sprite("secondary_header", "source.png", "dirty.png", "secondary_header.png", Vec2(800, 550))
make_src_sprite("main_src",         "source.png", "dirty.png", "main_src.png",         Vec2(50, 300))
make_src_sprite("secondary_src",    "source.png", "dirty.png", "secondary_src.png",    Vec2(50, 550))
make_src_sprite("test_src",         "source.png", "dirty.png", "test_some_src.png",    Vec2(50, 800))

make_program_sprite("some_lib", "library.png", "some_archive.png",      Vec2(2300, 550))
sprites["some_lib"].opacity = 0.0

make_program_sprite("secondary_object", "object.png",  "secondary_object.png", Vec2(1550, 550))
make_program_sprite("test_object",      "object.png",  "some_test_object.png", Vec2(1550, 800))
make_program_sprite("main_object",      "object.png",  "main_object.png",      Vec2(1550, 300))
sprites["main_object"].opacity = 0.0
sprites["secondary_object"].opacity = 0.0
sprites["test_object"].opacity = 0.0

make_program_sprite("gpp",          "program.png", "g++.png",               Vec2(50, 50))
make_program_sprite("some_program", "program.png", "some_program.png",      Vec2(1550, 1050))
make_program_sprite("test_some",    "program.png", "some_test_program.png", Vec2(2300, 1050))
sprites["some_program"].opacity = 0.0
sprites["test_some"].opacity = 0.0

# ---------------- Helpers / predeclares ----------------
def on_main_src_paused(*, sprite: Sprite, sweep: Sweep):
    # main_src bumps secondary_header while its compile is paused
    bump = make_bump(sprite, sprites["secondary_header"])
    sweep.toggle_paused()
    sprite.replace_layer_image(Layer.COMPILING.value, "compile frozen.png")
    bump.bus.on("bump_contact", lambda **kw: compile_secondary_source(sprite, sweep))

def re_bump(sprite_from: Sprite, bump_target: Sprite, notify_target: Sweep):
    # secondary_header bumps back to resume the paused compile
    bump = make_bump(sprite_from, bump_target)
    bump.bus.on("bump_completed", lambda **kw: notify_target.toggle_paused())
    bump.bus.on("bump_completed", lambda **kw: bump_target.replace_layer_image(Layer.COMPILING.value, "compiling.png"))

def compile_secondary_source(bump_target: Sprite, notify_target: Sweep):
    # secondary_header compiles, then bumps back and unpauses notify_target
    sweep = compile_indicator_for(sprites["secondary_header"])
    sweep.bus.on(
        "sweep_completed",
        lambda **kw: re_bump(sprites["secondary_header"], bump_target, notify_target),
    )
    sweep.bus.on("sweep_completed", lambda **kw: animation.add_animation(
                        Fade(
                            target=sprites['secondary_header'].layers[Layer.DIRTY_INDICATOR.value],
                            duration_s=TIMING_FADE,
                            end=0.0
                        )
                    )
                )
    sweep.bus.on("sweep_completed", lambda **kw: sprites["secondary_header"].layers.pop(Layer.COMPILING.value))

# ---------------- Act 1: g++ -> secondary_src  ----------------
initial_bump = make_bump(sprites["gpp"], sprites["secondary_src"])
initial_bump.bus.on("bump_contact", lambda **kw: on_secondary_src_bump_contact())

def on_secondary_src_bump_contact():
    # **** secondary_src compiles, pauses
    sweep = compile_indicator_for(sprites["secondary_src"])
    indicators["secondary_src"] = sweep
    sweep.queue_event_in(TIMING_SWEEP_PAUSE, "pause_me", sprite=sprites["secondary_src"], sweep=sweep)
    sweep.bus.on("pause_me", lambda **kw: on_secondary_src_paused(**kw))
    sweep.bus.on("sweep_completed", lambda **kw: on_secondary_src_compile_completed())
    sweep.bus.on("sweep_completed", lambda **kw: sprites["secondary_src"].layers.pop(Layer.COMPILING.value))

def on_secondary_src_paused(*, sprite: Sprite, sweep: Sweep):
    # **** secondary_src bumps secondary_header (while paused)
    bump = make_bump(sprite, sprites["secondary_header"])
    sweep.toggle_paused()
    sprite.replace_layer_image(Layer.COMPILING.value, "compile frozen.png")
    bump.bus.on("bump_contact", lambda **kw: compile_secondary_source(sprite, sweep))

def on_secondary_src_compile_completed():
    # **** secondary_header compiles (handled in compile_secondary_source)
    # **** secondary_header bumps secondary_src (handled in re_bump)
    # **** secondary_src spawns secondary_object
    # **** next up, g++ bumps secondary_object to make some.a
    fade = Fade(target=sprites['secondary_src'].layers[Layer.DIRTY_INDICATOR.value], duration_s=TIMING_FADE, end=0.0)
    animation.add_animation(fade)
    bump = make_bump(sprites["secondary_src"], sprites["secondary_object"])
    bump.bus.on("bump_contact", lambda **kw: on_secondary_object_bump_contact())

def on_secondary_object_bump_contact():
    fade = Fade(target=sprites['secondary_object'], duration_s=TIMING_FADE)
    animation.add_animation(fade)
    fade.bus.on("fade_completed", lambda **kw: on_secondary_object_fade_in_completed())

def on_secondary_object_fade_in_completed():
    bump = make_bump(sprites["gpp"], sprites["secondary_object"])
    bump.bus.on("bump_contact", lambda **kw: on_main_object_bump_contact_create_archive())

def on_main_object_bump_contact_create_archive():
    bump = make_bump(sprites["secondary_object"], sprites["some_lib"])
    bump.bus.on("bump_contact", lambda **kw: on_some_lib_bump_contact())

def on_some_lib_bump_contact():
    fade = Fade(target=sprites['some_lib'], duration_s=TIMING_FADE, start=0.0, end=1.0)
    animation.add_animation(fade)
    fade.bus.on("fade_completed", lambda **kw: on_some_lib_fade_in_completed())

def on_some_lib_fade_in_completed():
    bump = make_bump(sprites["gpp"], sprites["main_src"])
    bump.bus.on("bump_contact", lambda **kw: on_main_src_bump_contact())

def on_main_src_bump_contact(**kwargs):
    sweep = compile_indicator_for(sprites["main_src"])
    indicators["main_src"] = sweep
    # quarter-way pause, then bounce to header and back, then finish compiling
    sweep.queue_event_in(0.25 * 1.0, "pause_me", sprite=sprites["main_src"], sweep=sweep)
    sweep.bus.on("pause_me", lambda **kw: on_main_src_paused(**kw))
    sweep.bus.on("sweep_completed", lambda **kw: on_main_src_compile_completed())
    sweep.bus.on("sweep_completed", lambda **kw: sprites["main_src"].layers.pop(Layer.COMPILING.value))

def on_main_src_compile_completed():
    # **** main_src finishes compiling
    # **** main_src bumps secondary_src
    fade = Fade(target=sprites['main_src'].layers[Layer.DIRTY_INDICATOR.value], duration_s=TIMING_FADE, end=0.0)
    animation.add_animation(fade)
    bump = make_bump(sprites["main_src"], sprites["main_object"])
    bump.bus.on("bump_contact", lambda **kw: on_main_object_bump_contact_compiled())

def on_main_object_bump_contact_compiled():
    fade = Fade(target=sprites['main_object'], duration_s=TIMING_FADE, end=1.0)
    animation.add_animation(fade)
    fade.bus.on("fade_completed", lambda **kw: on_main_object_fade_in_completed())

def on_main_object_fade_in_completed():
    bump = make_bump(sprites["gpp"], sprites["main_object"])
    bump.bus.on("bump_contact", lambda **kw: on_some_lib_bump_contact_link_phase())

def on_some_lib_bump_contact_link_phase():
    bump = make_bump(sprites["some_lib"], sprites["some_program"])
    bump = make_bump(sprites["main_object"], sprites["some_program"])
    bump.bus.on("bump_contact", lambda **kw: fade_in_some_program())

def fade_in_some_program():
    fade = Fade(target=sprites['some_program'], duration_s=TIMING_FADE)
    animation.add_animation(fade)
    fade.bus.on("fade_completed", lambda **kw: compile_test_object())

def compile_test_object():
    bump = make_bump(sprites["gpp"], sprites["test_src"])
    bump.bus.on("bump_contact", lambda **kw: compile_test_src_bumped())

def compile_test_src_bumped():
    sweep = compile_indicator_for(sprites["test_src"])
    indicators["test_src"] = sweep
    # quarter-way pause, then bounce to header and back, then finish compiling
    sweep.queue_event_in(0.25 * 1.0, "pause_me", sprite=sprites["test_src"], sweep=sweep)
    sweep.bus.on("pause_me", lambda **kw: on_test_src_paused(**kw))
    sweep.bus.on("sweep_completed", lambda **kw: on_test_src_compile_completed())
    sweep.bus.on("sweep_completed", lambda **kw: sprites["test_src"].layers.pop(Layer.COMPILING.value))

def on_test_src_paused(*, sprite: Sprite, sweep: Sweep):
    # **** secondary_src bumps secondary_header (while paused)
    bump = make_bump(sprite, sprites["secondary_header"])
    sweep.toggle_paused()
    sprite.replace_layer_image(Layer.COMPILING.value, "compile frozen.png")
    bump.bus.on("bump_contact", lambda **kw: compile_secondary_source(sprite, sweep))

def on_test_src_compile_completed():
    bump = make_bump(sprites["test_src"], sprites["test_object"])
    bump.bus.on("bump_completed", lambda **kw: link_test_executable())
    bump.bus.on("bump_contact", lambda **kw: create_test_object())
    fade = Fade(target=sprites['test_src'].layers[Layer.DIRTY_INDICATOR.value], duration_s=TIMING_FADE, end=0.0)
    animation.add_animation(fade)

def create_test_object():
    fade = Fade(target=sprites['test_object'], duration_s=TIMING_FADE, start = 0.0, end=1.0)
    animation.add_animation(fade)

def link_test_executable():
    bump = make_bump(sprites["gpp"], sprites["test_object"])
    bump.bus.on("bump_completed", lambda **kw: create_test_executable())

def create_test_executable():
    bump = make_bump(sprites["test_object"], sprites["test_some"])
    bump = make_bump(sprites["some_lib"], sprites["test_some"])
    bump.bus.on("bump_completed", lambda **kw: fade_in_test_executable())

def fade_in_test_executable():
    fade = Fade(target=sprites['test_some'], duration_s=TIMING_FADE)
    animation.add_animation(fade)
    fade.bus.on("fade_completed", lambda **kw: animation.bus.emit("animation.done"))
# Go.
animation.render_until_done()
