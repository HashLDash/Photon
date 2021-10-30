#include <stdio.h>
#include <stdlib.h>
#include "asprintf.h"

typedef struct list_int {
    int len;  // number of element stored
    int size; // allocated array size
    long* values;
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

void list_int_set(list_int* list, int index, long value) {
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

void list_int_append(list_int* list, long value) {
    if (list->len >= list->size) {
        list->size = list->size * 2;
        list->values = realloc(list->values, sizeof(long) * list->size);
    }
    list->values[list->len] = value;
    list->len += 1;
}

void list_int_removeAll(list_int* list, long value) {
    int removedItems = 0;
    int listLen = list->len;
    for (int i=0; i<listLen; i++) {
        if (list->values[i] == value) {
            removedItems = 1;
            for (i=i; i<listLen-removedItems; i++) {
                if (list->values[i] == value) {
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

void list_int_del(list_int* list, int index) {
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

void list_int_inc(list_int* list, int index, long value) {
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

void list_int_repr(list_int* list) {
    int listLen = list->len;
    printf("[");
    for (int i=0; i<listLen-1; i++) {
        printf("%ld, ", list->values[i]);
    }
    if (listLen > 0) {
        printf("%ld]\n", list->values[listLen-1]);
    } else {
        printf("]\n");
    }
}

char* list_int_str(list_int* list) {
    int listLen = list->len;
    char* out = "[";
    for (int i=0; i<listLen-1; i++) {
        asprintf(&out, "%s%ld, ", out, list->values[i]);
    }
    if (listLen > 0) {
        asprintf(&out, "%s%ld]", out, list->values[listLen-1]);
    } else {
        asprintf(&out, "%s]", out);
    }
    return out;
}
