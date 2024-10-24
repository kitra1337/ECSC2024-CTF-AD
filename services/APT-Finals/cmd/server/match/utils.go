package match

import (
	"apt"
	"math"
)

func isShotPossible(last, curr BallShot) bool {
	if curr.IsClient && (math.Abs(curr.BallX-curr.ClientX) > apt.PlayerWidth+1e-7 || math.Abs(curr.BallY-curr.ClientY) > apt.PlayerHeight+1e-7) {
		return false
	}
	if !curr.IsClient && (math.Abs(curr.BallX-curr.BotX) > apt.PlayerWidth+1e-7 || math.Abs(curr.BallY-curr.BotY) > apt.PlayerHeight+1e-7) {
		return false
	}

	lastDeltaY := last.NextBallY - last.BallY
	lastDeltaX := last.NextBallX - last.BallX
	lastSlope := lastDeltaY / lastDeltaX

	currDeltaY := curr.BallY - last.BallY
	currDeltaX := curr.BallX - last.BallX
	curSlope := currDeltaY / currDeltaX

	if math.Signbit(currDeltaX) != math.Signbit(lastDeltaX) || math.Signbit(currDeltaY) != math.Signbit(lastDeltaY) || math.Abs(lastSlope-curSlope) > 1e-7 {
		return false
	}

	if currDeltaX/lastDeltaX > (1.1 + apt.BallBounceFactor*apt.BallBounceFactor) {
		return false
	}

	var timeBall float64

	if math.Abs(currDeltaX) < math.Abs(lastDeltaX) {
		timeBall = currDeltaX / lastDeltaX * apt.BallFirstBounceDuration
	} else {
		timeBall = apt.BallFirstBounceDuration + (currDeltaX/lastDeltaX-1)*apt.BallFirstBounceDuration/apt.BallBounceFactor
	}

	if curr.IsClient && (curr.BotX != last.BotX || curr.BotY != last.BotY) {
		return false
	}

	if math.Sqrt(math.Pow(curr.ClientY-last.ClientY, 2)+math.Pow(curr.ClientX-last.ClientX, 2))/apt.PlayerSpeed > (timeBall+1e-7) || math.Sqrt(math.Pow(curr.BotY-last.BotY, 2)+math.Pow(curr.BotX-last.BotX, 2))/apt.PlayerSpeed > (timeBall+1e-7) {
		return false
	}

	return true
}

func isFirstShotPossible(curr BallShot) bool {
	if !(curr.BallX == apt.BallStartX) || !(curr.BallY == apt.BallStartY) {
		return false
	}

	if !(curr.BotX == apt.BotStartX) || !(curr.BotY == apt.BotStartY) {
		return false
	}

	if math.Abs(curr.BallX-curr.ClientX) > apt.PlayerWidth+1e-7 || math.Abs(curr.BallY-curr.ClientY) > apt.PlayerHeight+1e-7 {
		return false
	}

	return true
}

func isPointLegit(last BallShot) bool {
	return !last.IsClient || math.Sqrt(math.Pow(last.NextBallY-last.BotY, 2)+math.Pow(last.NextBallX-last.BotX, 2))/apt.PlayerSpeed > (apt.BallFirstBounceDuration+1e-7)
}

func abs(a int32) int32 {
	if a < 0 {
		return -a
	}
	return a
}
