#!/bin/bash -e

SOURCE_FILE="$(dirname $(realpath $0))/checker"
DEST_FILE="/localfiles/service3-1-checker"
LOCK_FILE="$DEST_FILE.lock"

copy_file_safely() {
    flock -x 200 || { echo "Failed to acquire lock"; exit 1; }

    if [[ -f "$DEST_FILE" ]]; then
        echo "Destination file already exists."
    elif [[ -f "$SOURCE_FILE" ]]; then
        cp "$SOURCE_FILE" "$DEST_FILE"
        echo "File copied successfully."
    else
        echo "Source file does not exist."
    fi
}

exec 200>"$LOCK_FILE"
copy_file_safely
exec 200>&-
