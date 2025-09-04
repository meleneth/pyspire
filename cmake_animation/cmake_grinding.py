from pyspire import Size, Vec2, PySpire

animation = PySpire(size=Size(1920, 1080), base_filename="cmake_animation")

gpp_sprite = animation.add_sprite("gpp_sprite")
gpp_bg_layer   = gpp_sprite.add_image("program.png")
gpp_text_layer = gpp_sprite.add_image("g++.png")
gpp_text_layer.center(gpp_bg_layer)        # center text over bg (layer-on-layer)
gpp_sprite.position = Vec2(50, 200)

main_src_sprite = animation.add_sprite("main_src_sprite")
main_src_bg_layer   = main_src_sprite.add_image("source.png")
main_src_text_layer = main_src_sprite.add_image("main_src.png")
main_src_text_layer.center(main_src_bg_layer)
main_src_sprite.position = Vec2(50, 400)

secondary_src_sprite = animation.add_sprite("secondary_src_sprite")
secondary_src_bg_layer   = secondary_src_sprite.add_image("source.png")
secondary_src_text_layer = secondary_src_sprite.add_image("secondary_src.png")
secondary_src_text_layer.center(secondary_src_bg_layer)
secondary_src_sprite.position = Vec2(50, 600)

secondary_header_sprite = animation.add_sprite("secondary_header_sprite")
secondary_header_bg_layer   = secondary_header_sprite.add_image("source.png")
secondary_header_text_layer = secondary_header_sprite.add_image("secondary_header.png")
secondary_header_text_layer.center(secondary_header_bg_layer)
secondary_header_sprite.position = Vec2(800, 600)

some_program_sprite = animation.add_sprite("some_program_sprite")
some_program_bg_layer   = some_program_sprite.add_image("program.png")
some_program_text_layer = some_program_sprite.add_image("some_program.png")
some_program_text_layer.center(some_program_bg_layer)
some_program_sprite.position = Vec2(50, 800)

# This would write "cmake_animation_000_000.png"
animation.render_frame()
