#ifndef __list_float
#define __list_float

#include <stdio.h>
#include <stdlib.h>
#include "asprintf.h"

typedef struct list_float {
    int len;
    int size;
    double* values;
} list_float;

list_float* list_float_constructor(int len, int size, ...) {
    list_float* list = malloc(sizeof(list_float));
    list->len = len;
    list->size = size;
    list->values = malloc(sizeof(double)*size);

    va_list ptr;
    va_start(ptr, size); // size is the last argument before the ellipsis

    for (int i = 0; i < len; i++) {
        list->values[i] = va_arg(ptr, double);
    }
    va_end(ptr);
    return list;
}

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

static inline int float_equals(double v1, double v2) {
    double delta = 0.0000000001;
    if (v1 >= v2 - delta && v1 <= v2 + delta) {
        return 1;
    } else {
        return 0;
    }
}

void list_float_removeAll(list_float* list, double value) {
    int removedItems = 0;
    int listLen = list->len;
    for (int i=0; i<listLen; i++) {
        if (float_equals(list->values[i], value)) {
            removedItems = 1;
            for (i=i; i<listLen-removedItems; i++) {
                if (float_equals(list->values[i], value)) {
                    removedItems++;
                }
                list->values[i] = list->values[i+removedItems];
            }
            break;
        }
    }
    list->len -= removedItems;
    if (list->size >= 4*list->len) {
        list->size = list->size / 2;
        list->values = realloc(list->values, sizeof(long) * list->size);
    }
}

void list_float_del(list_float* list, int index) {
    int listLen = list->len;
    for (int i=index; i<listLen-1; i++) {
        list->values[i] = list->values[i+1];
    }
    list->len -= 1;
    if (list->size >= 4*list->len) {
        list->size = list->size / 2;
        list->values = realloc(list->values, sizeof(long) * list->size);
    }
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
        printf("%lg, ", list->values[i]);
    }
    if (listLen > 0) {
        printf("%lg]\n", list->values[listLen-1]);
    } else {
        printf("]\n");
    }
}

char* list_float_str(list_float* list) {
    int listLen = list->len;
    char* out = "[";
    for (int i=0; i<listLen-1; i++) {
        asprintf(&out, "%s%lg, ", out, list->values[i]);
    }
    if (listLen > 0) {
        asprintf(&out, "%s%lg]", out, list->values[listLen-1]);
    } else {
        asprintf(&out, "%s]", out);
    }
    return out;
}
#endif
