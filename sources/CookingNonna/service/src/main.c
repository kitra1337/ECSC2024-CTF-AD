#define _GNU_SOURCE
#include <stdio.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/sha.h>
#include <linux/limits.h>

#include "util.h"
#include "recipe.h"
#include "user.h"
#include "crypto.h"

static int data_fd = -1;

void signup() {
    int dfd = -1, fd = -1;
    ssize_t username_len, password_len;
    char username[MAX_USERNAME_LEN];
    char password[MAX_PASSWORD_LEN];
    char digest[HEXDIGEST_LEN+1];

    prompt("Enter username");
    username_len = read_line(0, username, sizeof(username));
    if (username_len < 0) {
        error("Error reading username");
        return;
    }

    prompt("Enter password");
    password_len = read_line(0, password, sizeof(password));
    if (password_len < 0) {
        error("Error reading password");
        return;
    }

    hexdigest(username, username_len, digest);

    if (dir_exists(data_fd, digest)) {
        warn("User already exists");
        return;
    }

    if (!ensure_dir(data_fd, digest)) {
        error("Error creating user directory");
        return;
    }

    dfd = openat(data_fd, digest, O_DIRECTORY);
    if (dfd < 0) {
        error("Error opening user directory");
        return;
    }

    fd = openat(dfd, "password", O_CREAT | O_RDWR, 0400);    // Open password file in read-only mode
    if (fd < 0) {
        error("Error creating password file");
        goto err;
    }

    if (!write_string(fd, password)) {
        error("Error writing password to file");
        goto err;
    }

    close(dfd);
    close(fd);
    success("User created successfully");
    return;
err:
    if (dfd != -1)
        close(dfd);
    if (fd != -1)
        close(fd);
}

void login() {
    int dfd, fd;
    ssize_t username_len, password_len;
    char username[MAX_USERNAME_LEN];
    char password[MAX_PASSWORD_LEN];
    char digest[HEXDIGEST_LEN+1];
    char json_token[MAX_JSON_TOKEN_LEN];
    unsigned char nonce[32] = {0};
    unsigned char hexnonce[sizeof(nonce) * 2 + 1] = {0};
    size_t enc_json_token_len = 0;
    unsigned char *enc_json_token;
    char response[64 + 1 + 1] = {0};

    prompt("Enter username");
    username_len = read_line(0, username, sizeof(username));
    if (username_len < 0) {
        error("Error reading username");
        return;
    }

    hexdigest(username, username_len, digest);

    if (!dir_exists(data_fd, digest)) {
        warn("User does not exist");
        return;
    }

    dfd = openat(data_fd, digest, O_DIRECTORY);
    if (dfd < 0) {
        error("Error opening user directory");
        return;
    }

    fd = openat(dfd, "password", O_RDONLY);
    if (!fd) {
        error("Error opening password file");
        goto err;
    }

    password_len = read_string(fd, password);
    if (password_len < 0) {
        error("Error reading password");
        goto err;
    }
    close(fd);

    rndbytes(nonce, sizeof(nonce));

    for (size_t i = 0; i < sizeof(nonce); i++)
        sprintf((char *)&hexnonce[i*2], "%02hhx", nonce[i]);
    hexnonce[sizeof(hexnonce) - 1] = '\0';

    snprintf(json_token, sizeof(json_token), "{\"username\": \"%s\", \"nonce\": \"%s\"}", username, hexnonce);

    enc_json_token = encrypt(json_token, username, password, &enc_json_token_len);
    
    info("Challenge: ");
    hexprint(enc_json_token, enc_json_token_len);
    puts("");

    free(enc_json_token);

    prompt("Enter response");
    read_line(0, response, sizeof(response) - 1);

    if (memcmp(response, hexnonce, sizeof(hexnonce))) {
        warn("Login failed");
        return;
    }

    current_dir = dfd;
    logged_in = true;
    success("User logged in successfully");
    return;
err:
    if (dfd != -1)
        close(dfd);
    if (fd != -1)
        close(fd);
}

void auth_menu() {
    int choice = 0;

    puts("==============================");
    puts("=         LOGIN MENU         =");
    puts("==============================");
    puts("= 1. Signup                  =");
    puts("= 2. Login                   =");
    puts("= 3. Exit                    =");
    puts("==============================");
    prompt("Enter choice");

    choice = get_int();
    putchar('\n');
    switch (choice) {
        case AUTH_SIGNUP:
            debug_print("Signup\n");
            signup();
            break;
        case AUTH_LOGIN:
            debug_print("Login\n");
            login();
            break;
        case AUTH_EXIT:
            exit(0);
        default:
            warn("Invalid choice");
    }
    putchar('\n');
}

void vault_menu() {
    int choice = 0;

    puts("==============================");
    puts("=         VAULT MENU         =");
    puts("==============================");
    puts("= 1. List                    =");
    puts("= 2. Create                  =");
    puts("= 3. Open                    =");
    puts("= 4. Close                   =");
    puts("= 5. List open               =");
    puts("= 6. Enter                   =");
    puts("= 7. Logout                  =");
    puts("==============================");
    prompt("Enter choice");

    choice = get_int();
    putchar('\n');
    switch (choice) {
        case VAULT_LIST:
            debug_print("List\n");
            list_vaults();
            break;
        case VAULT_CREATE:
            debug_print("Create\n");
            create_vault();
            break;
        case VAULT_OPEN:
            debug_print("Open\n");
            open_vault();
            break;
        case VAULT_CLOSE:
            debug_print("Close\n");
            close_vault();
            break;
        case VAULT_LIST_OPEN:
            debug_print("List open\n");
            list_open_vaults();
            break;
        case VAULT_ENTER:
            debug_print("Enter\n");
            enter_vault();
            break;
        case VAULT_LOGOUT:
            debug_print("Logout\n");
            logout();
            break;
        default:
            warn("Invalid choice");
    }
    putchar('\n');
}

