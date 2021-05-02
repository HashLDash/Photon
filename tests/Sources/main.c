#include <locale.h>
#include <stdlib.h>
#include <stdio.h>


int main() {
    setlocale(LC_ALL, "");
    printf("%s\n", "Hello World");
    return 0;
}
