#define _GNU_SOURCE
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <dirent.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>

#include "recipe.h"
#include "user.h"
#include "util.h"

static const char *NO_RECIPES_FOUND = "No recipes found";
static const char *NO_RECIPE_OPEN = "No recipe open";
static const char *NO_RECIPES_OPEN = "No recipes open";
static const char *NO_FREE_RECIPE_SLOT = "No free recipe slots";
static const char *RECIPE_NOT_FOUND = "Recipe not found";
static const char *RECIPE_CREATED = "Recipe created";
static const char *RECIPE_OPENED = "Recipe opened";
static const char *RECIPE_CLOSED = "Recipe closed";
static const char *RECIPE_SAVED = "Recipe saved";
static const char *RECIPE_DISCARDED = "Recipe discarded";
static const char *RECIPE_SELECTED = "Recipe selected";
static const char *RECIPE_EDITED = "Recipe edited";
static const char *RECIPE_NOT_DIRTY = "Recipe not dirty";
static const char *RECIPE_IS_LOCKED = "Recipe is locked";

static const char *FORBIDDEN_IDS[] = {
    ".",
    "..",
    "name",
};

struct recipe *current_recipe;
struct recipe open_recipes[MAX_OPEN_RECIPES];

/* HELPERS START */
static struct recipe* get_recipe_slot() {
    for (int i = 0; i < MAX_OPEN_RECIPES; i++) {
        if (open_recipes[i].vault == NULL) {
            memset(&open_recipes[i], 0, sizeof(struct recipe));
            return &open_recipes[i];
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

static bool write_recipe_to_file(int fd, struct recipe *recipe) {
    return write_string(fd, recipe->name) &&
           write_string(fd, recipe->author) &&
           write_string(fd, recipe->description);
}

static void print_recipe(char *id, char *name, char *author, char *description) {
    if (current_recipe && strcmp(current_recipe->id, id) == 0)
        printf(" * [ID]: %s\n", id);
    else
        printf(" - [ID]: %s\n", id);

    printf("   [Name]: %s\n", name);

    if (author) {
        printf("   [Author]: %s\n", author);
    }

    if (description) {
        printf("   [Description]: %s\n", description);
    }
}

static void show_recipe_details(char *id) {
    int fd = -1;
    char name[MAX_RECIPE_NAME] = {0};
    
    fd = openat(current_vault->fd, id, O_RDONLY);
    if (fd < 0) {
        error("Error opening recipe file");
        return;
    }

    if (read_string(fd, name) < 0) {
        error("Error reading recipe name");
        close(fd);
        return;
    }

    close(fd);
    
    print_recipe(id, name, NULL, NULL);
}

static bool prompt_recipe(struct recipe *recipe) {
    prompt("Enter recipe name");
    if (read_line(0, recipe->name, sizeof(recipe->name)) < 0) {
        error("Error reading vault name");
        return false;
    }
    
    prompt("Enter author name");
    if (read_line(0, recipe->author, sizeof(recipe->author)) < 0) {
        error("Error reading author name");
        return false;
    }

    prompt("Enter description");
    if (read_line(0, recipe->description, sizeof(recipe->description)) < 0) {
        error("Error reading description");
        return false;
    }

    return true;
}
/* HELPERS END */

void list_recipes() {
    int dirfd = -1;
    bool found = false;
    struct dirent *entry = NULL;
    DIR *dir = NULL;

    dirfd = openat(current_vault->fd, ".", O_RDONLY);
    if (dirfd < 0) {
        error("Error opening recipe directory");
        return;
    }
    dir = fdopendir(dirfd);
    if (dir == NULL) {
        error("Error opening directory");
        close(dirfd);
        return;
    }

    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type != DT_REG || is_forbidden_id(entry->d_name))
            continue;

        if (!found) {
            found = true;
            success("Recipes:");
        }

        show_recipe_details(entry->d_name);
    }

    closedir(dir);

    if (!found)
        info(NO_RECIPES_FOUND);
}

void create_recipe() {
    int fd = -1;
    bool locked = false;
    struct recipe *recipe = NULL;

    recipe = get_recipe_slot();
    if (recipe == NULL) {
        warn(NO_FREE_RECIPE_SLOT);
        return;
    }

    random_id(recipe->id);

    if (!prompt_recipe(recipe))
        goto err;

    prompt("Lock recipe? (y/n)");
    locked = read_bool();
    
    fd = openat(current_vault->fd, recipe->id, O_CREAT | O_WRONLY, locked ? 0400 : 0600);
    if (fd < 0) {
        error("Error creating recipe file");
        goto err;
    }

    if (!write_recipe_to_file(fd, recipe)) {
        error("Error writing recipe to file");
        goto err;
    }

    close(fd);

    recipe->vault = current_vault;
    current_recipe = recipe;

    success(RECIPE_CREATED);
    return;
err:
    memset(recipe, 0, sizeof(struct recipe));
    if (fd != -1)
        close(fd);
}

void open_recipe() {
    int fd = -1;
    struct recipe *recipe = NULL;

    recipe = get_recipe_slot();
    if (recipe == NULL) {
        warn(NO_FREE_RECIPE_SLOT);
        return;
    }

    prompt("Enter recipe ID");
    if (!read_id(0, recipe->id)) {
        error("Error reading recipe ID");
        goto err;
    }

    if (is_forbidden_id(recipe->id)) {
        warn("Forbidden ID");
        goto err;
    }

    fd = openat(current_vault->fd, recipe->id, O_RDONLY);
    if (fd < 0) {
        warn(RECIPE_NOT_FOUND);
        goto err;
    }

    if (read_string(fd, recipe->name) < 0) {
        error("Error reading recipe name");
        goto err;
    }
    if (read_string(fd, recipe->author) < 0) {
        error("Error reading recipe author");
        goto err;
    }
    if (read_string(fd, recipe->description) < 0) {
        error("Error reading recipe description");
        goto err;
    }

    close(fd);

    recipe->vault = current_vault;
    current_recipe = recipe;

    success(RECIPE_OPENED);
    return;

err:
    memset(recipe, 0, sizeof(struct recipe));
    if (fd != -1)
        close(fd);
}

void close_recipe() {
    if (current_recipe == NULL) {
        warn(NO_RECIPE_OPEN);
        return;
    }
    
    if (current_recipe->is_dirty) {
        prompt("Save recipe before closing? (y/n)");
        if (read_bool()) {
            if (!save_recipe())
                return;
        }
    }

    memset(current_recipe, 0, sizeof(struct recipe));
    current_recipe = NULL;

    success(RECIPE_CLOSED);
}

bool save_recipe() {
    int fd = -1;

    if (current_recipe == NULL) {
        warn(NO_RECIPE_OPEN);
        return false;
    }

    if (!current_recipe->is_dirty) {
        warn(RECIPE_NOT_DIRTY);
        return false;
    }

    fd = openat(current_vault->fd, current_recipe->id, O_WRONLY);
    if (fd < 0) {
        warn(RECIPE_IS_LOCKED);
        return false;
    }

    if (!write_recipe_to_file(fd, current_recipe)) {
        error("Error writing recipe to file");
        close(fd);
        return false;
    }

    close(fd);

    current_recipe->is_dirty = false;

    success(RECIPE_SAVED);
    return true;
}

void discard_recipe() {
    if (current_recipe == NULL) {
        warn(NO_RECIPE_OPEN);
        return;
    }

    memset(current_recipe, 0, sizeof(struct recipe));
    current_recipe = NULL;

    success(RECIPE_DISCARDED);
}

void list_open_recipes() {
    bool found = false;

    for (int i = 0; i < MAX_OPEN_RECIPES; i++) {
        if (open_recipes[i].vault == current_vault) {
            if (!found) {
                found = true;
                success("Open recipes:");
            }

            print_recipe(open_recipes[i].id, open_recipes[i].name, open_recipes[i].author, NULL);
        }
    }

    if (!found)
        info(NO_RECIPES_OPEN);
}

void select_recipe() {
    char recipe_id[ID_LEN] = {0};

    prompt("Enter recipe ID");
    if (!read_id(0, recipe_id)) {
        error("Error reading recipe ID");
        return;
    }

    for (int i = 0; i < MAX_OPEN_VAULTS; i++) {
        if (open_recipes[i].vault == current_vault && strcmp(open_recipes[i].id, recipe_id) == 0) {
            current_recipe = &open_recipes[i];
            success(RECIPE_SELECTED);
            return;
        }
    }

    warn(RECIPE_NOT_FOUND);
}

void show_recipe() {
    if (current_recipe == NULL) {
        warn(NO_RECIPE_OPEN);
        return;
    }

    success("Recipe:");
    print_recipe(current_recipe->id, current_recipe->name, current_recipe->author, current_recipe->description);
}

void edit_recipe() {
    if (current_recipe == NULL) {
        warn(NO_RECIPE_OPEN);
        return;
    }

    current_recipe->is_dirty = true;

    if (!prompt_recipe(current_recipe))
        return;
    
    success(RECIPE_EDITED);
    return;
}

void back() {
    current_recipe = NULL;
    current_vault = NULL;
}