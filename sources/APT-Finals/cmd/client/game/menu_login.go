package game

import (
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"golang.design/x/clipboard"
	"image"
	"image/color"
)

func (m *Menu) drawLogin(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Type your username, press Enter, type your password, press Enter", 24, screen.Bounds().Sub(image.Pt(0, 100)), color.White)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 350, 700, 50), &m.username)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 430, 700, 50), &m.password)
}

func (m *Menu) updateLogin() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateSplash)
	case inpututil.IsKeyJustPressed(ebiten.KeyEnter):
		if m.username.IsTyping() && len(m.username.String()) > 0 {
			m.username.SetTyping(false)
			m.password.SetTyping(true)
		} else if m.password.IsTyping() && len(m.password.String()) > 0 {
			m.password.SetTyping(false)

			ok, err := m.g.client.Login(m.username.String(), m.password.String())
			if err != nil {
				m.messageIsError = true
				m.message = err.Error()
			} else if ok {
				m.loggedUsername = m.username.String()
				m.changeState(MenuStateLogged)
			} else {
				m.messageIsError = true
				m.message = "Invalid credentials"
			}
		}
	case inpututil.KeyPressDuration(ebiten.KeyControl) > 0 && inpututil.IsKeyJustPressed(ebiten.KeyV):
		if m.username.IsTyping() {
			m.username.Append(string(clipboard.Read(clipboard.FmtText)))
		} else if m.password.IsTyping() {
			m.password.Append(string(clipboard.Read(clipboard.FmtText)))
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyBackspace):
		if m.username.IsTyping() {
			m.username.Backspace()
		} else if m.password.IsTyping() {
			m.password.Backspace()
		}
	default:
		if m.username.IsTyping() {
			m.username.Append(GetTypedText())
		} else if m.password.IsTyping() {
			m.password.Append(GetTypedText())
		}
	}
}
