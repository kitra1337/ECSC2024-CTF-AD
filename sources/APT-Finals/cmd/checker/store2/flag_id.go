package store2

type FlagIdPrivate struct {
	Username string `json:"username"`
	Password string `json:"password"`

	FriendUsername string `json:"friend_username"`
	FriendPassword string `json:"friend_password"`
	FriendInvite   string `json:"friend_invite"`
}

type FlagId struct {
	Username string `json:"username"`
}
