package game

import (
	"fmt"
	"image"
	"image/color"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"golang.design/x/clipboard"
)

func (m *Menu) drawCreateMatch(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Type the match prize, press Enter, type the secret key, press Enter, select difficulty, press Enter", 24, screen.Bounds().Sub(image.Pt(0, 100)), color.White)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 350, 700, 50), &m.matchPrize)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 430, 700, 50), &m.matchSecret)
	m.g.DrawChoiceInput(screen, OffsetTopCenterX(screen.Bounds(), 510, 500, 50), &m.difficulty)
}

func (m *Menu) updateCreateMatch() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateLogged)
	case inpututil.KeyPressDuration(ebiten.KeyControl) > 0 && inpututil.IsKeyJustPressed(ebiten.KeyV):
		if m.matchPrize.IsTyping() {
			m.matchPrize.Append(string(clipboard.Read(clipboard.FmtText)))
		} else if m.matchSecret.IsTyping() {
			m.matchSecret.Append(string(clipboard.Read(clipboard.FmtText)))
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyEnter):
		if m.matchPrize.IsTyping() && len(m.matchPrize.String()) > 0 {
			m.matchPrize.SetTyping(false)
			m.matchSecret.SetTyping(true)
		} else if m.matchSecret.IsTyping() && len(m.matchSecret.String()) > 0 {
			m.matchSecret.SetTyping(false)
			m.difficulty.SetTyping(true)
		} else if m.difficulty.IsTyping() && len(m.difficulty.String()) > 0 {
			m.difficulty.SetTyping(false)

			matchId, err := m.g.client.CreateMatch(m.matchPrize.String(), m.matchSecret.String(), m.difficulty.Value())
			if err != nil {
				m.messageIsError = true
				m.message = err.Error()
			} else {
				m.messageIsError = false
				m.message = fmt.Sprintf("Match #%d created, press Esc", matchId)
			}
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyBackspace):
		if m.matchPrize.IsTyping() {
			m.matchPrize.Backspace()
		} else if m.matchSecret.IsTyping() {
			m.matchSecret.Backspace()
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyLeft) && m.difficulty.IsTyping():
		m.difficulty.Prev()
	case inpututil.IsKeyJustPressed(ebiten.KeyRight) && m.difficulty.IsTyping():
		m.difficulty.Next()
	default:
		if m.matchPrize.IsTyping() {
			m.matchPrize.Append(GetTypedText())
		} else if m.matchSecret.IsTyping() {
			m.matchSecret.Append(GetTypedText())
		}
	}
}
