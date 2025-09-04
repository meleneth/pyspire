def ease_out_cubic(t: float) -> float:
    u = 1.0 - t
    return 1.0 - u*u*u

def ease_in_cubic(t: float) -> float:
    return t*t*t
