//PHOTON_FLAGS curl
//PHOTON_INCLUDES asprintf
#include <stdio.h>
#include <curl/curl.h>
#include "asprintf.h"

size_t get_data(char* buffer, size_t itemsize, size_t nitems, void* obj) {
    char** old = (char**) obj;
    asprintf(old, "%s%s", *old, buffer);
    return itemsize * nitems;
}

char* get(char* url) {
    CURL* curl;
    CURLcode resp;
    
    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        char* result = "";
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &result);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, get_data);

        resp = curl_easy_perform(curl);
        if (resp != CURLE_OK) {
            printf("GET failed: %s\n", curl_easy_strerror(resp));
        }

        curl_easy_cleanup(curl);
        return result;
    }
}
