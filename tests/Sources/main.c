#include <stdio.h>
#include <locale.h>
#include <stdlib.h>


int main() {
    setlocale(LC_ALL, "");
    long var = 2;
    printf("%ld\n", var);
    return 0;
}
