package utils

import (
	"apt/cmd/checker/error"
	"math/rand"
	"reflect"
)

func RandStr(length int) string {
	const alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012345689"

	str := ""
	for i := 0; i < length; i++ {
		str += string(alphabet[rand.Intn(len(alphabet))])
	}
	return str
}

func RandOrder(funcs ...func() *error.CheckerError) *error.CheckerError {
	rand.Shuffle(len(funcs), reflect.Swapper(funcs))
	for _, fn := range funcs {
		if err := fn(); err != nil {
			return err
		}
	}
	return nil
}
