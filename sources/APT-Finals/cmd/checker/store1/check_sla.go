package store1

import (
	"apt/cmd/checker/error"
	"apt/cmd/checker/utils"
	"apt/pkg/proto"
	"math/rand/v2"
)

func CheckSla(host string) *error.CheckerError {
	client1, err := utils.NewClient(host)
	if err != nil {
		return err
	}

	var friends1 int
	var secret1, username1 string
	if err := utils.RegisterAndLogin(client1, "", &username1, &secret1, nil); err != nil {
		return err
	}

	if rand.Int()%2 == 0 {
		friends, err := utils.ListFriends(client1)
		if err != nil {
			return err
		} else if len(friends) != 0 {
			return error.New("Invalid friends list", nil)
		}
	}

	var prize1, secretKey1 string
	matchId1, err := utils.CreateMatch(client1, "", "", rand.IntN(2), &prize1, &secretKey1)
	if err != nil {
		return err
	}

	var played1 int
	var won1 uint32
	if rand.Int()%2 == 0 {
		if err := utils.PlayMatch(client1, matchId1); err != nil {
			return err
		}

		var respPoint *proto.ResponseDataPoint
		if rand.Int()%2 == 0 {
			if respPoint, err = utils.WinMatch(client1, secretKey1); err != nil {
				return err
			}
		} else {
			if respPoint, err = utils.PlayRandomMatch(client1); err != nil {
				return err
			}
		}

		if respPoint.ClientPoints > respPoint.BotPoints {
			won1++

			if prize1 != respPoint.Prize {
				return error.New("Invalid prize", nil)
			}
		}

		played1++
	}

	playedMatches1, err := utils.ListPlayedMatches(client1)
	if err != nil {
		return err
	} else if len(playedMatches1) != played1 {
		return error.New("Invalid played matches", nil)
	} else if len(playedMatches1) > 0 {
		if playedMatches1[0].ID != matchId1 {
			return error.New("Invalid played matches", nil)
		} else if playedMatches1[0].Owner != username1 {
			return error.New("Invalid played matches", nil)
		}
	}

	client2, err := utils.NewClient(host)
	if err != nil {
		return err
	}

	var friends2 int
	var secret2, username2 string
	if err := utils.RegisterAndLogin(client2, "", &username2, &secret2, nil); err != nil {
		return err
	}

	invite, err := utils.InviteFriend(client2, username1)
	if err != nil {
		return err
	}

	if err := utils.RandOrder(
		func() *error.CheckerError {
			friends, err := utils.ListFriends(client1)
			if err != nil {
				return err
			} else if len(friends) != 1 {
				return error.New("Invalid friends list", nil)
			} else if !friends[0].Pending {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Username != username2 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].MatchesWon != 0 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Secret != "" {
				return error.New("Invalid friends list", nil)
			} else {
				return nil
			}
		},
		func() *error.CheckerError {
			friends, err := utils.ListFriends(client2)
			if err != nil {
				return err
			} else if len(friends) != 1 {
				return error.New("Invalid friends list", nil)
			} else if !friends[0].Pending {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Username != username1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].MatchesWon != 0 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Secret != "" {
				return error.New("Invalid friends list", nil)
			} else {
				return nil
			}
		},
	); err != nil {
		return err
	}

	if err := utils.AddFriend(client1, username2, invite); err != nil {
		return err
	}

	friends1++
	friends2++

	if err := utils.RandOrder(
		func() *error.CheckerError {
			friends, err := utils.ListFriends(client1)
			if err != nil {
				return err
			} else if len(friends) != 1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Pending {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Username != username2 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].MatchesWon != 0 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Secret != secret2 {
				return error.New("Invalid friends list", nil)
			} else {
				return nil
			}
		},
		func() *error.CheckerError {
			friends, err := utils.ListFriends(client2)
			if err != nil {
				return err
			} else if len(friends) != 1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Pending {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Username != username1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].MatchesWon != won1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Secret != secret1 {
				return error.New("Invalid friends list", nil)
			} else {
				return nil
			}
		},
	); err != nil {
		return err
	}

	var played2 int
	var won2 uint32
	if rand.Int()%2 == 0 {
		if err := utils.PlayMatch(client2, matchId1); err != nil {
			return err
		}

		var respPoint *proto.ResponseDataPoint
		if rand.Int()%2 == 0 {
			if respPoint, err = utils.WinMatch(client2, secretKey1); err != nil {
				return err
			}
		} else {
			if respPoint, err = utils.PlayRandomMatch(client2); err != nil {
				return err
			}
		}

		if respPoint.ClientPoints > respPoint.BotPoints {
			won2++

			if prize1 != respPoint.Prize {
				return error.New("Invalid prize", nil)
			}
		}

		played2++

		playedMatches2, err := utils.ListPlayedMatches(client2)
		if err != nil {
			return err
		} else if len(playedMatches2) != played2 {
			return error.New("Invalid played matches", nil)
		} else if playedMatches2[0].ID != matchId1 {
			return error.New("Invalid played matches", nil)
		} else if playedMatches2[0].Owner != username1 {
			return error.New("Invalid played matches", nil)
		}
	}

	if err := utils.RandOrder(
		func() *error.CheckerError {
			friends, err := utils.ListFriends(client1)
			if err != nil {
				return err
			} else if len(friends) != 1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Pending {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Username != username2 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].MatchesWon != won2 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Secret != secret2 {
				return error.New("Invalid friends list", nil)
			} else {
				return nil
			}
		},
		func() *error.CheckerError {
			friends, err := utils.ListFriends(client2)
			if err != nil {
				return err
			} else if len(friends) != 1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Pending {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Username != username1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].MatchesWon != won1 {
				return error.New("Invalid friends list", nil)
			} else if friends[0].Secret != secret1 {
				return error.New("Invalid friends list", nil)
			} else {
				return nil
			}
		},
	); err != nil {
		return err
	}

	var matchId2 uint64
	if rand.Int()%2 == 0 {
		var prize2, secretKey2 string
		matchId2, err = utils.CreateMatch(client2, "", "", rand.IntN(2), &prize2, &secretKey2)
		if err != nil {
			return err
		}

		if err := utils.PlayMatch(client2, matchId2); err != nil {
			return err
		}

		var respPoint *proto.ResponseDataPoint
		if rand.Int()%2 == 0 {
			if respPoint, err = utils.WinMatch(client2, secretKey2); err != nil {
				return err
			}
		} else {
			if respPoint, err = utils.PlayRandomMatch(client2); err != nil {
				return err
			}
		}

		if respPoint.ClientPoints > respPoint.BotPoints {
			won2++

			if prize2 != respPoint.Prize {
				return error.New("Invalid prize", nil)
			}
		}

		played2++
	}

	if rand.Int()%2 == 0 {
		playedMatches2, err := utils.ListPlayedMatches(client2)
		if err != nil {
			return err
		} else if len(playedMatches2) != played2 {
			return error.New("Invalid played matches", nil)
		}
	}

	return nil
}
