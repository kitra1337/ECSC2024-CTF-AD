package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"encoding/base64"
	"fmt"
)

func EncryptInvite(key []byte, username string) (string, error) {
	bc, err := aes.NewCipher(key[:32])
	if err != nil {
		return "", err
	}

	sc := cipher.NewCBCEncrypter(bc, key[32:])

	paddedUsername := Pad([]byte(username), bc.BlockSize())

	inviteBytes := make([]byte, len(paddedUsername))
	sc.CryptBlocks(inviteBytes, paddedUsername)

	return base64.RawStdEncoding.EncodeToString(inviteBytes), nil
}

func DecryptInvite(key []byte, invite string) ([]byte, error) {
	bc, err := aes.NewCipher(key[:32])
	if err != nil {
		return nil, err
	}

	if len(invite)*3/4%bc.BlockSize() != 0 {
		return nil, fmt.Errorf("malformed invite")
	}

	inviteBytes, err := base64.RawStdEncoding.DecodeString(invite)
	if err != nil {
		return nil, err
	}

	sc := cipher.NewCBCDecrypter(bc, key[32:])
	sc.CryptBlocks(inviteBytes, inviteBytes)

	ok, unpaddedInvite := Unpad(inviteBytes)
	if !ok {
		return nil, fmt.Errorf("invalid padding")
	}

	return unpaddedInvite, nil
}
