for C:
    native import time

    time.srand(time.time(null))
    def random():
        float maxNumber = time.RAND_MAX
        float a = time.rand() / maxNumber
        return a

for Python:
    native import random

    def random():
        float a = random.random()
        return a

def randint(int begin, int end):
    int a = random()*(end-begin)+begin
    return a

def randfloat(float begin, float end):
    float a = random()*(end-begin)+begin
    return a
