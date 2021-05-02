#include <stdio.h>
#include <locale.h>
#include <stdlib.h>


int main() {
    setlocale(LC_ALL, "");
    printf("%s\n", "Hello World");
    return 0;
}
