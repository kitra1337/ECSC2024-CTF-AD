package crypto

import (
	"fmt"
	"math/big"
)

type Curve struct {
	P       *big.Int
	N       *big.Int
	G       *Point
	Factors []int
	Invs    []int
}

func NewCurve(P, N, Gx, Gy *big.Int, Factors, Invs []int) *Curve {
	G := NewPoint(Gx, Gy)
	curve := &Curve{P: P, N: N, G: G, Factors: Factors, Invs: Invs}

	return curve
}

func (curve *Curve) polynomial(x *big.Int) *big.Int {
	x3 := new(big.Int).Mul(x, x)
	x3.Mul(x3, x)
	x3.Add(x3, x)
	x3.Mod(x3, curve.P)

	return x3
}

func (curve *Curve) IsOnCurve(P *Point) bool {
	if P.X.Sign() < 0 || P.X.Cmp(curve.P) >= 0 ||
		P.Y.Sign() < 0 || P.Y.Cmp(curve.P) >= 0 {
		return false
	}

	y2 := new(big.Int).Mul(P.Y, P.Y)
	y2.Mod(y2, curve.P)

	return curve.polynomial(P.X).Cmp(y2) == 0
}

func (curve *Curve) Add(P1, P2 *Point) *Point {
	P3 := Origin()
	lam := new(big.Int)
	if P1.IsOrigin {
		P3.X = P2.X
		P3.Y = P2.Y
		P3.IsOrigin = P2.IsOrigin
		return P3
	}
	if P2.IsOrigin {
		P3.X = P1.X
		P3.Y = P1.Y
		P3.IsOrigin = P1.IsOrigin
		return P3
	}
	if P1.X.Cmp(P2.X) == 0 && P1.Y.Cmp(new(big.Int).Mod(new(big.Int).Neg(P2.Y), curve.P)) == 0 {
		return P3
	}
	if P1.X.Cmp(P2.X) == 0 && P1.Y.Cmp(P2.Y) == 0 {
		x1x1 := new(big.Int).Mul(P1.X, P1.X)
		num := new(big.Int).Lsh(x1x1, 1)
		num.Add(num, x1x1)
		num.Add(num, big.NewInt(1))
		num.Mod(num, curve.P)
		den := new(big.Int).Lsh(P1.Y, 1)
		den.ModInverse(den, curve.P)
		lam.Mul(num, den)
		lam.Mod(lam, curve.P)
	} else {
		num := new(big.Int).Sub(P2.Y, P1.Y)
		den := new(big.Int).Sub(P2.X, P1.X)
		den.ModInverse(den, curve.P)
		lam.Mul(num, den)
		lam.Mod(lam, curve.P)
	}
	P3.X.Mul(lam, lam)
	P3.X.Sub(P3.X, P2.X)
	P3.X.Sub(P3.X, P1.X)
	P3.X.Mod(P3.X, curve.P)

	P3.Y.Sub(P1.X, P3.X)
	P3.Y.Mul(P3.Y, lam)
	P3.Y.Sub(P3.Y, P1.Y)
	P3.Y.Mod(P3.Y, curve.P)

	P3.IsOrigin = false

	return P3
}

func (curve *Curve) ScalarMult(P *Point, k *big.Int) *Point {
	kMod := new(big.Int).Mod(k, curve.N)
	res := Origin()
	tmp := &Point{X: P.X, Y: P.Y, IsOrigin: P.IsOrigin}
	for kMod.Sign() > 0 {
		if kMod.Bit(0) == 1 {
			res = curve.Add(res, tmp)
		}
		tmp = curve.Add(tmp, tmp)
		kMod.Rsh(kMod, 1)
	}
	return res
}

func (curve *Curve) LiftX(x *big.Int) (*Point, error) {
	y2 := curve.polynomial(x)
	y := new(big.Int).ModSqrt(y2, curve.P)
	if y != nil {
		return &Point{X: x, Y: y, IsOrigin: false}, nil
	} else {
		return nil, fmt.Errorf("cannot find point with x = %d", x)
	}
}

func (curve *Curve) Solve2kSDLog(G, P *Point, k int) int {
	res := 0
	for e := range k {
		G1 := curve.ScalarMult(G, big.NewInt(1<<(k-e-1)))
		P1 := curve.ScalarMult(P, big.NewInt(1<<(k-e-1)))
		P2 := curve.Add(P1, curve.ScalarMult(G1, big.NewInt(int64(-res))))
		if !P2.Cmp(G1) {
			res += 1 << e
		}
	}
	return res + 1
}

func (curve *Curve) SolveDLog(G, P *Point) *big.Int {
	res := big.NewInt(0)
	for i, fact := range curve.Factors {
		cofact := new(big.Int).Div(curve.N, big.NewInt(int64(fact)))
		G1 := curve.ScalarMult(G, cofact)
		P1 := curve.ScalarMult(P, cofact)
		if i == 0 {
			f := curve.Solve2kSDLog(G1, P1, 20)
			tmp := big.NewInt(int64(f))
			tmp.Mul(tmp, cofact)
			tmp.Mul(tmp, big.NewInt(int64(curve.Invs[i])))
			res.Add(res, tmp)
			res.Mod(res, curve.N)
		} else {
			for f := range fact {
				G2 := curve.ScalarMult(G1, big.NewInt(int64(f)))
				if G2.X.Cmp(P1.X) == 0 {
					if G2.Y.Cmp(P1.Y) != 0 {
						f = fact - f
					}
					tmp := big.NewInt(int64(f))
					tmp.Mul(tmp, cofact)
					tmp.Mul(tmp, big.NewInt(int64(curve.Invs[i])))
					res.Add(res, tmp)
					res.Mod(res, curve.N)
					break
				}
			}
		}
	}
	return res
}
