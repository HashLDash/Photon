for C:
    import time

    srand(time(NULL))

    def random():
        float a = rand() / RAND_MAX
        return a

    def randint(int begin, int end):
        int a = random()*(end-begin)+begin
        return a

    def randfloat(float begin, float end):
        float a = random()*(end-begin)+begin
        return a
