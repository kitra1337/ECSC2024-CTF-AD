package game

import (
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"image"
	"image/color"
	"math/rand/v2"
)

var (
	CourtColors = []color.RGBA{
		{R: 0x33, G: 0x99, B: 0x66, A: 0xff},
		{R: 0x99, G: 0x33, B: 0x00, A: 0xff},
		{R: 0x33, G: 0x66, B: 0x99, A: 0xff},
	}
)

type Court struct {
	g *Game

	rect  image.Rectangle
	color color.Color
}

func NewCourt(g *Game, rect image.Rectangle) *Court {
	c := &Court{g: g, rect: rect}
	c.color = &CourtColors[rand.IntN(len(CourtColors))]
	return c
}

func (c *Court) Draw(screen *ebiten.Image) {
	screen.Fill(c.color)

	const strokeWidth = 5

	// Draw the outline of the court
	vector.StrokeRect(screen, float32(c.rect.Min.X), float32(c.rect.Min.Y), float32(c.rect.Dx()), float32(c.rect.Dy()), strokeWidth, color.White, true)

	// Draw the middle line (net)
	middleX := c.rect.Min.X + c.rect.Dx()/2
	vector.StrokeLine(screen, float32(middleX), float32(c.rect.Min.Y), float32(middleX), float32(c.rect.Max.Y), strokeWidth*2, color.White, true)

	// Draw the alleys
	alleysHeight := c.rect.Dy() / 8
	vector.StrokeLine(screen, float32(c.rect.Min.X), float32(c.rect.Min.Y+alleysHeight), float32(c.rect.Min.X+c.rect.Dx()), float32(c.rect.Min.Y+alleysHeight), strokeWidth, color.White, true)
	vector.StrokeLine(screen, float32(c.rect.Min.X), float32(c.rect.Min.Y+c.rect.Dy()-alleysHeight), float32(c.rect.Min.X+c.rect.Dx()), float32(c.rect.Min.Y+c.rect.Dy()-alleysHeight), strokeWidth, color.White, true)

	// Draw the left and right service boxes
	serviceBoxWidth, serviceBoxHeight := c.rect.Dx()/4, (c.rect.Dy()-alleysHeight*2)/2
	vector.StrokeRect(screen, float32(c.rect.Min.X+(c.rect.Dx()-serviceBoxWidth*2)/2), float32(c.rect.Min.Y+alleysHeight), float32(serviceBoxWidth*2), float32(serviceBoxHeight), strokeWidth, color.White, true)
	vector.StrokeRect(screen, float32(c.rect.Min.X+(c.rect.Dx()-serviceBoxWidth*2)/2), float32(c.rect.Min.Y+alleysHeight+serviceBoxHeight), float32(serviceBoxWidth*2), float32(serviceBoxHeight), strokeWidth, color.White, true)
}

func (c *Court) Update() {
}
