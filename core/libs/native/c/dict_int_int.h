typedef struct dict_int_int {
    list_int keys;
    list_int values;
} dict_int_int;

int dict_int_int_get(dict_int_int* self, int key) {
    int k;
    for (int n=0; n<self->keys.len; n++) {
        k = list_int_get(&self->keys,n);
        if (key == k) {
            return list_int_get(&self->values,n);
        }
    }
}
void dict_int_int_set(dict_int_int* self, int key,int value) {
    list_int_append(&self->keys,key);
    list_int_append(&self->values,value);
}
