for C:
    import time
    native import random

    time.srand(time.time(null))

    def random():
        float a = rand() / RAND_MAX
        return a

    def randint(int begin, int end):
        int a = random()*(end-begin)+begin
        return a

    def randfloat(float begin, float end):
        float a = random()*(end-begin)+begin
        return a
