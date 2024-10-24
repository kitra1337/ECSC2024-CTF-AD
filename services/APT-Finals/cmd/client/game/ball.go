package game

import (
	"apt"
	"image"
	"image/color"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"github.com/jakecoffman/cp"
)

var BallColor = color.RGBA{R: 0xcc, G: 0xff, B: 0x0, A: 0xff}

type Ball struct {
	m *Match

	body  *cp.Body
	shape *cp.Shape

	flying   bool
	z        float64
	zVel     float64
	zInitVel float64
	bounces  int
}

func NewBall(m *Match, x, y int) *Ball {
	ball := &Ball{m: m}
	ball.body = cp.NewBody(1, cp.MomentForCircle(1, 0, apt.BallRadius, cp.Vector{}))
	ball.body.SetPosition(cp.Vector{X: float64(x), Y: float64(y)})
	ball.body.SetPositionUpdateFunc(ball.positionUpdate)
	ball.shape = cp.NewCircle(ball.body, apt.BallRadius, cp.Vector{})
	ball.shape.SetElasticity(0)
	ball.shape.SetFriction(0)
	ball.shape.SetCollisionType(CollisionTypeBall)

	m.space.AddBody(ball.body)
	m.space.AddShape(ball.shape)

	return ball
}

func (b *Ball) positionUpdate(body *cp.Body, dt float64) {
	cp.BodyUpdatePosition(body, dt)

	if b.flying {
		b.z += b.zVel * dt
		b.zVel -= apt.BallAcceleration * dt

		if b.z < 0 {
			b.z = 0
			b.zInitVel *= apt.BallBounceFactor

			b.bounces -= 1
			if b.bounces == 0 {
				b.flying = false
				b.body.SetVelocity(0, 0)
			} else {
				b.zVel = b.zInitVel
				b.body.SetVelocityVector(b.body.Velocity().Mult(apt.BallBounceFactor))
			}

			if apt.BallMaxBounces-b.bounces >= 2 {
				resp, err := b.m.g.client.HandlePoint()
				if err != nil {
					panic(err)
				}

				b.m.points.Set(resp.ClientPoints, resp.BotPoints)

				b.flying = false
				b.z = 0
				b.m.ResetOnPoint(resp.End, resp.Prize)
			}
		}
	}
}

func (b *Ball) LaunchTo(pos cp.Vector) {
	delta := pos.Sub(b.body.Position())
	dist := pos.Distance(b.body.Position())

	b.flying = true
	b.bounces = apt.BallMaxBounces
	b.z = 0
	b.zInitVel = (dist + apt.BallAcceleration*apt.BallFirstBounceDuration*apt.BallFirstBounceDuration/2) / apt.BallFirstBounceDuration
	b.zVel = b.zInitVel

	b.body.SetVelocityVector(delta.Mult(1 / apt.BallFirstBounceDuration))
}

func (b *Ball) CanCollide() bool {
	return !b.flying || b.z < apt.BallCollisionFactor*apt.BallAcceleration
}

func (b *Ball) Draw(screen *ebiten.Image, rect image.Rectangle) {
	pos := b.body.Position()
	vector.DrawFilledCircle(screen, float32(float64(rect.Min.X)+pos.X), float32(float64(rect.Min.Y)+pos.Y), float32(apt.BallRadius*(1+b.z/apt.BallAcceleration)), BallColor, true)
}
