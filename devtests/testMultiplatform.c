#include "asprintf.h"
#include <stdio.h>

int main() {
    char* a;
    int len = asprintf(&a, "%s", "Hello");
    printf("%s\n", a);
}
