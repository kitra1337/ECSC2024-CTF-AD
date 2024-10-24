package game

import (
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"image"
	"image/color"
)

func (m *Menu) drawListMatches(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Select a match using Up and Down, press Enter", 24, image.Rect(50, 50, ScreenWidth-50, 100), color.White)

	const maxRows = 20

	row, col := 0, 0
	for idx, match := range m.matches {
		rect := image.Rect(50+col*300, 100+row*30, 50+(col+1)*300, 100+(row+1)*30)

		m.g.DrawTextCenter(screen, fmt.Sprintf("#%d %s %d", match.ID, match.Owner, match.Difficulty), 16, rect, color.White)

		if idx == m.selectedMatchIdx {
			m.g.StrokeRect(screen, rect, color.White)
		}

		row++
		if row > maxRows {
			row = 0
			col++
		}
	}
}

func (m *Menu) updateListMatches() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateLogged)
	case inpututil.IsKeyJustPressed(ebiten.KeyArrowDown):
		m.selectedMatchIdx = min(m.selectedMatchIdx+1, len(m.matches)-1)
	case inpututil.IsKeyJustPressed(ebiten.KeyArrowUp):
		m.selectedMatchIdx = max(m.selectedMatchIdx-1, 0)
	case inpututil.IsKeyJustPressed(ebiten.KeyEnter):
		if m.selectedMatchIdx != -1 {
			if err := m.g.PlayMatch(m.matches[m.selectedMatchIdx].ID); err != nil {
				m.messageIsError = true
				m.message = err.Error()
			}
		}
	}
}
