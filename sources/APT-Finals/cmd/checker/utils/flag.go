package utils

import (
	"apt/cmd/checker/error"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

const flagIdsDir = "flags"

func hashFlag(flag string) string {
	sum := md5.Sum([]byte(flag))
	return hex.EncodeToString(sum[:])
}

func ReadFlagId[T any](flag string) (*T, *error.CheckerError) {
	_, _ = fmt.Fprintf(os.Stderr, "Flag: %s\n", flag)

	file, err := os.Open(filepath.Join(flagIdsDir, hashFlag(flag)+".json"))
	if err != nil {
		return nil, error.New("Failed reading flag id", err)
	}

	defer func() { _ = file.Close() }()

	var data T
	if err := json.NewDecoder(file).Decode(&data); err != nil {
		return nil, error.New("Failed decoding flag id", err)
	}

	return &data, nil
}

func WriteFlagId[T any](flag string, data *T) *error.CheckerError {
	_, _ = fmt.Fprintf(os.Stderr, "Flag: %s\n", flag)

	file, err := os.OpenFile(filepath.Join(flagIdsDir, hashFlag(flag)+".json"), os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0644)
	if err != nil {
		return error.New("Failed writing flag id", err)
	}

	defer func() { _ = file.Close() }()

	if err := json.NewEncoder(file).Encode(data); err != nil {
		return error.New("Failed encoding flag id", err)
	}

	return nil
}
