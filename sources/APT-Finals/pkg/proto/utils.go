package proto

import (
	"bytes"
	"encoding/gob"
)

func unmarshal[T any](data []byte) (*T, error) {
	var t T
	if err := gob.NewDecoder(bytes.NewBuffer(data)).Decode(&t); err != nil {
		return nil, err
	}

	return &t, nil
}

func marshal[T any](data *T) ([]byte, error) {
	var buf bytes.Buffer
	if err := gob.NewEncoder(&buf).Encode(data); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}
