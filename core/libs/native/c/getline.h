/* getline.c --- Implementation of replacement getline function.
   Copyright (C) 2005, 2006 Free Software Foundation, Inc.
   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2, or (at
   your option) any later version.
   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.
   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
   02110-1301, USA.  */

/* Written by Simon Josefsson. */

#include "utils.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include <errno.h>


ssize_t getline(char **lineptr, size_t *n, FILE *stream) {
        char *dest = *lineptr, *ret, *newline;
        size_t len = *n;

        if (dest == NULL || len < 1) {
                len = 256;
                if ((dest = malloc(len)) == NULL) {
                        goto error;
                }
        }

        /* Fetch up to line_length bytes from the file, or up to a newline */
        ret = fgets(dest, (int) (len-1), stream);
        if (ret == NULL) {
                if (feof(stream) != 0) {
                        dest[0] = '\0';
                        len = 0;
                        return 0;
                } else {
                        goto error;
                }
        }

        /* If the line was too long, and so doesn't contain a newline, carry on
         * fetching until it does, or we hit the end of the file. */
        while ((newline = strchr(dest, '\n')) == NULL) {
                char *new_dest, *tmp;

                /* Create a new storage space the same size as the last one, and carry
                 * on reading. We'll need to append this to the previous string - fgets
                 * will just overwrite it. */
                if ((tmp = malloc(len)) == NULL) {
                        goto error;
                }

                ret = fgets(tmp, (int) (len-1), stream);
                if (ret == NULL) {
                        /* This probably shouldn't happen... */
                        if (feof(stream) != 0) {
                                free(tmp);
                                break;
                        } else {
                                free(tmp);
                                goto error;
                        }
                }

                len *= 2;
                if ((new_dest = realloc(dest, (size_t)len)) == NULL) {
                        free(tmp);
                        goto error;
                }

                dest = new_dest;
                strlcat(dest, tmp, len);
                free(tmp);
        }

        /* Don't include the newline in the line we return. */
        if (newline != NULL)
                *newline = '\0';

        return (ssize_t) (newline - dest - 1);

error:
        free(dest);
        dest = NULL;
        len = 0;
        return -1;
}
