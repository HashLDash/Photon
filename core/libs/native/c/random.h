#include "time.h"
#include "sys/random.h"

srand(time(null))

double random() {
    double a = rand() / RAND_MAX;
    return a;
}

long randint(long begin, long end) {
    long a = random()*(end-begin)+begin;
    return a;
}

double randfloat(double begin, double end) {
    double a = random()*(end-begin)+begin;
    return a;
}
