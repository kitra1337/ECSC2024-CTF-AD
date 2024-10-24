package game

import (
	"image"
	"image/color"

	"github.com/hajimehoshi/ebiten/v2"
)

func pointsToStr(a, b int32) (string, string) {
	valToStr := func(v int32) string {
		switch v {
		case 0:
			return "0"
		case 1:
			return "15"
		case 2:
			return "30"
		case 3:
			return "40"
		default:
			return "W"
		}
	}

	if a < 3 || b < 3 {
		return valToStr(a), valToStr(b)
	} else if a == b {
		return "40", "40"
	} else if a+1 < b {
		return "", "W"
	} else if b+1 < a {
		return "W", ""
	} else if a < b {
		return "", "AD"
	} else {
		return "AD", ""
	}
}

type Points struct {
	g *Game

	player int32
	bot    int32
}

func NewPoints(g *Game) *Points {
	return &Points{g: g}
}

func (p *Points) Draw(screen *ebiten.Image) {
	playerPoints, botPoints := pointsToStr(p.player, p.bot)

	p.g.FillRect(screen, OffsetTopLeft(screen.Bounds(), 20, 20, 100, 36), color.White)
	p.g.DrawTextLeft(screen, "YOU", 28, image.Pt(20+5, 20), color.Black)

	p.g.FillRect(screen, OffsetTopLeft(screen.Bounds(), 20, 20+36, 100, 36), color.White)
	p.g.DrawTextLeft(screen, "BOT", 28, image.Pt(20+5, 20+36), color.Black)

	p.g.FillRect(screen, OffsetTopLeft(screen.Bounds(), 20+100, 20, 50, 36), color.Black)
	p.g.DrawTextCenter(screen, playerPoints, 28, OffsetTopLeft(screen.Bounds(), 20+100, 20, 50, 36), color.White)

	p.g.FillRect(screen, OffsetTopLeft(screen.Bounds(), 20+100, 20+36, 50, 36), color.Black)
	p.g.DrawTextCenter(screen, botPoints, 28, OffsetTopLeft(screen.Bounds(), 20+100, 20+36, 50, 36), color.White)
}

func (p *Points) Set(player, bot int32) {
	p.player, p.bot = player, bot
}
