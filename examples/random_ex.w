
for C:

    import time

    srand(time(NULL))

    def float random(float begin = 0.0, float end = 0.0):
        float gen = rand() / RAND_MAX
        if begin != 0.0 or end != 0.0:
            gen = gen * (end - begin) + begin
        return gen

def test_random(float begin, float end, int max_iteration = 100000):
    x = 0
    y = 0
    z = 0
    float k = []
    for i in 0..max_iteration:
        gen = random(begin = begin, end = end)
        if gen == begin:
            x += 1
        elif gen == end:
            y += 1
        else:
            z += 1
            k += gen
    print("max_iteration: {max_iteration == (x + y + z)}")
    print("x: {x} | Begin: {begin}")
    print("y: {y} | End: {end}")
    print("z: {z} | Interval: {begin}..{end}")
    #print("k: ", end='')
    #print(k)
    print()

test_random(-5, 5)
