package proto

import (
	"fmt"
	"math/big"
)

type Type int32

const (
	TypeUnknown Type = iota
	TypeRegister
	TypeLogin
	TypeCreateMatch
	TypeListMatches
	TypeListPlayedMatches
	TypePlayMatch
	TypePoint
	TypeCollision
	TypeListFriends
	TypeInviteFriend
	TypeAddFriend
)

type Request struct {
	Type Type
	Data []uint8
}

func (r *Request) Marshal() ([]byte, error) {
	if r.Type == TypeUnknown {
		return nil, fmt.Errorf("unknown type")
	}

	return marshal(r)
}

func (r *Request) Unmarshal(data []byte) error {
	rr, err := unmarshal[Request](data)
	if err != nil {
		return err
	}

	*r = *rr
	return nil
}

func PackRequest[T any](typ Type, data *T) (*Request, error) {
	dataBytes, err := marshal[T](data)
	if err != nil {
		return nil, err
	}

	return &Request{Type: typ, Data: dataBytes}, nil
}

func UnpackRequest[T any](req *Request, data *T) error {
	t, err := unmarshal[T](req.Data)
	if err != nil {
		return err
	}

	*data = *t
	return nil
}

type RequestDataListMatches struct {
}

type RequestDataListPlayedMatches struct {
}

type RequestDataListFriends struct {
}

type RequestDataRegister struct {
	Username string
	Secret   string
}

type RequestDataLogin struct {
	Username string
	Password string
}

type RequestDataCreateMatch struct {
	Prize      string
	SecretKey  string
	Difficulty int
}

type RequestDataPlayMatch struct {
	ID uint64
}

type RequestDataPoint struct {
}

type RequestDataCollision struct {
	BallX    float64
	BallY    float64
	ClientX  float64
	ClientY  float64
	BotX     float64
	BotY     float64
	Rnd1     *big.Int
	Rnd2     *big.Int
	IsClient bool
}

type RequestDataAddFriend struct {
	Username string
	Invite   string
}

type RequestDataInviteFriend struct {
	Username string
}
