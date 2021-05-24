#include <stdio.h>
#include <stdlib.h>

typedef struct list_int {
    int len;
    int size;
    int* values;
} list_int;

int list_int_get(list_int* list, int index) {
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

void list_int_set(list_int* list, int index, int value) {
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

void list_int_append(list_int* list, int value) {
    if (list->len >= list->size) {
        list->size = list->size * 2;
        list->values = realloc(list->values, sizeof(int) * list->size);
    }
    list->values[list->len] = value;
    list->len += 1;
}

void list_int_inc(list_int* list, int index, int value) {
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
