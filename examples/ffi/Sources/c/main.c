#ifndef __main
#define __main
#include "asprintf.h"
#include "main.h"
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
void compute() {
    long i = 0; for (; i < 11; i += 1) {
        printf("Ok %ld\n", i);
    } i -= 1;
}

int main() {
    setlocale(LC_ALL, "");
    return 0;
}
#endif