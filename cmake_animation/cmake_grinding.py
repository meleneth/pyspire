#!/usr/bin/env python

from pyspire import Size, Vec2, PySpire
from pyspire.animation import BumpAnimation
from pyspire.animation import BumpAnimationPlayer

targets = {
    "sprites": {}, "indicators": {}
}

sprites = targets["sprites"]
indicators = targets["indicators"]

animation = PySpire(size=Size(1920, 1080), base_filename="output/cmake_animation")

def make_sprite(sprite_name, bg_image, fg_image, position):
    new_sprite = animation.add_sprite(sprite_name)
    bg_layer = new_sprite.add_image(bg_image)
    text_layer = new_sprite.add_image(fg_image)
    text_layer.center(bg_layer)
    new_sprite.position = position
    sprites[sprite_name] = new_sprite
    return new_sprite

def compile_indicator_for(sprite):
    compile_sprite = animation.add_sprite("compile_sprite")
    compile_layer  = compile_sprite.add_image("compiling.png")
    compile_sprite.position = Vec2(sprite.x, sprite.y)
    return compile_sprite

make_sprite("gpp_sprite",              "program.png", "g++.png",              Vec2(50, 50))
make_sprite("main_src_sprite",         "source.png",  "main_src.png",         Vec2(50, 300))
make_sprite("secondary_src_sprite",    "source.png",  "secondary_src.png",    Vec2(50, 550))
make_sprite("secondary_header_sprite", "source.png",  "secondary_header.png", Vec2(800, 550))
make_sprite("some_program_sprite",     "source.png",  "secondary_header.png", Vec2(50, 800))

def finished_handler(payload):
    animation.done = True

def make_bump(source, target, bus):
    bump = BumpAnimation(
        source, target, bus=bus,
        fps=60, forward_time_s=0.5, hold_time_s=0.1, return_time_s=0.5,
    )
    bump_player = BumpAnimationPlayer(bump)
    animation.add_animation(bump_player)
    return bump

def main_src_bump_handler(payload):
    indicators["main_src_compile"] = compile_indicator_for(sprites["main_src_sprite"])
    make_bump(indicators["main_src_compile"], sprites["secondary_header_sprite"], animation.bus)

animation.bus.on("bump_completed", finished_handler)
sprites["main_src_sprite"].bus.on("bump", main_src_bump_handler)

make_bump(sprites["gpp_sprite"], sprites["main_src_sprite"], sprites["main_src_sprite"].bus)

animation.render_until_done()

