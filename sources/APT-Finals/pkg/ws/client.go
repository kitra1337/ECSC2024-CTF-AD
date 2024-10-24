package ws

import (
	"apt/pkg/models"
	"apt/pkg/proto"
	"fmt"
	"math/big"
	"net/http"
	"net/url"

	"github.com/jakecoffman/cp"

	"github.com/gorilla/websocket"
)

type Client struct {
	c *websocket.Conn

	username string
}

func NewClient(host string, header http.Header) (*Client, error) {
	u := url.URL{Scheme: "ws", Host: host, Path: "/"}
	c, _, err := websocket.DefaultDialer.Dial(u.String(), header)
	if err != nil {
		return nil, err
	}

	return &Client{c: c}, nil
}

func (c *Client) sendRequest(req *proto.Request) (*proto.Response, error) {
	reqBytes, err := req.Marshal()
	if err != nil {
		return nil, fmt.Errorf("failed marshalling request: %w", err)
	}

	if err = c.c.WriteMessage(websocket.BinaryMessage, reqBytes); err != nil {
		return nil, fmt.Errorf("failed writing to websocket: %w", err)
	}

	_, respBytes, err := c.c.ReadMessage()
	if err != nil {
		return nil, fmt.Errorf("failed reading from websocket: %w", err)
	}

	var resp proto.Response
	if err = resp.Unmarshal(respBytes); err != nil {
		return nil, fmt.Errorf("failed unmarshalling response: %w", err)
	}

	return &resp, nil
}

func (c *Client) Username() string {
	return c.username
}

func (c *Client) Login(username, password string) (bool, error) {
	if req, err := proto.PackRequest(proto.TypeLogin, &proto.RequestDataLogin{Username: username, Password: password}); err != nil {
		return false, err
	} else if resp, err := c.sendRequest(req); err != nil {
		return false, err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataLogin](resp); err != nil {
		return false, err
	} else {
		if respData.Ok {
			c.username = username
		}

		return respData.Ok, nil
	}
}

func (c *Client) Register(username, secret string) (string, error) {
	if req, err := proto.PackRequest(proto.TypeRegister, &proto.RequestDataRegister{Username: username, Secret: secret}); err != nil {
		return "", err
	} else if resp, err := c.sendRequest(req); err != nil {
		return "", err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataRegister](resp); err != nil {
		return "", err
	} else {
		return respData.Password, nil
	}
}

func (c *Client) CreateMatch(prize, secretKey string, difficulty int) (uint64, error) {
	if req, err := proto.PackRequest(proto.TypeCreateMatch, &proto.RequestDataCreateMatch{Prize: prize, SecretKey: secretKey, Difficulty: difficulty}); err != nil {
		return 0, err
	} else if resp, err := c.sendRequest(req); err != nil {
		return 0, err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataCreateMatch](resp); err != nil {
		return 0, err
	} else {
		return respData.ID, nil
	}
}

func (c *Client) ListMatches() ([]models.Match, error) {
	if req, err := proto.PackRequest(proto.TypeListMatches, &proto.RequestDataListMatches{}); err != nil {
		return nil, err
	} else if resp, err := c.sendRequest(req); err != nil {
		return nil, err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataListMatches](resp); err != nil {
		return nil, err
	} else {
		return respData.Matches, nil
	}
}

func (c *Client) PlayMatch(id uint64) error {
	if req, err := proto.PackRequest(proto.TypePlayMatch, &proto.RequestDataPlayMatch{ID: id}); err != nil {
		return err
	} else if _, err := c.sendRequest(req); err != nil {
		return err
	} else {
		return nil
	}
}

func (c *Client) ListPlayedMatches() ([]models.PlayedMatch, error) {
	if req, err := proto.PackRequest(proto.TypeListPlayedMatches, &proto.RequestDataListPlayedMatches{}); err != nil {
		return nil, err
	} else if resp, err := c.sendRequest(req); err != nil {
		return nil, err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataListPlayedMatches](resp); err != nil {
		return nil, err
	} else {
		return respData.Matches, nil
	}
}

func (c *Client) HandlePoint() (*proto.ResponseDataPoint, error) {
	if req, err := proto.PackRequest(proto.TypePoint, &proto.RequestDataPoint{}); err != nil {
		return nil, err
	} else if resp, err := c.sendRequest(req); err != nil {
		return nil, err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataPoint](resp); err != nil {
		return nil, err
	} else {
		return respData, nil
	}
}

func (c *Client) HandleCollision(ball cp.Vector, client cp.Vector, bot cp.Vector, isClient bool, rnd1, rnd2 *big.Int) (*proto.ResponseDataCollision, error) {
	if req, err := proto.PackRequest(proto.TypeCollision, &proto.RequestDataCollision{
		BallX:    ball.X,
		BallY:    ball.Y,
		ClientX:  client.X,
		ClientY:  client.Y,
		BotX:     bot.X,
		BotY:     bot.Y,
		Rnd1:     rnd1,
		Rnd2:     rnd2,
		IsClient: isClient,
	}); err != nil {
		return nil, err
	} else if resp, err := c.sendRequest(req); err != nil {
		return nil, err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataCollision](resp); err != nil {
		return nil, err
	} else {
		return respData, nil
	}
}

func (c *Client) ListFriends() ([]models.Friend, error) {
	if req, err := proto.PackRequest(proto.TypeListFriends, &proto.RequestDataListFriends{}); err != nil {
		return nil, err
	} else if resp, err := c.sendRequest(req); err != nil {
		return nil, err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataListFriends](resp); err != nil {
		return nil, err
	} else {
		return respData.Friends, nil
	}
}

func (c *Client) AddFriend(username, invite string) error {
	if req, err := proto.PackRequest(proto.TypeAddFriend, &proto.RequestDataAddFriend{Username: username, Invite: invite}); err != nil {
		return err
	} else if _, err := c.sendRequest(req); err != nil {
		return err
	} else {
		return nil
	}
}

func (c *Client) InviteFriend(username string) (string, error) {
	if req, err := proto.PackRequest(proto.TypeInviteFriend, &proto.RequestDataInviteFriend{Username: username}); err != nil {
		return "", err
	} else if resp, err := c.sendRequest(req); err != nil {
		return "", err
	} else if respData, err := proto.UnpackResponse[proto.ResponseDataInviteFriend](resp); err != nil {
		return "", err
	} else {
		return respData.Invite, nil
	}
}