void recipe_menu() {
    int choice = 0;

    puts("==============================");
    puts("=        RECIPE MENU         =");
    puts("==============================");
    puts("= 1. List                    =");
    puts("= 2. Create                  =");
    puts("= 3. Open                    =");
    puts("= 4. Close                   =");
    puts("= 5. Save                    =");
    puts("= 6. Discard                 =");
    puts("= 7. List open               =");
    puts("= 8. Select                  =");
    puts("= 9. Show                    =");
    puts("= 10. Edit                   =");
    puts("= 11. Back                   =");
    puts("==============================");
    prompt("Enter choice");

    choice = get_int();
    putchar('\n');
    switch (choice) {
        case RECIPE_LIST:
            debug_print("List\n");
            list_recipes();
            break;
        case RECIPE_CREATE:
            debug_print("Create\n");
            create_recipe();
            break;
        case RECIPE_OPEN:
            debug_print("Open\n");
            open_recipe();
            break;
        case RECIPE_CLOSE:
            debug_print("Close\n");
            close_recipe();
            break;
        case RECIPE_SAVE:
            debug_print("Save\n");
            save_recipe();
            break;
        case RECIPE_DISCARD:
            debug_print("Discard\n");
            discard_recipe();
            break;
        case RECIPE_LIST_OPEN:
            debug_print("List open\n");
            list_open_recipes();
            break;
        case RECIPE_SELECT:
            debug_print("Select\n");
            select_recipe();
            break;
        case RECIPE_SHOW:
            debug_print("Show\n");
            show_recipe();
            break;
        case RECIPE_EDIT:
            debug_print("Edit\n");
            edit_recipe();
            break;
        case RECIPE_BACK:
            debug_print("Back\n");
            back();
            break;
        default:
            warn("Invalid choice");
    }
    putchar('\n');
}


void set_seccomp() {
    #define VALIDATE_ARCHITECTURE \
    BPF_STMT(BPF_LD+BPF_W+BPF_ABS, (offsetof(struct seccomp_data, arch))), \
    BPF_JUMP(BPF_JMP+BPF_JEQ+BPF_K, AUDIT_ARCH_X86_64, 1, 0), \
    BPF_STMT(BPF_RET+BPF_K, SECCOMP_RET_KILL)

    #define EXAMINE_SYSCALL \
        BPF_STMT(BPF_LD+BPF_W+BPF_ABS, (offsetof(struct seccomp_data, nr)))

    #define ALLOW_SYSCALL(name) \
        BPF_JUMP(BPF_JMP+BPF_JEQ+BPF_K, __NR_##name, 0, 1), \
        BPF_STMT(BPF_RET+BPF_K, SECCOMP_RET_ALLOW)

    #define KILL_PROCESS \
        BPF_STMT(BPF_RET+BPF_K, SECCOMP_RET_KILL)

	struct sock_filter seccomp_filter[] = {
		VALIDATE_ARCHITECTURE,
		EXAMINE_SYSCALL,
        ALLOW_SYSCALL(brk),
        ALLOW_SYSCALL(close),
		ALLOW_SYSCALL(exit),
		ALLOW_SYSCALL(exit_group),
        ALLOW_SYSCALL(fcntl),
        ALLOW_SYSCALL(fstat),
        ALLOW_SYSCALL(futex),
        ALLOW_SYSCALL(getdents64),
        ALLOW_SYSCALL(getrandom),
        // ALLOW_SYSCALL(gettid),
        // ALLOW_SYSCALL(ioctl),
        ALLOW_SYSCALL(mkdirat),
        ALLOW_SYSCALL(mmap),
        ALLOW_SYSCALL(mprotect),
        ALLOW_SYSCALL(newfstatat),
        ALLOW_SYSCALL(openat),
        ALLOW_SYSCALL(read),
        // ALLOW_SYSCALL(rt_sigprocmask),
        ALLOW_SYSCALL(write),
        // ALLOW_SYSCALL(writev),
		KILL_PROCESS,
	};

    struct sock_fprog prog = {
        .len = (unsigned short)(sizeof(seccomp_filter) / sizeof(struct sock_filter)),
        .filter = (struct sock_filter*)&seccomp_filter,
    };

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
        die("prctl(NO_NEW_PRIVS)");

    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog, 0, 0, 0))
        die("prctl(PR_SET_SECCOMP)");
}

int main() {

    set_buf();
    set_seccomp();

    debug_print("==============================\n");

    if (!ensure_dir(AT_FDCWD, "/data")) {
        die("Error creating data directory");
    }

    data_fd = open("/data", O_DIRECTORY);
    if (data_fd < 0) {
        die("Error opening data directory");
    }

    while (true) {
        if (current_vault != NULL) {
            recipe_menu();
        } else if (logged_in) {
            vault_menu();
        } else {
            auth_menu();
        }
    }
}
