package store1

import (
	"apt/cmd/checker/error"
	"apt/cmd/checker/utils"
)

func PutFlag(host, flag string) (any, *error.CheckerError) {
	client, err := utils.NewClient(host)
	if err != nil {
		return nil, err
	}

	if err := utils.RegisterAndLogin(client, "", nil, nil, nil); err != nil {
		return nil, err
	}

	var secretKey string
	matchId, err := utils.CreateMatch(client, flag, "", 3, nil, &secretKey)
	if err != nil {
		return nil, err
	}

	if err := utils.WriteFlagId(flag, &FlagIdPrivate{MatchID: matchId, SecretKey: secretKey}); err != nil {
		return nil, err
	}

	return &FlagId{matchId}, nil
}
