package models

type Match struct {
	ID         uint64
	Owner      string
	Difficulty int
}

type PlayedMatch struct {
	Match

	Winner bool
}

type MatchPrivate struct {
	Match

	Prize     string
	SecretKey string
}

type FriendInvite struct {
	UsernameA string
	UsernameB string
	Key       string
}

type Friend struct {
	Username   string
	Secret     string
	MatchesWon uint32
	Pending    bool
}
