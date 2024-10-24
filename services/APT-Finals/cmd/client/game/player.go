package game

import (
	"apt"
	"image"
	"image/color"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"github.com/jakecoffman/cp"
)

type Player struct {
	m *Match

	body  *cp.Body
	shape *cp.Shape

	target *cp.Vector
}

func NewPlayer(m *Match, x, y int) *Player {
	player := &Player{m: m}
	player.body = cp.NewKinematicBody()
	player.body.SetPosition(cp.Vector{X: float64(x), Y: float64(y)})
	player.body.SetPositionUpdateFunc(player.positionUpdate)
	player.shape = cp.NewBox(player.body, apt.PlayerWidth, apt.PlayerHeight, 0)
	player.shape.SetElasticity(0)
	player.shape.SetFriction(0)
	player.shape.SetCollisionType(CollisionTypePlayer)

	m.space.AddBody(player.body)
	m.space.AddShape(player.shape)

	return player
}

func (p *Player) Draw(screen *ebiten.Image, rect image.Rectangle) {
	pos := p.body.Position()
	vector.DrawFilledRect(screen, float32(float64(rect.Min.X)+pos.X-apt.PlayerWidth/2), float32(float64(rect.Min.Y)+pos.Y-apt.PlayerHeight/2), apt.PlayerWidth, apt.PlayerHeight, color.Black, true)
}

func (p *Player) Move(delta cp.Vector) {
	if delta.Length() > 0 {
		delta = delta.Normalize()
	}
	p.body.SetVelocityVector(delta.Mult(apt.PlayerSpeed))
}

func (p *Player) positionUpdate(body *cp.Body, dt float64) {
	cp.BodyUpdatePosition(body, dt)

	if p.target != nil {
		dist := p.target.Distance(body.Position())
		if dist < 10 {
			p.target = nil
			p.body.SetVelocity(0, 0)
		}
	}
}

func (p *Player) MoveTo(pos cp.Vector) {
	p.target = &pos

	delta := pos.Sub(p.body.Position())
	dist := pos.Distance(p.body.Position())
	p.body.SetVelocityVector(delta.Mult(apt.PlayerSpeed / dist))
}
