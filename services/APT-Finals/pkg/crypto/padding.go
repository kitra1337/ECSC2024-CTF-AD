package crypto

import "bytes"

func Pad(data []byte, blockSize int) []byte {
	padding := blockSize - len(data)%blockSize
	pad := bytes.Repeat([]byte{byte(padding)}, padding)
	return append(data, pad...)
}

func Unpad(data []byte) (bool, []byte) {
	if len(data) == 0 {
		return false, nil
	}

	padding := int(data[len(data)-1])
	if padding >= len(data) {
		return false, nil
	}

	for _, b := range data[len(data)-padding:] {
		if b != byte(padding) {
			return false, nil
		}
	}

	return true, data[:len(data)-padding]
}
