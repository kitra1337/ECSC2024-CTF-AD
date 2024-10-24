package store2

import (
	"apt/cmd/checker/error"
	"apt/cmd/checker/utils"
	"apt/pkg/models"
	"apt/pkg/ws"
	"fmt"
	"os"
	"slices"
)

func GetFlag(host, flag string) *error.CheckerError {
	flagId, err := utils.ReadFlagId[FlagIdPrivate](flag)
	if err != nil {
		return err
	}

	// Connect clients
	var client1, client2 *ws.Client
	if err := utils.RandOrder(
		func() *error.CheckerError {
			client1, err = utils.NewClient(host)
			if err != nil {
				return err
			}

			return nil
		},
		func() *error.CheckerError {
			client2, err = utils.NewClient(host)
			if err != nil {
				return err
			}

			return nil
		},
	); err != nil {
		return err
	}

	// Register/login
	var username1 string
	if err := utils.RandOrder(
		func() *error.CheckerError {
			// If the friend was already created, just connect
			if len(flagId.FriendUsername) > 0 {
				_, _ = fmt.Fprintf(os.Stderr, "Friend already created: %s\n", flagId.FriendUsername)

				if err := utils.Login(client1, flagId.FriendUsername, flagId.FriendPassword); err != nil {
					return err
				}

				username1 = flagId.FriendUsername
			} else {
				if err := utils.RegisterAndLogin(client1, "", &username1, nil, nil); err != nil {
					return err
				}
			}

			return nil
		},
		func() *error.CheckerError {
			if err := utils.Login(client2, flagId.Username, flagId.Password); err != nil {
				return err
			}

			return nil
		},
	); err != nil {
		return err
	}

	// If the friend was already created
	var friends []models.Friend
	if len(flagId.FriendUsername) > 0 {
		friends, err = utils.ListFriends(client1)
		if err != nil {
			return err
		}

		// Check if the invite was already accepted or accept it
		if slices.ContainsFunc(friends, func(f models.Friend) bool { return f.Username == flagId.Username && !f.Pending }) {
			_, _ = fmt.Fprintf(os.Stderr, "Friend already accepted\n")
		} else {
			if err := utils.AddFriend(client1, flagId.Username, flagId.FriendInvite); err != nil {
				return err
			}

			friends, err = utils.ListFriends(client1)
			if err != nil {
				return err
			}
		}
	} else {
		invite, err := utils.InviteFriend(client2, username1)
		if err != nil {
			return err
		}

		if err := utils.AddFriend(client1, flagId.Username, invite); err != nil {
			return err
		}

		friends, err = utils.ListFriends(client1)
		if err != nil {
			return err
		}
	}

	for _, friend := range friends {
		if friend.Username == flagId.Username && friend.Secret == flag {
			return nil
		}
	}

	return error.New("Could not find flag", nil)
}
