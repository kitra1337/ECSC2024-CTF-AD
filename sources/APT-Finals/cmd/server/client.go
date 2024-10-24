package main

import (
	"apt"
	"apt/cmd/server/db"
	"apt/cmd/server/match"
	"apt/pkg/crypto"
	"apt/pkg/models"
	"apt/pkg/proto"
	"context"
	"crypto/rand"
	"crypto/subtle"
	"encoding/hex"
	"fmt"
	"log/slog"
	"slices"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

type Client struct {
	db *db.DB

	log  *slog.Logger
	conn *websocket.Conn

	username *string
	match    *match.Match
}

func (c *Client) handleRequest(ctx context.Context, req *proto.Request) (*proto.Response, error) {
	c.log.With("type", req.Type).Debug("handling request")

	switch req.Type {
	case proto.TypeRegister:
		var reqData proto.RequestDataRegister
		if err := proto.UnpackRequest(req, &reqData); err != nil {
			return nil, err
		}

		if len(reqData.Username) < apt.UsernameMinLength {
			return nil, fmt.Errorf("username too short")
		}

		passwordBytes := make([]byte, apt.PasswordLength/2)
		_, _ = rand.Read(passwordBytes)
		password := hex.EncodeToString(passwordBytes)

		if err := c.db.Register(ctx, reqData.Username, password, strings.TrimSpace(reqData.Secret)); err != nil {
			return nil, err
		}

		return proto.PackResponse(&proto.ResponseDataRegister{Password: password})
	case proto.TypeLogin:
		if c.username != nil {
			return nil, fmt.Errorf("already logged in")
		}

		var reqData proto.RequestDataLogin
		if err := proto.UnpackRequest(req, &reqData); err != nil {
			return nil, err
		}

		ok, err := c.db.Login(ctx, reqData.Username, reqData.Password)
		if err != nil {
			return nil, err
		}

		if ok {
			c.username = &reqData.Username
			c.match = nil
		} else {
			c.username = nil
			c.match = nil
		}

		return proto.PackResponse(&proto.ResponseDataLogin{Ok: ok})
	case proto.TypeCreateMatch:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		}

		var reqData proto.RequestDataCreateMatch
		if err := proto.UnpackRequest(req, &reqData); err != nil {
			return nil, err
		}

		id, err := c.db.CreateMatch(ctx, *c.username, reqData.Prize, reqData.SecretKey, reqData.Difficulty)
		if err != nil {
			return nil, err
		}

		return proto.PackResponse(&proto.ResponseDataCreateMatch{ID: id})
	case proto.TypeListMatches:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		}

		matches, err := c.db.ListMatches(ctx)
		if err != nil {
			return nil, err
		}

		return proto.PackResponse(&proto.ResponseDataListMatches{Matches: matches})
	case proto.TypeListPlayedMatches:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		}

		matches, err := c.db.ListPlayedMatches(ctx, *c.username)
		if err != nil {
			return nil, err
		}

		return proto.PackResponse(&proto.ResponseDataListPlayedMatches{Matches: matches})
	case proto.TypePlayMatch:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		} else if c.match != nil {
			return nil, fmt.Errorf("match is already started")
		}

		var reqData proto.RequestDataPlayMatch
		if err := proto.UnpackRequest(req, &reqData); err != nil {
			return nil, err
		}

		matchPriv, err := c.db.GetMatch(ctx, reqData.ID)
		if err != nil {
			return nil, err
		} else if matchPriv == nil {
			return nil, fmt.Errorf("match does not exist")
		}

		if err := c.db.PlayMatch(ctx, matchPriv.ID, *c.username); err != nil {
			return nil, err
		}

		log := c.log.With("match", matchPriv.ID)
		c.match = match.New(log, matchPriv)
		return proto.PackResponse(&proto.ResponseDataPlayMatch{})
	case proto.TypePoint:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		} else if c.match == nil {
			return nil, fmt.Errorf("no ongoing match")
		}

		respData, err := c.match.HandlePoint()
		if err != nil {
			return nil, err
		}

		if respData.End {
			if err := c.db.SetMatchWinner(ctx, c.match.ID(), respData.ClientPoints > respData.BotPoints, *c.username); err != nil {
				return nil, err
			}

			c.match = nil
		}

		return proto.PackResponse(respData)
	case proto.TypeCollision:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		} else if c.match == nil {
			return nil, fmt.Errorf("no ongoing match")
		}

		var reqData proto.RequestDataCollision
		if err := proto.UnpackRequest(req, &reqData); err != nil {
			return nil, err
		}

		respData, err := c.match.HandleCollision(&reqData)
		if err != nil {
			return nil, err
		}

		return proto.PackResponse(respData)
	case proto.TypeListFriends:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		}

		friends, err := c.db.ListFriends(ctx, *c.username)
		if err != nil {
			return nil, err
		}

		slices.SortFunc(friends, func(a, b models.Friend) int {
			return int(a.MatchesWon - b.MatchesWon)
		})

		return proto.PackResponse(&proto.ResponseDataListFriends{Friends: friends})
	case proto.TypeInviteFriend:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		}

		var reqData proto.RequestDataInviteFriend
		if err := proto.UnpackRequest(req, &reqData); err != nil {
			return nil, err
		}

		key := make([]byte, 48)
		_, _ = rand.Read(key)

		if err := c.db.CreateFriendInvite(ctx, *c.username, reqData.Username, key); err != nil {
			return nil, err
		}

		invite, err := crypto.EncryptInvite(key, reqData.Username)
		if err != nil {
			return nil, err
		}

		return proto.PackResponse(&proto.ResponseDataInviteFriend{Invite: invite})
	case proto.TypeAddFriend:
		if c.username == nil {
			return nil, fmt.Errorf("not logged in")
		}

		var reqData proto.RequestDataAddFriend
		if err := proto.UnpackRequest(req, &reqData); err != nil {
			return nil, err
		}

		inviteKey, err := c.db.GetFriendInviteKey(ctx, *c.username, reqData.Username)
		if err != nil {
			_ = c.db.RemoveFriend(ctx, *c.username, reqData.Username)
			return nil, err
		} else if len(inviteKey) == 0 {
			_ = c.db.RemoveFriend(ctx, *c.username, reqData.Username)
			return nil, fmt.Errorf("invalid invite")
		}

		invitedUser, err := crypto.DecryptInvite(inviteKey, strings.TrimSpace(reqData.Invite))
		if err != nil {
			_ = c.db.RemoveFriend(ctx, *c.username, reqData.Username)
			return nil, err
		}

		if subtle.ConstantTimeCompare(invitedUser, []byte(*c.username)) == 0 {
			_ = c.db.RemoveFriend(ctx, *c.username, reqData.Username)
			return nil, fmt.Errorf("invalid invite")
		}

		return proto.PackResponse(&proto.ResponseDataAddFriend{})
	default:
		return nil, fmt.Errorf("unknown type: %d", req.Type)
	}
}

