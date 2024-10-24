package rng

import (
	"apt/pkg/crypto"
	"crypto/md5"
	"math"
	"math/big"
	"math/rand/v2"

	"github.com/chobie/go-gaussian"
)

type RNG struct {
	curve       *crypto.Curve
	Q           *crypto.Point
	dist        *gaussian.Gaussian
	maxDistance float64
	client      bool
}

func nextPrime(n *big.Int) *big.Int {
	for !n.ProbablyPrime(20) {
		n = n.Add(n, big.NewInt(1))
	}
	return n
}

func NewRNG(mean, variance float64, key string, client bool) *RNG {
	P, _ := new(big.Int).SetString("32993028718791676799062280315466580754431", 10)
	N, _ := new(big.Int).SetString("32993028718791676799062280315466580754432", 10)
	Gx, _ := new(big.Int).SetString("9303000621785476190709230799534131554011", 10)
	Gy, _ := new(big.Int).SetString("31009977496009883450976840324529127486069", 10)
	factors := []int{1048576, 761, 1213, 1471, 2447, 3067, 3947, 4373, 4663, 5189, 7393}
	invs := []int{387019, 524, 1063, 1225, 418, 1624, 3431, 2098, 4091, 3099, 5244}
	curve := crypto.NewCurve(P, N, Gx, Gy, factors, invs)

	h := md5.New()
	h.Write([]byte(key))
	digest := h.Sum(nil)
	s := nextPrime(new(big.Int).SetBytes(digest))
	Q := curve.ScalarMult(curve.G, s)

	dist := gaussian.NewGaussian(mean, variance)
	maxDistance := float64(25)

	rng := &RNG{curve: curve, Q: Q, dist: dist, maxDistance: maxDistance, client: client}

	return rng
}

func (rng *RNG) GetRand(r *big.Int) float64 {
	P := rng.curve.ScalarMult(rng.Q, r)
	Px := new(big.Float).SetInt(P.X)
	Py := new(big.Float).SetInt(P.Y)
	tmp := new(big.Float).Set(Px)
	Px.Add(Px, Py)
	Px.Mul(Px, big.NewFloat(2))
	tmp.Quo(tmp, Px)
	prob, _ := tmp.Float64()

	return rng.dist.Ppf(prob)
}

func (rng *RNG) GetRandPos(r1, r2 *big.Int, first bool) (float64, float64) {
	px := rng.GetRand(r1) / (-rng.maxDistance)
	px = min(px, 1)
	px = px * math.Pow(-1, float64(rand.IntN(2)))

	py := rng.GetRand(r2) / (-rng.maxDistance)
	py = min(py, 1)
	py = py * math.Pow(-1, float64(rand.IntN(2)))

	if first {
		return 0.65 + px*0.1, 0.3125 + py*0.1875
	}
	if rng.client {
		return 0.75 + px*0.25, 0.5 + py*0.375
	} else {
		return 0.25 + px*0.25, 0.5 + py*0.375
	}
}
