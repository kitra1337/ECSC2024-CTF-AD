#ifndef UTIL_H
#define UTIL_H

#include <unistd.h>
#include <stdbool.h>

#define DEBUG 0

#if DEBUG
#define debug(x) x
#define debug_print(fmt, ...) fprintf(stderr, fmt, ##__VA_ARGS__)
#else
#define debug(x)
#define debug_print(fmt, ...)
#endif

#define HEXDIGEST_LEN 64
#define ID_LEN 0x20

enum AuthOperation {
    AUTH_SIGNUP = 1,
    AUTH_LOGIN,
    AUTH_EXIT
};

enum VaultOperation {
    VAULT_LIST = 1,
    VAULT_CREATE,
    VAULT_OPEN,
    VAULT_CLOSE,
    VAULT_LIST_OPEN,
    VAULT_ENTER,
    VAULT_LOGOUT
};

enum RecipeOperation {
    RECIPE_LIST = 1,
    RECIPE_CREATE,
    RECIPE_OPEN,
    RECIPE_CLOSE,
    RECIPE_SAVE,
    RECIPE_DISCARD,
    RECIPE_LIST_OPEN,
    RECIPE_SELECT,
    RECIPE_SHOW,
    RECIPE_EDIT,
    RECIPE_BACK
};

void die(const char *msg);
void prompt(const char *msg);
void success(const char *msg);
void error(const char *msg);
void info(const char *msg);
void warn(const char *msg);
int get_int();
long get_long();
bool read_bool();
int random_int();
long random_long();
void random_id(char *id);
bool read_exactly(int fd, void *buf, size_t size);
bool read_id(int fd, char *buf);
ssize_t read_line(int fd, char *buf, size_t size);
ssize_t read_string(int fd, char *buf);
bool write_exactly(int fd, const void *buf, size_t size);
bool write_string(int fd, char *buf);
void set_buf(void);
void hexprint(const void *buf, size_t size);
void hexdigest(const void *buf, size_t size, char *out);
bool dir_exists(int dfd, const char *path);
bool ensure_dir(int dfd, const char *path);
void rndbytes(unsigned char *x, size_t xlen);

#endif