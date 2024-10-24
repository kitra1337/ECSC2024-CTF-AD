#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/random.h>
#include <openssl/sha.h>

#include "util.h"

char alphabet[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

void die(const char *msg) {
    error(msg);
    exit(1);
}

void prompt(const char *msg) {
    printf("[%s]> ", msg);
}

void success(const char *msg) {
    printf("[+] %s\n", msg);
}

void error(const char *msg) {
    printf("[-] %s\n", msg);
}

void info(const char *msg) {
    printf("[*] %s\n", msg);
}

void warn(const char *msg) {
    printf("[!] %s\n", msg);
}

int get_int() {
    char input[16];
    fgets(input, sizeof(input), stdin);
    return atoi(input);
}

long get_long() {
    char input[32];
    fgets(input, sizeof(input), stdin);
    return strtoul(input, NULL, 10);
}

bool read_bool() {
    char input[16];
    fgets(input, sizeof(input), stdin);
    return input[0] == 'y' || input[0] == 't';
}

int random_int() {
    int res;
    if (getrandom(&res, sizeof(res), 0) == -1)
        die("Error generating random number");
    return res;
}

long random_long() {
    long res;
    if (getrandom(&res, sizeof(res), 0) == -1)
        die("Error generating random number");
    return res;
}

void random_id(char *id) {
    for (size_t i = 0; i < ID_LEN - 1; i++) {
        id[i] = alphabet[random_int() % (sizeof(alphabet) - 1)];
    }
    id[ID_LEN - 1] = '\0';
}

bool read_exactly(int fd, void *buf, size_t size) {
    size_t done = 0;
    while (done != size) {
        ssize_t count = read(fd, (char *)buf + done, size - done);
        if (count <= 0)
            return false;
        done += count;
    }
    return true;
}

bool read_id(int fd, char *buf) {
    if (!read_exactly(fd, buf, ID_LEN - 1))
        return false;
    buf[ID_LEN - 1] = '\0';
    getchar(); // Consume newline

    // Check if all characters are valid
    for (int i = 0; i < ID_LEN - 1; i++) {
        if (strchr(alphabet, buf[i]) == NULL) {
            return false;
        }
    }

    return true;
}

ssize_t read_line(int fd, char *buf, size_t size) {
    if (size == 0) return -1;

    size_t count = 0;
    while (count < size) {
        ssize_t res = read(fd, buf + count, 1);
        if (res <= 0) {
            if (res == 0) break; // End of file
            return -1; // Error
        }
        if (buf[count] == '\n') break;
        count++;
    }
    buf[count] = '\0';
    return count;
}

ssize_t read_string(int fd, char *buf) {
    unsigned int len;
    if (!read_exactly(fd, &len, sizeof(len))) {
        return -1;
    }
    if (!read_exactly(fd, buf, len)) {
        return -1;
    }
    buf[len] = '\0';
    return len;
}

bool write_exactly(int fd, const void *buf, size_t size) {
    size_t done = 0;
    while (done != size) {
        ssize_t count = write(fd, (const char *)buf + done, size - done);
        if (count <= 0)
            return false;
        done += count;
    }
    return true;
}

bool write_string(int fd, char *buf) {
    unsigned int len = strlen(buf);
    return write_exactly(fd, &len, sizeof(len)) && write_exactly(fd, buf, len);
}

void set_buf() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

void hexprint(const void *buf, size_t size) {
    for (size_t i = 0; i < size; i++)
        printf("%02hhx", ((unsigned char *)buf)[i]);
}

void hexdigest(const void *buf, size_t size, char *out) {
    unsigned char digest[SHA256_DIGEST_LENGTH];
    SHA256(buf, size, digest);
    for (size_t i = 0; i < sizeof(digest); i++)
        sprintf(&out[i * 2], "%02hhx", digest[i]);
}

bool dir_exists(int dfd, const char *path) {
    struct stat sb;
    if (fstatat(dfd, path, &sb, 0) == 0 && S_ISDIR(sb.st_mode))
        return true;
    else
        return false;
}

bool ensure_dir(int dfd, const char *path) {
    if (mkdirat(dfd, path, 0700) == -1) {
        if (errno != EEXIST)
            return false;
    }
    return true;
}

void rndbytes(unsigned char *x, size_t xlen) {
    ssize_t i;
    while (xlen > 0) {
        i = getrandom(x, xlen, 0);
        if (i < 0)
            die("Random generation failed");
        x += i;
        xlen -= i;
    }
}