package crypto

import (
	"fmt"
	"math/big"
)

type Point struct {
	X        *big.Int
	Y        *big.Int
	IsOrigin bool
}

func Origin() *Point {
	return &Point{X: big.NewInt(-1), Y: big.NewInt(-1), IsOrigin: true}
}

func NewPoint(X, Y *big.Int) *Point {
	return &Point{X: X, Y: Y, IsOrigin: false}
}

func (P *Point) Cmp(Q *Point) bool {
	return (P.IsOrigin && Q.IsOrigin) || ((!P.IsOrigin && !Q.IsOrigin) && (P.X.Cmp(Q.X) == 0 && P.Y.Cmp(Q.Y) == 0))
}

func (P *Point) ToStr() string {
	return fmt.Sprintf("x = %d, y = %d, IsOrigin = %t", P.X, P.Y, P.IsOrigin)
}
