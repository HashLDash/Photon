for C:
    native import time

time.srand(time.time(null))

def randomm():
    float a = time.rand() / time.RAND_MAX
    return a

def randint(int begin, int end):
    int a = randomm()*(end-begin)+begin
    return a

def randfloat(float begin, float end):
    float a = randomm()*(end-begin)+begin
    return a
