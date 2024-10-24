package store1

type FlagIdPrivate struct {
	MatchID   uint64 `json:"match_id"`
	SecretKey string `json:"secret_key"`
}

type FlagId struct {
	MatchID uint64 `json:"match_id"`
}
