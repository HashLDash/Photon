#include <stdio.h>
#include <stdlib.h>

typedef struct list_str {
    int len;  // number of element stored
    int size; // allocated array size
    char** values;
} list_str;

char* list_str_get(list_str* list, int index) {
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

void list_str_set(list_str* list, int index, char* value) {
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

void list_str_append(list_str* list, char* value) {
    if (list->len >= list->size) {
        list->size = list->size * 2;
        list->values = realloc(list->values, sizeof(char*) * list->size);
    }
    list->values[list->len] = value;
    list->len += 1;
}

void list_str_inc(list_str* list, int index, char* value) {
    if (index < 0) {
        // -1 is equivalent to the last element
        index = list->len + index;
    }
    if (index < 0 || index > list->len) {
        printf("IndexError: The array has %d elements, but you required the %d index\n", list->len, index);
        exit(-1);
    }
    asprintf(&list->values[index], "%s%s", list->values[index], value);
}
