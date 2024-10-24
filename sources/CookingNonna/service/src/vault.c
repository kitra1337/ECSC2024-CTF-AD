#define _GNU_SOURCE
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <dirent.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>       
#include <sys/stat.h>

#include "recipe.h"
#include "vault.h"
#include "user.h"
#include "util.h"

static const char *NO_VAULTS_FOUND = "No vaults found";
static const char *NO_VAULTS_OPEN = "No vaults open";
static const char *NO_FREE_VAULT_SLOT = "No free vault slots";
static const char *VAULT_NOT_FOUND = "Vault not found";
static const char *VAULT_CREATED = "Vault created";
static const char *VAULT_OPENED = "Vault opened";
static const char *VAULT_CLOSED = "Vault closed";
static const char *VAULT_ENTERED = "Vault entered";

static const char *FORBIDDEN_IDS[] = {
    ".",
    "..",
    "name",
};

struct vault *current_vault;
struct vault open_vaults[MAX_OPEN_VAULTS];

/* HELPERS START */
static struct vault* get_vault_slot() {
    for (int i = 0; i < MAX_OPEN_VAULTS; i++) {
        if (open_vaults[i].fd == 0) {
            memset(&open_vaults[i], 0, sizeof(struct vault));
            return &open_vaults[i];
        }
    }
    return NULL;
}

static bool is_forbidden_id(const char *name) {
    for (size_t i = 0; i < sizeof(FORBIDDEN_IDS) / sizeof(FORBIDDEN_IDS[0]); i++) {
        if (strcmp(name, FORBIDDEN_IDS[i]) == 0)
            return true;
    }
    return false;
}

static struct vault *get_vault_by_id(const char *id) {
    for (int i = 0; i < MAX_OPEN_VAULTS; i++) {
        if (open_vaults[i].fd != 0 && strcmp(open_vaults[i].id, id) == 0)
            return &open_vaults[i];
    }
    return NULL;
}

static void print_vault(char *id, char *name) {
    if (current_vault && strcmp(current_vault->id, id) == 0)
        printf(" * [ID]: %s\n", id);
    else
        printf(" - [ID]: %s\n", id);

    printf("   [Name]: %s\n", name);
}

static void show_vault_details(char *file_path) {
    int dfd = -1, fd = -1;
    char name[MAX_VAULT_NAME];

    dfd = openat(current_dir, file_path, O_DIRECTORY);
    if (dfd < 0) {
        error("Error opening vault directory");
        return;
    }
    
    fd = openat(dfd, "name", O_RDONLY);
    if (fd < 0) {
        error("Error opening vault name file");
        goto cleanup;
    }

    if(read_string(fd, name) < 0) {
        error("Error reading vault name");
        goto cleanup;
    }

    print_vault(file_path, name);

cleanup:
    if (dfd != -1)
        close(dfd);
    if (fd != -1)
        close(fd);
}
/* HELPERS END */

void list_vaults() {
    int dirfd = -1;
    bool found = false;
    struct dirent *entry = NULL;
    DIR *dir = NULL;

    dirfd = openat(current_dir, ".", O_RDONLY);
    if (dirfd < 0) {
        error("Error opening vault directory");
        return;
    }
    dir = fdopendir(dirfd);
    if (dir == NULL) {
        error("Error opening directory");
        close(dirfd);
        return;
    }

    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type != DT_DIR || is_forbidden_id(entry->d_name))
            continue;

        if (!found) {
            found = true;
            success("Vaults:");
        }

        show_vault_details(entry->d_name);
    }

    closedir(dir);

    if (!found)
        info(NO_VAULTS_FOUND);
}

