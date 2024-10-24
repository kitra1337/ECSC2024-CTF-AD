#ifndef RECIPE_H
#define RECIPE_H

#include <stdbool.h>

#include "util.h"
#include "vault.h"

#define MAX_RECIPE_NAME 64
#define MAX_RECIPE_AUTHOR 64
#define MAX_RECIPE_DESCRIPTION 0x100
#define MAX_OPEN_RECIPES 10

struct recipe {
    struct vault *vault;
    char id[ID_LEN];
    char name[MAX_RECIPE_NAME];
    char author[MAX_RECIPE_AUTHOR];
    char description[MAX_RECIPE_DESCRIPTION];
    bool is_dirty;
};

extern struct recipe *current_recipe;
extern struct recipe open_recipes[MAX_OPEN_RECIPES];

void list_recipes();
void create_recipe();
void open_recipe();
void close_recipe();
bool save_recipe();
void discard_recipe();
void list_open_recipes();
void select_recipe();
void show_recipe();
void edit_recipe();
void back();

#endif