package db

import (
	"apt/pkg/models"
	"context"
	"crypto/subtle"
	"database/sql"
	"errors"
	"fmt"
	"os"

	_ "github.com/lib/pq"
)

type DB struct {
	db *sql.DB
}

func New() (db *DB, err error) {
	db = &DB{}
	db.db, err = sql.Open("postgres", os.Getenv("DB_DSN"))
	if err != nil {
		return nil, fmt.Errorf("failed connecting to database: %w", err)
	}

	return db, nil
}

func (db *DB) Login(ctx context.Context, username, password string) (bool, error) {
	row := db.db.QueryRowContext(ctx, "select password from users where username = $1", username)

	var actualPassword string
	if err := row.Scan(&actualPassword); errors.Is(err, sql.ErrNoRows) {
		return false, nil
	} else if err != nil {
		return false, err
	}

	return subtle.ConstantTimeCompare([]byte(password), []byte(actualPassword)) == 1, nil
}

func (db *DB) Register(ctx context.Context, username, password, secret string) error {
	_, err := db.db.ExecContext(ctx, "insert into users (username, password, secret) values ($1, $2, $3)", username, password, secret)
	return err
}

func (db *DB) ListMatches(ctx context.Context) ([]models.Match, error) {
	rows, err := db.db.QueryContext(ctx, "select id, owner, difficulty from matches")
	if err != nil {
		return nil, err
	}

	defer func() { _ = rows.Close() }()

	var matches []models.Match
	for rows.Next() {
		var match models.Match
		if err := rows.Scan(&match.ID, &match.Owner, &match.Difficulty); err != nil {
			return nil, err
		}

		matches = append(matches, match)
	}

	return matches, nil
}

func (db *DB) ListPlayedMatches(ctx context.Context, username string) ([]models.PlayedMatch, error) {
	rows, err := db.db.QueryContext(ctx, "select m.id, m.owner, m.difficulty, mp.winner from matches_played mp left join public.matches m on m.id = mp.match_id where username = $1", username)
	if err != nil {
		return nil, err
	}

	defer func() { _ = rows.Close() }()

	var matches []models.PlayedMatch
	for rows.Next() {
		var winner sql.NullString
		var match models.PlayedMatch
		if err := rows.Scan(&match.ID, &match.Owner, &match.Difficulty, &winner); err != nil {
			return nil, err
		}

		match.Winner = winner.String == "client"
		matches = append(matches, match)
	}

	return matches, nil
}

func (db *DB) GetMatch(ctx context.Context, id uint64) (*models.MatchPrivate, error) {
	row := db.db.QueryRowContext(ctx, "select id, owner, prize, secret_key, difficulty from matches where id = $1", id)

	var match models.MatchPrivate
	if err := row.Scan(&match.ID, &match.Owner, &match.Prize, &match.SecretKey, &match.Difficulty); errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	} else if err != nil {
		return nil, err
	}

	return &match, nil
}

func (db *DB) CreateMatch(ctx context.Context, username, prize, secretKey string, difficulty int) (uint64, error) {
	row := db.db.QueryRowContext(ctx, "insert into matches (owner, prize, secret_key, difficulty) values ($1, $2, $3, $4) returning id", username, prize, secretKey, difficulty)

	var id uint64
	if err := row.Scan(&id); err != nil {
		return 0, err
	}

	return id, nil
}

func (db *DB) SetMatchWinner(ctx context.Context, match uint64, client bool, username string) error {
	var winner string
	if client {
		winner = "client"
	} else {
		winner = "bot"
	}

	_, err := db.db.ExecContext(ctx, "update matches_played set winner = $1 where match_id = $2 and username = $3", winner, match, username)
	return err
}

func (db *DB) PlayMatch(ctx context.Context, match uint64, username string) error {
	_, err := db.db.ExecContext(ctx, "insert into matches_played (match_id, username) values ($1, $2)", match, username)
	return err
}

func (db *DB) ListFriends(ctx context.Context, username string) ([]models.Friend, error) {
	rows, err := db.db.QueryContext(ctx, `
		select u.username, 
			   u.secret, 
			   (select count(*) from matches_played mp where f.user_a = mp.username and mp.winner = 'client') as matches_won,
			   (select count(*) > 0 from friend_invites fi where (fi.user_a = f.user_a and fi.user_b = f.user_b) or (fi.user_a = f.user_b and fi.user_b = f.user_a)) as pending 
		from friends f 
			left join users u on u.username = f.user_a 
				where f.user_b = $1
    `, username)
	if err != nil {
		return nil, err
	}

	defer func() { _ = rows.Close() }()

	var friends []models.Friend
	for rows.Next() {
		var friend models.Friend
		if err := rows.Scan(&friend.Username, &friend.Secret, &friend.MatchesWon, &friend.Pending); err != nil {
			return nil, err
		}

		if friend.Pending {
			friend.Secret = ""
			friend.MatchesWon = 0
		}

		friends = append(friends, friend)
	}

	return friends, nil
}

func (db *DB) GetFriendInviteKey(ctx context.Context, username, friend string) ([]byte, error) {
	tx, err := db.db.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}

	defer func() { _ = tx.Rollback() }()

	row := tx.QueryRowContext(ctx, "select key from friend_invites where (user_a = $1 and user_b = $2) or (user_b = $1 and user_a = $2)", username, friend)

	var key []byte
	if err := row.Scan(&key); errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	} else if err != nil {
		return nil, err
	}

	if _, err := db.db.ExecContext(ctx, "delete from friend_invites where (user_a = $1 and user_b = $2) or (user_b = $1 and user_a = $2)", username, friend); err != nil {
		return nil, err
	}

	return key, tx.Commit()
}

func (db *DB) RemoveFriend(ctx context.Context, username, friend string) error {
	_, err := db.db.ExecContext(ctx, "delete from friends where (user_a = $1 and user_b = $2) or (user_b = $1 and user_a = $2)", username, friend)
	return err
}

func (db *DB) CreateFriendInvite(ctx context.Context, username, friend string, key []byte) error {
	tx, err := db.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}

	defer func() { _ = tx.Rollback() }()

	if _, err := tx.ExecContext(ctx, "insert into friend_invites (user_a, user_b, key) values ($1, $2, $3)", username, friend, key); err != nil {
		return err
	} else if _, err := tx.ExecContext(ctx, "insert into friends (user_a, user_b) values ($1, $2)", username, friend); err != nil {
		return err
	} else if _, err := tx.ExecContext(ctx, "insert into friends (user_a, user_b) values ($1, $2)", friend, username); err != nil {
		return err
	}

	return tx.Commit()
}
