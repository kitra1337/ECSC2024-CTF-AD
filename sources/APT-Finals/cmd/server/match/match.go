package match

import (
	"apt"
	"apt/cmd/server/rng"
	"apt/pkg/models"
	"apt/pkg/proto"
	"fmt"
	"log/slog"
)

type BallShot struct {
	// Ball position when it was hit
	BallX float64
	BallY float64
	// Client position when it hit the ball
	ClientX float64
	ClientY float64
	// Bot position when it hit the ball
	BotX float64
	BotY float64
	// Who hit the ball
	IsClient bool
	// Next position the ball will bounce
	NextBallX float64
	NextBallY float64
}

type Match struct {
	log   *slog.Logger
	match *models.MatchPrivate

	clientRng *rng.RNG
	botRng    *rng.RNG

	done  bool
	shots []BallShot

	clientPoints int32
	botPoints    int32
}

func New(log *slog.Logger, matchDb *models.MatchPrivate) *Match {
	m := &Match{log: log, match: matchDb}

	difficulty := min(max(0, matchDb.Difficulty), 3)

	m.clientRng = rng.NewRNG(0, apt.DifficultiesClient[difficulty], matchDb.SecretKey, true)
	m.botRng = rng.NewRNG(0, apt.DifficultiesBot[difficulty], matchDb.SecretKey, false)
	return m
}

func (m *Match) ID() uint64 {
	return m.match.ID
}

func (m *Match) HandleCollision(req *proto.RequestDataCollision) (*proto.ResponseDataCollision, error) {
	if m.done {
		return nil, fmt.Errorf("match is over")
	}

	shot := BallShot{
		BallX:    req.BallX,
		BallY:    req.BallY,
		ClientX:  req.ClientX,
		ClientY:  req.ClientY,
		BotX:     req.BotX,
		BotY:     req.BotY,
		IsClient: req.IsClient,
	}

	if len(m.shots) > 0 {
		lastShot := m.shots[len(m.shots)-1]
		if lastShot.IsClient == req.IsClient {
			m.done = true
			return nil, fmt.Errorf("invalid turn")
		}

		if !isShotPossible(lastShot, shot) {
			m.done = true
			return nil, fmt.Errorf("impossible shot detected")
		}
	} else {
		if !isFirstShotPossible(shot) {
			m.done = true
			return nil, fmt.Errorf("impossible shot detected")
		}
	}

	if req.IsClient {
		shot.NextBallX, shot.NextBallY = m.clientRng.GetRandPos(req.Rnd1, req.Rnd2, len(m.shots) == 0)
	} else {
		shot.NextBallX, shot.NextBallY = m.botRng.GetRandPos(req.Rnd1, req.Rnd2, len(m.shots) == 0)
	}

	shot.NextBallX *= apt.CourtWidth
	shot.NextBallY *= apt.CourtHeight

	m.shots = append(m.shots, shot)

	m.log.With("x0", req.BallX).
		With("y0", req.BallY).
		With("x1", shot.NextBallX).
		With("y1", shot.NextBallY).
		With("rnd1", req.Rnd1).
		With("rnd2", req.Rnd2).
		With("client", req.IsClient).
		With("shots", len(m.shots)).
		Debug("handled collision")

	return &proto.ResponseDataCollision{
		X1: shot.NextBallX,
		Y1: shot.NextBallY,
	}, nil
}

func (m *Match) HandlePoint() (*proto.ResponseDataPoint, error) {
	if m.done {
		return nil, fmt.Errorf("match is over")
	}

	if len(m.shots) == 0 {
		m.done = true
		return nil, fmt.Errorf("invalid point")
	}

	lastShot := m.shots[len(m.shots)-1]
	if !isPointLegit(lastShot) {
		m.done = true
		return nil, fmt.Errorf("impossible point detected")
	}

	if lastShot.IsClient {
		m.clientPoints++
	} else {
		m.botPoints++
	}

	m.shots = m.shots[:0]

	var prize string
	if (m.clientPoints >= 4 || m.botPoints >= 4) && abs(m.clientPoints-m.botPoints) >= 2 {
		m.done = true

		if m.clientPoints > m.botPoints {
			prize = m.match.Prize
		}
	}

	return &proto.ResponseDataPoint{
		End:          m.done,
		Prize:        prize,
		ClientPoints: m.clientPoints,
		BotPoints:    m.botPoints,
	}, nil
}
