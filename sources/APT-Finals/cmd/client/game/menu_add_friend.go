package game

import (
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"golang.design/x/clipboard"
	"image"
	"image/color"
	"strings"
)

func (m *Menu) drawAddFriend(screen *ebiten.Image) {
	m.g.DrawTextCenter(screen, "Type the invite, press Enter", 24, screen.Bounds().Sub(image.Pt(0, 100)), color.White)
	m.g.DrawTextInput(screen, OffsetTopCenterX(screen.Bounds(), 350, 700, 50), &m.invite)
}

func (m *Menu) updateAddFriend() {
	switch {
	case inpututil.IsKeyJustPressed(ebiten.KeyEscape):
		m.changeState(MenuStateListFriends)
	case inpututil.IsKeyJustPressed(ebiten.KeyEnter):
		if m.invite.IsTyping() && len(m.invite.String()) > 0 {
			m.invite.SetTyping(false)

			invite := m.invite.String()
			colonIdx := strings.LastIndex(invite, ":")
			if colonIdx == -1 {
				m.messageIsError = true
				m.message = "Invalid invite"
			} else {
				if err := m.g.client.AddFriend(invite[:colonIdx], invite[colonIdx+1:]); err != nil {
					m.messageIsError = true
					m.message = err.Error()
				} else {
					m.messageIsError = false
					m.message = "Friend added"

					if friends, err := m.g.client.ListFriends(); err != nil {
						m.messageIsError = true
						m.message = err.Error()
					} else {
						m.friends = friends
					}
				}
			}
		}
	case inpututil.KeyPressDuration(ebiten.KeyControl) > 0 && inpututil.IsKeyJustPressed(ebiten.KeyV):
		if m.invite.IsTyping() {
			m.invite.Append(string(clipboard.Read(clipboard.FmtText)))
		}
	case inpututil.IsKeyJustPressed(ebiten.KeyBackspace):
		if m.invite.IsTyping() {
			m.invite.Backspace()
		}
	default:
		if m.invite.IsTyping() {
			m.invite.Append(GetTypedText())
		}
	}
}
