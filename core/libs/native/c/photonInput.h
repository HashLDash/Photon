#include <stdlib.h>
#include <stdio.h>

char *photonInput()
{
    int c;
    size_t size = 5;
    size_t read_size = 0;
    char *line = malloc(size);
    if (!line) 
    {
        perror("malloc");
        return line;
    }

    line[0] = '\0';

    c = fgetc(stdin);
    while (c != EOF && c!= '\n')
    {            
        line[read_size] = c;            
        ++read_size;
        if (read_size == size)
        {
            size += 5;
            char *test = realloc(line, size);
            if (!test)
            {
                perror("realloc");
                return line;
            }
            line = test;
        }
        c = fgetc(stdin);
    }
    line[read_size] = '\0';
    return line;
}
