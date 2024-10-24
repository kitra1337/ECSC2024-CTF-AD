package game

import (
	"apt"
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"golang.design/x/clipboard"
	"image"
	"image/color"
)

func (m *Menu) updateRegister() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateSplash)
	case inpututil.KeyPressDuration(ebiten.KeyControl) > 0 && inpututil.IsKeyJustPressed(ebiten.KeyV):
		if m.username.IsTyping() {
			m.username.Append(string(clipboard.Read(clipboard.FmtText)))
		} else if m.secret.IsTyping() {
			m.secret.Append(string(clipboard.Read(clipboard.FmtText)))
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyEnter):
		if m.username.IsTyping() && len(m.username.String()) > 0 {
			if len(m.username.String()) >= apt.UsernameMinLength {
				m.username.SetTyping(false)
				m.secret.SetTyping(true)
			} else {
				m.messageIsError = true
				m.message = "Username is too short"
			}
		} else if m.secret.IsTyping() && len(m.secret.String()) > 0 {
			m.secret.SetTyping(false)

			password, err := m.g.client.Register(m.username.String(), m.secret.String())
			if err != nil {
				m.messageIsError = true
				m.message = err.Error()
			} else {
				m.messageIsError = false
				m.message = fmt.Sprintf("Your password is %s, press Esc and login", password)

				clipboard.Write(clipboard.FmtText, []byte(password))
			}
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyBackspace):
		if m.username.IsTyping() {
			m.username.Backspace()
		} else if m.secret.IsTyping() {
			m.secret.Backspace()
		}
	default:
		if m.username.IsTyping() {
			m.username.Append(GetTypedText())
		} else if m.secret.IsTyping() {
			m.secret.Append(GetTypedText())
		}
	}
}

func (m *Menu) drawRegister(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Type your username, press Enter, type your secret tennis strategy, press Enter", 24, screen.Bounds().Sub(image.Pt(0, 100)), color.White)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 350, 700, 50), &m.username)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 430, 700, 50), &m.secret)
}
