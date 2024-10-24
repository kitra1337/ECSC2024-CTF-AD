package store2

import (
	"apt/cmd/checker/error"
	"apt/cmd/checker/utils"
	"math/rand/v2"
)

func PutFlag(host, flag string) (any, *error.CheckerError) {
	client1, err := utils.NewClient(host)
	if err != nil {
		return nil, err
	}

	flagId := &FlagIdPrivate{}

	if err := utils.RegisterAndLogin(client1, flag, &flagId.Username, nil, &flagId.Password); err != nil {
		return nil, err
	}

	// Occasionally create the friend and invite here
	if rand.Int()%3 == 0 {
		client2, err := utils.NewClient(host)
		if err != nil {
			return nil, err
		}

		if err := utils.Register(client2, flag, &flagId.FriendUsername, nil, &flagId.FriendPassword); err != nil {
			return nil, err
		}

		invite, err := utils.InviteFriend(client1, flagId.FriendUsername)
		if err != nil {
			return nil, err
		}

		flagId.FriendInvite = invite
	}

	if err := utils.WriteFlagId(flag, flagId); err != nil {
		return nil, err
	}

	return &FlagId{flagId.Username}, nil
}
