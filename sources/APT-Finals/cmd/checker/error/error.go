package error

import "runtime/debug"

type CheckerError struct {
	Message string
	Detail  error
	Stack   string
}

func New(msg string, detail error) *CheckerError {
	return &CheckerError{
		msg,
		detail,
		string(debug.Stack()),
	}
}
