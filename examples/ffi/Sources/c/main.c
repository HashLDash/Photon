#include <stdlib.h>
#include <stdio.h>
#include <locale.h>
#include "asprintf.h"
void compute() {
    long i = 0; for (; i < 10; i += 1) {
        printf("Ok %ld\n", i);
    } i -= 1;
}

int main() {
    setlocale(LC_ALL, "");
    return 0;
}