void create_vault() {
    int dfd = -1, fd = -1;
    struct vault *vault = NULL;

    vault = get_vault_slot();
    if (vault == NULL) {
        warn(NO_FREE_VAULT_SLOT);
        return;
    }

    prompt("Enter vault name");
    if (read_line(0, vault->name, sizeof(vault->name)) < 0) {
        error("Error reading vault name");
        goto err;
    }

    random_id(vault->id);

    if (mkdirat(current_dir, vault->id, 0700) < 0) {
        error("Error creating vault directory");
        goto err;
    }

    dfd = openat(current_dir, vault->id, O_DIRECTORY);
    if (dfd < 0) {
        error("Error opening vault directory");
        goto err;
    }

    fd = openat(dfd, "name", O_CREAT | O_WRONLY, 0400);
    if (fd < 0) {
        error("Error creating name file");
        goto err;
    }

    if (!write_string(fd, vault->name)) {
        error("Error writing name to file");
        goto err;
    }

    debug({
        prompt("Override vault fd? (y/n)");
        if (read_bool()) {
            prompt("Enter vault fd");
            dfd = get_int();
        }
    });

    close(fd);

    vault->fd = dfd;
    current_vault = vault;
    
    success(VAULT_CREATED);
    return;
err:
    memset(vault, 0, sizeof(struct vault));
    if (dfd != -1)
        close(dfd);
    if (fd != -1)
        close(fd);
}

void open_vault() {
    int dfd = -1, fd = -1;
    struct vault *vault = NULL;

    vault = get_vault_slot();
    if (vault == NULL) {
        warn(NO_FREE_VAULT_SLOT);
        return;
    }
    
    prompt("Enter vault ID");
    if (!read_id(0, vault->id)) {
        error("Error reading vault ID");
        goto err;
    }

    if (is_forbidden_id(vault->id)) {
        warn("Forbidden ID");
        goto err;
    }

    dfd = openat(current_dir, vault->id, O_DIRECTORY);
    if (dfd < 0) {
        warn(VAULT_NOT_FOUND);
        goto err;
    }

    fd = openat(dfd, "name", O_RDONLY);
    if (fd < 0) {
        error("Error creating name file");
        goto err;
    }

    if (read_string(fd, vault->name) < 0) {
        error("Error reading vault name");
        goto err;
    }

    debug({
        prompt("Override vault fd? (y/n)");
        if (read_bool()) {
            prompt("Enter vault fd");
            dfd = get_int();
        }
    });

    close(fd);

    vault->fd = dfd;
    current_vault = vault;

    success(VAULT_OPENED);
    return;
err:
    memset(vault, 0, sizeof(struct vault));
    if (dfd != -1)
        close(dfd);
    if (fd != -1)
        close(fd);
}

void close_vault() {
    char vault_id[ID_LEN] = {0};
    struct vault *vault = NULL;

    prompt("Enter vault ID");
    if (!read_id(0, vault_id)) {
        error("Error reading vault ID");
        return;
    }

    vault = get_vault_by_id(vault_id);
    if (vault == NULL) {
        warn(VAULT_NOT_FOUND);
        return;
    }

    close(vault->fd);
    memset(vault, 0, sizeof(struct vault));

    success(VAULT_CLOSED);
}

void list_open_vaults() {
    bool found = false;

    for (int i = 0; i < MAX_OPEN_VAULTS; i++) {
        if (open_vaults[i].fd != 0) {
            if (!found) {
                found = true;
                success("Open vaults:");
            }
            print_vault(open_vaults[i].id, open_vaults[i].name);
        }
    }

    if (!found)
        info(NO_VAULTS_OPEN);
}

void enter_vault() {
    struct vault *vault = NULL;
    char vault_id[ID_LEN] = {0};

    prompt("Enter vault ID");
    if (!read_id(0, vault_id)) {
        error("Error reading vault ID");
        return;
    }

    vault = get_vault_by_id(vault_id);
    if (vault == NULL) {
        warn(VAULT_NOT_FOUND);
        return;
    }

    current_vault = vault;
    success(VAULT_ENTERED);
}

void logout() {
    for (int i = 0; i < MAX_OPEN_RECIPES; i++) {
        if (open_recipes[i].vault != NULL && open_recipes[i].is_dirty) {
            prompt("You have unsaved recipes. Discard them? (y/n)");
            if (!read_bool()) {
                return;
            }
            break;
        }
    }

    close(current_dir);
    current_vault = NULL;
    current_dir = -1;
    logged_in = false;

    for (int i = 0; i < MAX_OPEN_VAULTS; i++) {
        if (open_vaults[i].fd != 0) {
            close(open_vaults[i].fd);
        }
    }

    memset(open_vaults, 0, sizeof(open_vaults));
    memset(open_recipes, 0, sizeof(open_recipes));

    success("User logged out successfully");
}