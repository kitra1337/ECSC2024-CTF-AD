package store1

import (
	"apt/cmd/checker/error"
	"apt/cmd/checker/utils"
	"fmt"
	"os"
)

func GetFlag(host, flag string) *error.CheckerError {
	flagId, err := utils.ReadFlagId[FlagIdPrivate](flag)
	if err != nil {
		return err
	}

	_, _ = fmt.Fprintf(os.Stderr, "Secret key: %s\n", flagId.SecretKey)
	_, _ = fmt.Fprintf(os.Stderr, "Match ID: %d\n", flagId.MatchID)

	client, err := utils.NewClient(host)
	if err != nil {
		return err
	}

	if err := utils.RegisterAndLogin(client, "", nil, nil, nil); err != nil {
		return err
	}

	if err := utils.PlayMatch(client, flagId.MatchID); err != nil {
		return err
	}

	for range 20 {
		pointResp, err := utils.WinMatch(client, flagId.SecretKey)
		if err != nil {
			return err
		}
		if pointResp.ClientPoints > pointResp.BotPoints {
			if pointResp.Prize != flag {
				return error.New("Invalid prize", nil)
			} else {
				return nil
			}
		}
		if err := utils.PlayMatch(client, flagId.MatchID); err != nil {
			return err
		}
	}

	return error.New("Unable to win match", nil)
}
