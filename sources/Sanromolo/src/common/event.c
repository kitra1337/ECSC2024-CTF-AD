#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include <stdio.h>

#include "common/event.h"
#include "common/util.h"

int get_event_data(uint8_t *event_id, struct Event *event) {
    char path[sizeof(EVENT_DIRECTORY) + 128] = {0};
    struct stat st = {0};

    strcpy(path, EVENT_DIRECTORY);
    bytes_to_hex(path + sizeof(EVENT_DIRECTORY) - 1, event_id, 16);

    if (stat(path, &st) != 0 || !S_ISREG(st.st_mode))
        return -1;

    int fd = open(path, O_RDONLY);
    if (fd < 0)
        return -1;

    char *event_name = calloc(1, EVENT_NAME_LEN + 1);
    char *event_star_signature = calloc(1, EVENT_STAR_SIGNATURE_LEN + 1);
    read_exactly(fd, event->id, sizeof(event->id));
    read_exactly(fd, event->vip_invitation_code, sizeof(event->vip_invitation_code));
    read_exactly(fd, event_name, EVENT_NAME_LEN);
    read_exactly(fd, event_star_signature, EVENT_STAR_SIGNATURE_LEN);
    event->name = event_name;
    event->star_signature = event_star_signature;

    close(fd);
    return 0;
}
