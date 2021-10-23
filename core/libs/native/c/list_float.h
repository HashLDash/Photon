#include <stdio.h>
#include <stdlib.h>

typedef struct list_float {
    int len;
    int size;
    double* values;
} list_float;

double list_float_get(list_float* list, int index) {
    if (index < 0) {
        // -1 is equivalent to the last element
        index = list->len + index;
    }
    if (index < 0 || index > list->len) {
        printf("IndexError: The array has %d elements, but you required the %d index\n", list->len, index);
        exit(-1);
    }
    return list->values[index];
}

void list_float_set(list_float* list, int index, double value) {
    if (index < 0) {
        // -1 is equivalent to the last element
        index = list->len + index;
    }
    if (index < 0 || index > list->len) {
        printf("IndexError: The array has %d elements, but you required the %d index\n", list->len, index);
        exit(-1);
    }
    list->values[index] = value;
}

void list_float_append(list_float* list, double value) {
    if (list->len >= list->size) {
        list->size = list->size * 2;
        list->values = realloc(list->values, sizeof(double) * list->size);
    }
    list->values[list->len] = value;
    list->len += 1;
}

void list_float_inc(list_float* list, int index, double value) {
    if (index < 0) {
        // -1 is equivalent to the last element
        index = list->len + index;
    }
    if (index < 0 || index > list->len) {
        printf("IndexError: The array has %d elements, but you required the %d index\n", list->len, index);
        exit(-1);
    }
    list->values[index] += value;
}

void list_float_repr(list_float* list) {
    int listLen = list->len;
    printf("[");
    for (int i=0; i<listLen-1; i++) {
        printf("%lf, ", list->values[i]);
    }
    if (listLen > 0) {
        printf("%lf]\n", list->values[listLen-1]);
    } else {
        printf("]");
    }
}
