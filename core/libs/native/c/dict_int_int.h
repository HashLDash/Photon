typedef struct dict_int_int_entry {
    int prehash;
    int key;
    int val;
} dict_int_int_entry;

typedef struct dict_int_int {
    int len;
    int size;
    int* indices;
    dict_int_int_entry* entries;
} dict_int_int;

int dict_int_int_get(dict_int_int* self, int key) {
    int size = self->size;
    int index = key % size;
    while (self->entries[self->indices[index]].key != key) {
        index = (index + 1) % size;
        if (self->indices[index] != -1) {
            printf("KeyError: The key %d was not found.\n", key);
            exit(-1);
        }
    }
    return self->entries[self->indices[index]].val;
}

void dict_int_int_set(dict_int_int* self, int key, int value) {
    int dictLen = self->len;
    self->entries[dictLen].prehash = key; 
    self->entries[dictLen].key = key; 
    self->entries[dictLen].val = value; 
    self->len += 1;
    if (dictLen+1 == self->size) {
        self->size *= 2;
        int size = self->size;
        // recompute entries
        self->indices = realloc(self->indices, sizeof(int)*size);
        self->entries = realloc(self->entries, sizeof(dict_int_int_entry)*size);
        for (int i=0; i<size; i++) {
            self->indices[i] = -1; // -1 is None
        }
        for (int i=0; i<dictLen+1; i++) {
            int index = self->entries[i].prehash % size;
            while (self->indices[index] != -1) {
                index = (index + 1) % size;
            }
            self->indices[index] = i;
        }
    } else {
        int size = self->size;
        int index = key % size;
        while (self->indices[index] != -1) {
            if (self->entries[self->indices[index]].key == key) {
                self->entries[self->indices[index]].val = value;
                return;
            }
            index = (index + 1) % size;
        }
        self->indices[index] = dictLen;
    }
}

void dict_int_int_del(dict_int_int* self, int key) {
    int size = self->size;
    int index = key % size;
    while (self->entries[self->indices[index]].key != key) {
        index = (index + 1) % size;
        if (self->indices[index] != -1) {
            printf("KeyError: The key %d was not found.\n", key);
            exit(-1);
        }
    }
    self->indices[index] = -2;
}
