package game

import (
	"apt"
	"image"
	"image/color"
	"math/big"
	"math/rand/v2"
	"slices"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"github.com/jakecoffman/cp"
)

const (
	CollisionTypeBall cp.CollisionType = iota
	CollisionTypePlayer
)

type Match struct {
	g     *Game
	id    uint64
	end   bool
	prize string

	space *cp.Space

	court  *Court
	points *Points
	ball   *Ball
	player *Player
	bot    *Player

	lastCollision *cp.Body
}

func NewMatch(g *Game, id uint64) *Match {
	m := &Match{g: g, id: id}

	m.court = NewCourt(g, CenterXY(g.bounds, apt.CourtWidth, apt.CourtHeight))
	m.points = NewPoints(g)

	m.space = cp.NewSpace()
	m.space.Iterations = 20
	m.space.SetGravity(cp.Vector{})

	m.ball = NewBall(m, apt.BallStartX, apt.BallStartY)
	m.player = NewPlayer(m, apt.ClientStartX, apt.ClientStartY)
	m.bot = NewPlayer(m, apt.BotStartX, apt.BotStartY)

	ch := m.space.NewCollisionHandler(CollisionTypePlayer, CollisionTypeBall)
	ch.BeginFunc = func(arb *cp.Arbiter, _ *cp.Space, _ interface{}) bool {
		if !m.ball.CanCollide() {
			return false
		}

		player, _ := arb.Bodies()
		if m.lastCollision == player {
			return false
		}

		m.lastCollision = player
		isClient := player == m.player.body

		resp, err := g.client.HandleCollision(m.ball.body.Position(), m.player.body.Position(), m.bot.body.Position(), isClient, new(big.Int).SetUint64(rand.Uint64()), new(big.Int).SetUint64(rand.Uint64()))
		if err != nil {
			panic(err)
		}

		dst := cp.Vector{X: resp.X1, Y: resp.Y1}
		m.ball.LaunchTo(dst)

		if isClient {
			m.bot.MoveTo(dst)
		} else {
			m.bot.target = nil
			m.bot.body.SetVelocity(0, 0)
		}

		return false
	}

	return m
}

func (m *Match) ResetOnPoint(end bool, prize string) {
	m.lastCollision = nil

	m.ball.body.SetVelocity(0, 0)
	m.player.body.SetVelocity(0, 0)
	m.bot.body.SetVelocity(0, 0)

	m.ball.body.SetPosition(cp.Vector{X: apt.BallStartX, Y: apt.BallStartY})
	m.player.body.SetPosition(cp.Vector{X: apt.ClientStartX, Y: apt.ClientStartY})
	m.bot.body.SetPosition(cp.Vector{X: apt.BotStartX, Y: apt.BotStartY})

	m.end = end
	m.prize = prize
}

func (m *Match) Draw(screen *ebiten.Image) {
	m.court.Draw(screen)
	m.points.Draw(screen)
	m.bot.Draw(screen, m.court.rect)
	m.player.Draw(screen, m.court.rect)
	m.ball.Draw(screen, m.court.rect)

	if m.end {
		m.g.FillRect(screen, image.Rect(300, 350, 300+1000, 350+100), color.Black)

		var msg string
		if m.points.bot > m.points.player {
			msg = "BOT won the match! Press Esc"
		} else {
			msg = "YOU won the match! Press Esc"
		}

		m.g.DrawTextCenter(screen, msg, 64, screen.Bounds(), color.White)

		if len(m.prize) > 0 {
			m.g.FillRect(screen, image.Rect(100, 450, 100+1400, 450+100), color.Black)
			m.g.DrawTextCenter(screen, m.prize, 56, screen.Bounds().Add(image.Pt(0, 100)), color.White)
		}
	}
}

func (m *Match) Update() {
	if m.end {
		if inpututil.IsKeyJustPressed(ebiten.KeyEscape) {
			m.g.ExitMatch()
		}

		return
	}

	pressedKeys := inpututil.AppendPressedKeys(nil)

	var move cp.Vector
	if slices.Contains(pressedKeys, ebiten.KeyA) {
		move.X -= 1
	} else if slices.Contains(pressedKeys, ebiten.KeyD) {
		move.X += 1
	}

	if slices.Contains(pressedKeys, ebiten.KeyW) {
		move.Y -= 1
	} else if slices.Contains(pressedKeys, ebiten.KeyS) {
		move.Y += 1
	}

	m.player.Move(move)

	m.space.Step(1.0 / float64(ebiten.TPS()))
}
