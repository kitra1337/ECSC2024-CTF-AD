package proto

import (
	"apt/pkg/models"
)

type Response struct {
	Data []byte
}

func (r *Response) Marshal() ([]byte, error) {
	return marshal(r)
}

func (r *Response) Unmarshal(data []byte) error {
	rr, err := unmarshal[Response](data)
	if err != nil {
		return err
	}

	*r = *rr
	return nil
}

func PackResponse[T any](data *T) (*Response, error) {
	dataBytes, err := marshal[T](data)
	if err != nil {
		return nil, err
	}

	return &Response{Data: dataBytes}, nil
}

func UnpackResponse[T any](req *Response) (*T, error) {
	return unmarshal[T](req.Data)
}

type ResponseDataRegister struct {
	Password string
}

type ResponseDataLogin struct {
	Ok bool
}

type ResponseDataCreateMatch struct {
	ID uint64
}

type ResponseDataPlayMatch struct {
}

type ResponseDataPoint struct {
	End          bool
	Prize        string
	ClientPoints int32
	BotPoints    int32
}

type ResponseDataCollision struct {
	X1 float64
	Y1 float64
}

type ResponseDataListPlayedMatches struct {
	Matches []models.PlayedMatch
}

type ResponseDataListMatches struct {
	Matches []models.Match
}

type ResponseDataListFriends struct {
	Friends []models.Friend
}

type ResponseDataAddFriend struct {
}

type ResponseDataInviteFriend struct {
	Invite string
}
