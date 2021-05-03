#include <locale.h>
#include <stdio.h>
#include <stdlib.h>


int main() {
    setlocale(LC_ALL, "");
    long var = 2;
    printf("%d\n", var);
    return 0;
}
