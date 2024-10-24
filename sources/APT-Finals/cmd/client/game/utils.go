package game

import (
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"github.com/hajimehoshi/ebiten/v2/text/v2"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"image"
	"image/color"
	"strconv"
	"strings"
)

func (g *Game) DrawTextLeft(screen *ebiten.Image, str string, size float64, pt image.Point, color color.Color) {
	font := &text.GoTextFace{Source: g.font, Size: size}

	op := &text.DrawOptions{}
	op.GeoM.Translate(float64(pt.X), float64(pt.Y))
	op.ColorScale.ScaleWithColor(color)
	text.Draw(screen, str, font, op)
}

func (g *Game) DrawTextCenter(screen *ebiten.Image, str string, size float64, rect image.Rectangle, color color.Color) {
	font := &text.GoTextFace{Source: g.font, Size: size}

	width, height := text.Measure(str, font, 0)

	op := &text.DrawOptions{}
	op.GeoM.Translate(float64(rect.Min.X+(rect.Dx()-int(width))/2), float64(rect.Min.Y+(rect.Dy()-int(height))/2))
	op.ColorScale.ScaleWithColor(color)
	text.Draw(screen, str, font, op)
}

func (g *Game) StrokeRect(screen *ebiten.Image, rect image.Rectangle, color color.Color) {
	vector.StrokeRect(screen, float32(rect.Min.X), float32(rect.Min.Y), float32(rect.Dx()), float32(rect.Dy()), 2, color, true)
}

func (g *Game) FillRect(screen *ebiten.Image, rect image.Rectangle, color color.Color) {
	vector.DrawFilledRect(screen, float32(rect.Min.X), float32(rect.Min.Y), float32(rect.Dx()), float32(rect.Dy()), color, true)
}

type TextInput struct {
	typing bool
	value  string
}

func (i *TextInput) String() string {
	return i.value
}

func (i *TextInput) Append(val string) {
	i.value += val
}

func (i *TextInput) Backspace() {
	if len(i.value) == 0 {
		return
	}

	i.value = i.value[:len(i.value)-1]
}

func (i *TextInput) IsTyping() bool {
	return i.typing
}

func (i *TextInput) SetTyping(val bool) {
	i.typing = val
}

func (i *TextInput) Clear() {
	i.typing = false
	i.value = ""
}

func (g *Game) DrawTextInput(screen *ebiten.Image, rect image.Rectangle, input *TextInput) {
	var border color.Color
	if input.typing {
		border = color.White
	} else {
		border = color.RGBA{R: 0x99, G: 0x99, B: 0x99, A: 0xff}
	}

	g.DrawTextCenter(screen, input.value, 24, rect, color.White)
	vector.StrokeRect(screen, float32(rect.Min.X), float32(rect.Min.Y), float32(rect.Dx()), float32(rect.Dy()), 2, border, true)
}

func GetTypedText() string {
	keys := inpututil.AppendJustPressedKeys(nil)

	var str string
	for _, key := range keys {
		val := key.String()
		if strings.HasPrefix(val, "Digit") {
			str += string(val[5])
		} else if len(val) == 1 {
			str += val
		}
	}

	return strings.ToLower(str)
}

type ChoiceInput struct {
	typing   bool
	values   []int
	selected int
}

func (i *ChoiceInput) IsTyping() bool {
	return i.typing
}

func (i *ChoiceInput) SetTyping(val bool) {
	i.typing = val
}

func (i *ChoiceInput) SetValues(val []int) {
	i.selected = -1
	i.values = val
}

func (i *ChoiceInput) Value() int {
	if i.selected == -1 {
		return -1
	}

	return i.values[i.selected]
}

func (i *ChoiceInput) String() string {
	if i.selected == -1 {
		return ""
	}

	return strconv.Itoa(i.values[i.selected])
}

func (i *ChoiceInput) Clear() {
	i.selected = -1
	i.typing = false
}

func (i *ChoiceInput) Next() {
	i.selected = min(i.selected+1, len(i.values)-1)
}

func (i *ChoiceInput) Prev() {
	i.selected = max(i.selected-1, 0)
}

func (g *Game) DrawChoiceInput(screen *ebiten.Image, rect image.Rectangle, input *ChoiceInput) {
	var border color.Color
	if input.typing {
		border = color.White
	} else {
		border = color.RGBA{R: 0x99, G: 0x99, B: 0x99, A: 0xff}
	}

	const (
		itemGap = 20
	)

	totalWidth := rect.Dy()*len(input.values) + itemGap*(len(input.values)-1)
	paddingX := (rect.Dx() - totalWidth) / 2

	for i, value := range input.values {
		var textColor color.Color
		if i == input.selected {
			textColor = color.Black
			vector.DrawFilledRect(screen, float32(rect.Min.X+paddingX)+float32((rect.Dy()+itemGap)*i), float32(rect.Min.Y), float32(rect.Dy()), float32(rect.Dy()), color.White, true)
		} else {
			textColor = color.White
			vector.StrokeRect(screen, float32(rect.Min.X+paddingX)+float32((rect.Dy()+itemGap)*i), float32(rect.Min.Y), float32(rect.Dy()), float32(rect.Dy()), 2, border, true)
		}

		g.DrawTextCenter(screen, strconv.Itoa(value), 24, image.Rect(
			rect.Min.X+paddingX+(rect.Dy()+itemGap)*i,
			rect.Min.Y,
			rect.Min.X+paddingX+(rect.Dy()+itemGap)*i+rect.Dy(),
			rect.Min.Y+rect.Dy(),
		), textColor)
	}
}

func CenterXY(rect image.Rectangle, width, height int) image.Rectangle {
	return OffsetTopLeft(rect, (rect.Dx()-width)/2, (rect.Dy()-height)/2, width, height)
}

func OffsetTopCenterX(rect image.Rectangle, top, width, height int) image.Rectangle {
	return OffsetTopLeft(rect, (rect.Dx()-width)/2, top, width, height)
}

func OffsetTopLeft(rect image.Rectangle, left, top, width, height int) image.Rectangle {
	return image.Rect(rect.Min.X+left, rect.Min.Y+top, rect.Min.X+left+width, rect.Min.Y+top+height)
}
