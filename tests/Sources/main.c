#include <locale.h>
#include <stdlib.h>
#include <stdio.h>


int main() {
    setlocale(LC_ALL, "");
    long var = 2;
    printf("%d\n", var);
    return 0;
}
