#ifndef __list_!@valType@!
#define __list_!@valType@!

#include <stdio.h>
#include <stdlib.h>
#include "asprintf.h"
#include "list_!@valType@!.h"

list_!@valType@!* list_!@valType@!_constructor(int len, int size, ...) {
    list_!@valType@!* list = malloc(sizeof(list_!@valType@!));
    list->len = len;
    list->size = size;
    list->values = malloc(sizeof(!@valType@!*)*size);

    va_list ptr;
    va_start(ptr, size); // size is the last argument before the ellipsis

    for (int i = 0; i < len; i++) {
        list->values[i] = va_arg(ptr, !@valType@!*);
    }
    va_end(ptr);
    return list;
}

!@valType@!* list_!@valType@!_get(list_!@valType@!* list, int index) {
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

void list_!@valType@!_set(list_!@valType@!* list, int index, !@valType@!* value) {
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

void list_!@valType@!_append(list_!@valType@!* list, !@valType@!* value) {
    if (list->len >= list->size) {
        list->size = list->size * 2;
        list->values = realloc(list->values, sizeof(!@valType@!) * list->size);
    }
    list->values[list->len] = value;
    list->len += 1;
}

void list_!@valType@!_removeAll(list_!@valType@!* list, !@valType@!* value) {
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
        list->values = realloc(list->values, sizeof(!@valType@!) * list->size);
    }
}

void list_!@valType@!_del(list_!@valType@!* list, int index) {
    int listLen = list->len;
    for (int i=index; i<listLen-1; i++) {
        list->values[i] = list->values[i+1];
    }
    list->len -= 1;
    if (list->size >= 4*list->len) {
        list->size = list->size / 2;
        list->values = realloc(list->values, sizeof(!@valType@!) * list->size);
    }
}

/* TODO: this makes sense for class?
void list_!@valType@!_inc(list_!@valType@!* list, int index, double value) {
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
*/

void list_!@valType@!_repr(list_!@valType@!* list) {
    int listLen = list->len;
    printf("[");
    for (int i=0; i<listLen-1; i++) {
        printf("<class !@valType@!>, ");
    }
    if (listLen > 0) {
        printf("<class !@valType@!>]\n");
    } else {
        printf("]\n");
    }
}

char* list_!@valType@!_str(list_!@valType@!* list) {
    int listLen = list->len;
    char* out = "[";
    // TODO: change to class_repr
    for (int i=0; i<listLen-1; i++) {
        asprintf(&out, "%s<class !@valType@!>, ", out);
    }
    if (listLen > 0) {
        asprintf(&out, "%s<class !@valType@!>]", out);
    } else {
        asprintf(&out, "%s]", out);
    }
    return out;
}

void list_!@valType@!_clear(list_!@valType@!* list) {
    list->len = 0;
}

#endif
