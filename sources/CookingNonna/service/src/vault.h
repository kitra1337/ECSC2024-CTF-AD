#ifndef VAULT_H
#define VAULT_H

#include <stdbool.h>

#include "util.h"

#define MAX_VAULT_NAME 64
#define MAX_OPEN_VAULTS 10

struct vault {
    int fd;
    char id[ID_LEN];
    char name[MAX_VAULT_NAME];
};

extern struct vault *current_vault;
extern struct vault open_vaults[MAX_OPEN_VAULTS];

void list_vaults();
void create_vault();
void open_vault();
void close_vault();
void list_open_vaults();
void enter_vault();
void logout();

#endif