package game

import (
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"image"
	"image/color"
)

func (m *Menu) drawMatchesHistory(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Your match history", 24, image.Rect(50, 50, ScreenWidth-50, 100), color.White)

	const maxRows = 20

	row, col := 0, 0
	for _, match := range m.history {
		rect := image.Rect(50+col*300, 100+row*30, 50+(col+1)*300, 100+(row+1)*30)

		var textColor color.Color
		var outcome string
		if match.Winner {
			outcome = "WIN"
			textColor = color.RGBA{R: 0x00, G: 0xff, B: 0x00, A: 0xff}
		} else {
			outcome = "LOST"
			textColor = color.RGBA{R: 0xff, G: 0x00, B: 0x00, A: 0xff}
		}

		m.g.DrawTextCenter(screen, fmt.Sprintf("#%d %s %s", match.ID, match.Owner, outcome), 16, rect, textColor)

		row++
		if row > maxRows {
			row = 0
			col++
		}
	}
}

func (m *Menu) updateMatchesHistory() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateLogged)
	}
}
