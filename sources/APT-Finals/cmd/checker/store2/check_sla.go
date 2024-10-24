package store2

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

	var prize, secretKey string
	matchId, err := utils.CreateMatch(client1, "", "", rand.IntN(2), &prize, &secretKey)
	if err != nil {
		return err
	}

	var won1 uint32
	if rand.Int()%3 == 0 {
		if err := utils.PlayMatch(client1, matchId); err != nil {
			return err
		}

		var respPoint *proto.ResponseDataPoint
		if rand.Int()%2 == 0 {
			if respPoint, err = utils.WinMatch(client1, secretKey); err != nil {
				return err
			}
		} else {
			if respPoint, err = utils.PlayRandomMatch(client1); err != nil {
				return err
			}
		}

		if respPoint.ClientPoints > respPoint.BotPoints {
			won1++

			if prize != respPoint.Prize {
				return error.New("Invalid prize", nil)
			}
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

	var won2 uint32
	if rand.Int()%3 == 0 {
		if err := utils.PlayMatch(client2, matchId); err != nil {
			return err
		}

		var respPoint *proto.ResponseDataPoint
		if rand.Int()%2 == 0 {
			if respPoint, err = utils.WinMatch(client2, secretKey); err != nil {
				return err
			}
		} else {
			if respPoint, err = utils.PlayRandomMatch(client2); err != nil {
				return err
			}
		}

		if respPoint.ClientPoints > respPoint.BotPoints {
			won2++

			if prize != respPoint.Prize {
				return error.New("Invalid prize", nil)
			}
		}

		playedMatches2, err := utils.ListPlayedMatches(client2)
		if err != nil {
			return err
		} else if len(playedMatches2) != 1 {
			return error.New("Invalid played matches", nil)
		} else if playedMatches2[0].ID != matchId {
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

	// Occasionally create another friend
	if rand.Int()%2 == 0 {
		client3, err := utils.NewClient(host)
		if err != nil {
			return err
		}

		var friends3 int
		var secret3, username3 string
		if err := utils.RegisterAndLogin(client3, "", &username3, &secret3, nil); err != nil {
			return err
		}

		switch rand.Int() % 4 {
		case 0:
			if invite, err := utils.InviteFriend(client1, username3); err != nil {
				return err
			} else if err := utils.AddFriend(client3, username1, invite); err != nil {
				return err
			}

			friends1++
			friends3++
		case 1:
			if invite, err := utils.InviteFriend(client2, username3); err != nil {
				return err
			} else if err := utils.AddFriend(client3, username2, invite); err != nil {
				return err
			}

			friends2++
			friends3++
		case 2:
			if invite, err := utils.InviteFriend(client3, username1); err != nil {
				return err
			} else if err := utils.AddFriend(client1, username3, invite); err != nil {
				return err
			}

			friends1++
			friends3++
		case 3:
			if invite, err := utils.InviteFriend(client3, username2); err != nil {
				return err
			} else if err := utils.AddFriend(client2, username3, invite); err != nil {
				return err
			}

			friends2++
			friends3++
		}

		if err := utils.RandOrder(
			func() *error.CheckerError {
				friends, err := utils.ListFriends(client1)
				if err != nil {
					return err
				} else if len(friends) != friends1 {
					return error.New("Invalid friends list", nil)
				} else {
					return nil
				}
			},
			func() *error.CheckerError {
				friends, err := utils.ListFriends(client2)
				if err != nil {
					return err
				} else if len(friends) != friends2 {
					return error.New("Invalid friends list", nil)
				} else {
					return nil
				}
			},
			func() *error.CheckerError {
				friends, err := utils.ListFriends(client3)
				if err != nil {
					return err
				} else if len(friends) != friends3 {
					return error.New("Invalid friends list", nil)
				} else {
					return nil
				}
			},
		); err != nil {
			return err
		}
	}

	return nil
}
