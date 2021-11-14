#ifndef __list_!@valType@!_h
#define __list_!@valType@!_h

#include "main.h"

typedef struct list_!@valType@! {
    int len;
    int size;
    !@valType@!** values;
} list_!@valType@!;

!@valType@!* list_!@valType@!_get(list_!@valType@!* list, int index);


void list_!@valType@!_set(list_!@valType@!* list, int index, !@valType@!* value);

void list_!@valType@!_append(list_!@valType@!* list, !@valType@!* value);

void list_!@valType@!_removeAll(list_!@valType@!* list, !@valType@!* value);

void list_!@valType@!_del(list_!@valType@!* list, int index);

void list_!@valType@!_repr(list_!@valType@!* list);

char* list_!@valType@!_str(list_!@valType@!* list);

#endif
