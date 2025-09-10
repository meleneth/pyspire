#!/usr/bin/env python
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

animation = PySpire(size=Size(3840, 2160), base_filename="output/cmake_animation")
animation.bus.on("animation.done", lambda **kw: setattr(animation, "done", True))

def make_sprite(sprite_name, bg_image, fg_image, position):
    s = animation.add_sprite(sprite_name)
    bg = s.add_image(bg_image)
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
make_sprite("gpp",              "program.png", "g++.png",              Vec2(50, 50))
make_sprite("main_src",         "source.png",  "main_src.png",         Vec2(50, 300))
make_sprite("secondary_src",    "source.png",  "secondary_src.png",    Vec2(50, 550))
make_sprite("secondary_header", "source.png",  "secondary_header.png", Vec2(800, 550))
make_sprite("some_program",     "program.png",  "some_program.png",     Vec2(50, 800))
sprites["some_program"].opacity = 0.0

# ---------------- Helpers / predeclares ----------------
def on_main_src_paused(*, sprite: Sprite, sweep: Sweep):
    # main_src bumps secondary_header while its compile is paused
    bump = make_bump(sprite, sprites["secondary_header"])
    sweep.toggle_paused()
    sprite.replace_layer_image(2, "compile frozen.png")
    bump.bus.on("bump_contact", lambda **kw: compile_secondary_source(sprite, sweep))

def re_bump(sprite_from: Sprite, bump_target: Sprite, notify_target: Sweep):
    # secondary_header bumps back to resume the paused compile
    bump = make_bump(sprite_from, bump_target)
    bump.bus.on("bump_completed", lambda **kw: notify_target.toggle_paused())
    bump.bus.on("bump_completed", lambda **kw: bump_target.replace_layer_image(2, "compiling.png"))

def compile_secondary_source(bump_target: Sprite, notify_target: Sweep):
    # secondary_header compiles, then bumps back and unpauses notify_target
    sweep = compile_indicator_for(sprites["secondary_header"])
    sweep.bus.on(
        "sweep_completed",
        lambda **kw: re_bump(sprites["secondary_header"], bump_target, notify_target),
    )
    sweep.bus.on("sweep_completed", lambda **kw: sprites["secondary_header"].layers.pop(2))

# ---------------- Act 1: g++ -> main_src ----------------
initial_bump = make_bump(sprites["gpp"], sprites["main_src"])

def on_main_src_bump_contact(**kwargs):
    sweep = compile_indicator_for(sprites["main_src"])
    indicators["main_src"] = sweep
    # quarter-way pause, then bounce to header and back, then finish compiling
    sweep.queue_event_in(0.25 * 1.0, "pause_me", sprite=sprites["main_src"], sweep=sweep)
    sweep.bus.on("pause_me", lambda **kw: on_main_src_paused(**kw))
    sweep.bus.on("sweep_completed", lambda **kw: on_main_src_compile_completed())
    sweep.bus.on("sweep_completed", lambda **kw: sprites["main_src"].layers.pop(2))

initial_bump.bus.on("bump_contact", on_main_src_bump_contact)

def on_main_src_compile_completed():
    # **** main_src finishes compiling
    # **** main_src bumps secondary_src
    bump = make_bump(sprites["main_src"], sprites["secondary_src"])
    bump.bus.on("bump_contact", lambda **kw: on_secondary_src_bump_contact())

# ---------------- Act 2: main_src -> secondary_src ----------------
def on_secondary_src_bump_contact():
    # **** secondary_src compiles, pauses
    sweep = compile_indicator_for(sprites["secondary_src"])
    indicators["secondary_src"] = sweep
    sweep.queue_event_in(TIMING_SWEEP_PAUSE, "pause_me", sprite=sprites["secondary_src"], sweep=sweep)
    sweep.bus.on("pause_me", lambda **kw: on_secondary_src_paused(**kw))
    sweep.bus.on("sweep_completed", lambda **kw: on_secondary_src_compile_completed())
    sweep.bus.on("sweep_completed", lambda **kw: sprites["secondary_src"].layers.pop(2))

def on_secondary_src_paused(*, sprite: Sprite, sweep: Sweep):
    # **** secondary_src bumps secondary_header (while paused)
    bump = make_bump(sprite, sprites["secondary_header"])
    sweep.toggle_paused()
    sprite.replace_layer_image(2, "compile frozen.png")
    bump.bus.on("bump_contact", lambda **kw: compile_secondary_source(sprite, sweep))

def on_secondary_src_compile_completed():
    # **** secondary_header compiles (handled in compile_secondary_source)
    # **** secondary_header bumps secondary_src (handled in re_bump)
    # **** secondary_src spawns some_program (already present; treat as "activated")
    # **** secondary_src bumps some_program
    bump = make_bump(sprites["secondary_src"], sprites["some_program"])
    bump.bus.on("bump_contact", lambda **kw: fade_in_some_program())

def fade_in_some_program():
    fade = Fade(target=sprites['some_program'], duration_s=TIMING_FADE)
    animation.add_animation(fade)
    fade.bus.on("fade_completed", lambda **kw: animation.bus.emit("animation.done"))

# Go.
animation.render_until_done()