func (c *Client) Handle(ctx_ context.Context) {
	ctx, cancel := context.WithTimeout(ctx_, 120*time.Second)
	defer cancel()

	c.log.Debug("entering websocket handle loop")

	for {
		deadline, _ := ctx.Deadline()
		_ = c.conn.SetReadDeadline(deadline)
		_ = c.conn.SetWriteDeadline(deadline)

		_, reqBytes, err := c.conn.ReadMessage()
		if err != nil {
			if deadline.Before(time.Now()) {
				break
			}

			c.log.With("error", err).Error("failed reading from websocket")
			break
		}

		var req proto.Request
		if err = req.Unmarshal(reqBytes); err != nil {
			c.log.With("error", err).Error("failed unmarshalling request")
			break
		}

		resp, err := c.handleRequest(ctx, &req)
		if err != nil {
			if deadline.Before(time.Now()) {
				break
			}

			c.log.With("error", err).Error("failed handling request")
			break
		}

		respBytes, err := resp.Marshal()
		if err != nil {
			c.log.With("error", err).Error("failed marshalling response")
			break
		}

		if err = c.conn.WriteMessage(websocket.BinaryMessage, respBytes); err != nil {
			if deadline.Before(time.Now()) {
				break
			}

			c.log.With("error", err).Error("failed writing response")
			break
		}
	}

	c.log.Debug("exited websocket handle loop")
}
